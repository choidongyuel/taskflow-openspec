## ADDED Requirements

### Requirement: Swagger/ReDoc API 문서 노출
시스템은 FastAPI 기본 제공 대화형 API 문서를 `/docs`(Swagger UI)와 `/redoc`(ReDoc)에서 노출해야 한다(SHALL). 문서에는 JWT Bearer 인증 스킴이 등록되어 있어야 하며, 개발자가 UI에서 토큰을 입력하고 인증이 필요한 엔드포인트를 직접 호출해 테스트할 수 있어야 한다(SHALL).

#### Scenario: Swagger UI 접근
- **WHEN** 개발자가 로컬 또는 배포 환경에서 GET /docs 요청
- **THEN** 시스템은 API 17개 엔드포인트가 모두 나열된 Swagger UI를 응답한다

#### Scenario: 인증이 필요한 엔드포인트 테스트
- **WHEN** 개발자가 /docs의 Authorize 버튼에 유효한 JWT를 입력한 뒤 인증이 필요한 엔드포인트를 Try it out으로 호출
- **THEN** 시스템은 Authorization 헤더가 자동 포함된 요청을 처리하고 정상 응답을 반환한다

### Requirement: pytest 자동 테스트 스위트
시스템은 백엔드 API 17개 전체에 대해 pytest 기반 자동 테스트를 갖춰야 한다(SHALL). 각 엔드포인트는 최소 1개의 정상 케이스와, 해당 엔드포인트가 발생시킬 수 있는 4xx 에러 케이스 중 최소 1개를 테스트로 커버해야 한다(SHALL). 테스트는 실제 개발/배포 DB와 분리된 인메모리 SQLite를 사용해야 한다(SHALL).

#### Scenario: 개발 완료 후 전체 테스트 실행
- **WHEN** 개발자가 로컬에서 `pytest` 명령을 실행
- **THEN** auth/team-management/kanban-tasks/team-chat 4개 캡페이빌리티의 테스트가 모두 수집되어 실행되고 결과(성공/실패)가 리포트된다

#### Scenario: 정상 케이스와 에러 케이스 동시 커버
- **WHEN** 특정 엔드포인트(예: POST /auth/signup)에 대한 테스트 모듈을 확인
- **THEN** 정상 가입 케이스와 최소 1개의 실패 케이스(예: 이메일 중복 409)가 함께 존재한다

#### Scenario: 테스트가 실제 DB에 영향 없음
- **WHEN** pytest 테스트 스위트가 실행되는 동안
- **THEN** 로컬 개발용 SQLite 파일(taskflow.db)의 데이터는 변경되지 않는다
