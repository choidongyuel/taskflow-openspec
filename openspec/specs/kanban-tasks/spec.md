# kanban-tasks Specification

## Purpose
TBD - synced from taskflow-mvp change.

## Requirements

### Requirement: 태스크 생성
시스템은 팀 멤버가 팀 내 태스크를 생성할 수 있어야 한다(SHALL). 태스크는 제목(1-100자), 상태(기본 TODO), creator_id(요청자), assignee_id(nullable, 선택 지정)를 가져야 한다.

#### Scenario: 정상 태스크 생성
- **WHEN** 팀 멤버가 제목과 선택적 assignee로 POST /teams/{id}/tasks 요청
- **THEN** 시스템은 201과 함께 생성된 태스크를 응답하며 creator_id는 요청자로 설정된다

#### Scenario: 비멤버의 태스크 생성 시도
- **WHEN** 비멤버가 POST /teams/{id}/tasks 요청
- **THEN** 시스템은 403 { error: { code: "FORBIDDEN" } }를 응답한다

### Requirement: 태스크 목록 조회 및 필터
시스템은 팀 멤버에게 팀 내 태스크 목록을 status별 3컬럼(TODO/DOING/DONE)으로 조회 가능하게 해야 한다(SHALL). 필터는 전체(WHERE team_id=?), @me(AND assignee_id=current_user_id), 미할당(AND assignee_id IS NULL) 3종을 지원해야 하며, 정렬은 생성일 역순(created_at desc)을 기본으로 해야 한다.

#### Scenario: 전체 조회
- **WHEN** 팀 멤버가 필터 없이 GET /teams/{id}/tasks 요청
- **THEN** 시스템은 해당 팀의 모든 태스크를 created_at 역순으로 응답한다

#### Scenario: 내 태스크 필터
- **WHEN** 팀 멤버가 filter=me로 GET /teams/{id}/tasks 요청
- **THEN** 시스템은 assignee_id가 요청자 id와 일치하는 태스크만 응답한다 (creator_id 기준이 아님)

#### Scenario: 미할당 필터
- **WHEN** 팀 멤버가 filter=unassigned로 GET /teams/{id}/tasks 요청
- **THEN** 시스템은 assignee_id가 NULL인 태스크만 응답한다

### Requirement: 태스크 단일 조회 및 제목/담당자 수정
시스템은 GET /tasks/{id}로 단일 태스크 상세를, PUT /tasks/{id}로 제목과 담당자 수정을 지원해야 한다(SHALL). 상태(status) 변경은 이 엔드포인트에서 다루지 않는다(별도 PATCH 사용).

#### Scenario: 단일 태스크 조회
- **WHEN** 팀 멤버가 GET /tasks/{id} 요청
- **THEN** 시스템은 200과 함께 태스크 상세(제목, 상태, creator, assignee, 생성시각)를 응답한다

#### Scenario: 제목 수정
- **WHEN** 팀 멤버가 PUT /tasks/{id}에 새 제목을 담아 요청
- **THEN** 시스템은 200과 함께 갱신된 태스크를 응답한다

### Requirement: 태스크 상태 변경 (드래그)
시스템은 PATCH /tasks/{id}/status 엔드포인트로 태스크 상태(TODO/DOING/DONE) 변경을 전용 처리해야 한다(SHALL). status 값은 TODO, DOING, DONE 리터럴 중 하나여야 하며 그 외 값은 400을 반환해야 한다.

#### Scenario: 정상 상태 변경
- **WHEN** 팀 멤버가 PATCH /tasks/{id}/status에 { status: "DOING" }으로 요청
- **THEN** 시스템은 200과 함께 상태가 갱신된 태스크를 응답한다

#### Scenario: 유효하지 않은 상태값
- **WHEN** 팀 멤버가 { status: "ARCHIVED" } 같은 허용되지 않은 값으로 요청
- **THEN** 시스템은 400 { error: { code: "VALIDATION_ERROR" } }를 응답한다

### Requirement: 태스크 삭제 권한
시스템은 DELETE /tasks/{id} 요청을 태스크 creator 본인 또는 팀 owner에게만 허용해야 한다(SHALL). 그 외 멤버(creator도 owner도 아닌 member)의 삭제 요청은 403 NOT_OWNER 또는 FORBIDDEN으로 거부해야 한다.

#### Scenario: creator 본인의 삭제
- **WHEN** 태스크를 생성한 본인이 DELETE /tasks/{id} 요청
- **THEN** 시스템은 200 또는 204로 삭제를 완료한다

#### Scenario: 팀 owner의 타인 태스크 삭제
- **WHEN** 팀 owner가 다른 멤버가 생성한 태스크를 DELETE /tasks/{id} 요청
- **THEN** 시스템은 삭제를 완료한다 (owner는 오버라이드 권한을 가짐)

#### Scenario: 권한 없는 멤버의 삭제 시도
- **WHEN** creator도 owner도 아닌 멤버가 다른 사람의 태스크를 DELETE /tasks/{id} 요청
- **THEN** 시스템은 403 { error: { code: "FORBIDDEN" } }를 응답한다
</content>
</invoke>
