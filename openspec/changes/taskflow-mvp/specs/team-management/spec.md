## ADDED Requirements

### Requirement: 팀 생성 및 초대코드 자동 발급
시스템은 팀 생성 요청 시 팀 이름(1-30자)을 받아 팀을 생성하고, 서버가 `^[A-Z]{4}-[0-9]{4}$` 형식의 초대코드를 자동 생성해야 한다(SHALL). 생성자는 자동으로 team.owner_id가 되어야 하며(SHALL), 생성자의 users.team_id가 새 팀 id로 갱신되어야 한다(SHALL). 이미 다른 팀에 소속된 사용자(team_id NOT NULL)가 팀 생성을 요청하면 409를 반환해야 한다.

#### Scenario: 정상 팀 생성
- **WHEN** team_id가 NULL인 사용자가 유효한 팀 이름으로 POST /teams 요청
- **THEN** 시스템은 201과 함께 { id, name, invite_code, owner_id, created_at }을 응답하고 요청자의 users.team_id를 갱신한다

#### Scenario: 이미 팀 소속인 사용자의 생성 시도
- **WHEN** team_id가 이미 설정된 사용자가 POST /teams 요청
- **THEN** 시스템은 409 { error: { code: "ALREADY_IN_TEAM" } }를 응답한다

### Requirement: 초대코드로 팀 합류
시스템은 유효한 초대코드로 합류 요청 시 사용자의 users.team_id를 해당 팀으로 갱신해야 한다(SHALL). 형식이 올바르지 않으면 400, 존재하지 않는 코드면 404, 이미 다른 팀에 소속된 사용자면 409를 반환해야 한다.

#### Scenario: 정상 합류
- **WHEN** team_id가 NULL인 사용자가 유효한 초대코드로 POST /teams/join 요청
- **THEN** 시스템은 200과 함께 팀 정보를 응답하고 사용자의 users.team_id를 갱신한다

#### Scenario: 초대코드 형식 오류
- **WHEN** 사용자가 `^[A-Z]{4}-[0-9]{4}$` 정규식에 맞지 않는 코드로 합류 요청
- **THEN** 시스템은 400 { error: { code: "VALIDATION_ERROR" } }를 응답한다

#### Scenario: 존재하지 않는 초대코드
- **WHEN** 사용자가 형식은 맞지만 DB에 없는 초대코드로 합류 요청
- **THEN** 시스템은 404 { error: { code: "NOT_FOUND" } }를 응답한다

#### Scenario: 이미 다른 팀 소속
- **WHEN** team_id가 이미 설정된 사용자가 다른 팀 초대코드로 합류 요청
- **THEN** 시스템은 409 { error: { code: "ALREADY_IN_TEAM" } }를 응답한다

### Requirement: 팀 정보 조회 및 멤버 목록
시스템은 팀 멤버에게만 GET /teams/{id} 및 GET /teams/{id}/members 응답을 제공해야 한다(SHALL). 멤버 목록은 각 사용자의 email과 owner 여부(★)를 포함해야 한다.

#### Scenario: 멤버가 팀 정보 조회
- **WHEN** 팀 멤버가 GET /teams/{id} 요청
- **THEN** 시스템은 200과 함께 팀 정보를 응답한다

#### Scenario: 멤버가 멤버 목록 조회
- **WHEN** 팀 멤버가 GET /teams/{id}/members 요청
- **THEN** 시스템은 200과 함께 각 멤버의 email, owner 여부를 포함한 목록을 응답한다

### Requirement: 비멤버 접근 차단
시스템은 요청자의 users.team_id가 대상 팀 id와 일치하지 않는 모든 /teams/{id}/* 요청(조회 및 쓰기 포함)에 대해 403 FORBIDDEN을 반환해야 한다(SHALL).

#### Scenario: 비멤버의 팀 조회 시도
- **WHEN** 팀 A 소속 사용자가 팀 B의 GET /teams/{B_id} 또는 하위 리소스에 접근 시도
- **THEN** 시스템은 403 { error: { code: "FORBIDDEN" } }를 응답한다

#### Scenario: 미가입 사용자의 팀 리소스 접근 시도
- **WHEN** team_id가 NULL인 사용자가 임의의 /teams/{id}/* 엔드포인트에 접근 시도
- **THEN** 시스템은 403 { error: { code: "FORBIDDEN" } }를 응답한다
