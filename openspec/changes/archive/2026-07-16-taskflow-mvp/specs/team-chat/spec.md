## ADDED Requirements

### Requirement: 메시지 전송
시스템은 팀 멤버가 팀 단위 채팅 메시지를 전송할 수 있어야 한다(SHALL). 메시지 content는 1-1000자여야 하며, 클라이언트와 서버 양쪽에서 길이를 검증해야 한다(SHALL). 1000자를 초과하면 400 TOO_LONG을 반환해야 한다.

#### Scenario: 정상 메시지 전송
- **WHEN** 팀 멤버가 1000자 이내 content로 POST /teams/{id}/messages 요청
- **THEN** 시스템은 201과 함께 생성된 메시지(id, user_id, content, created_at)를 응답한다

#### Scenario: 1000자 초과
- **WHEN** 팀 멤버가 1000자를 초과하는 content로 메시지 전송 요청
- **THEN** 시스템은 400 { error: { code: "TOO_LONG", limit: 1000, actual: <실제길이> } }를 응답한다

#### Scenario: 비멤버의 전송 시도
- **WHEN** 비멤버가 POST /teams/{id}/messages 요청
- **THEN** 시스템은 403 { error: { code: "FORBIDDEN" } }를 응답한다

### Requirement: 메시지 조회 (폴링)
시스템은 GET /teams/{id}/messages 요청 시 `since=` 쿼리 파라미터를 지원해야 한다(SHALL). since가 없으면 최근 50개를 반환하고, since가 있으면 해당 시각 이후 생성된 메시지만 반환해야 한다. 클라이언트는 5초 주기로 이 엔드포인트를 폴링한다(재시도/백오프 로직은 서버 책임이 아님).

#### Scenario: 최초 진입 조회
- **WHEN** 팀 멤버가 since 파라미터 없이 GET /teams/{id}/messages 요청
- **THEN** 시스템은 최근 생성된 최대 50개의 메시지를 시간순으로 응답한다

#### Scenario: 증분 폴링 조회
- **WHEN** 팀 멤버가 since={마지막 수신 시각}으로 GET /teams/{id}/messages?since= 요청
- **THEN** 시스템은 해당 시각 이후 생성된 메시지만 응답하며, 새 메시지가 없으면 빈 배열을 응답한다

#### Scenario: 메시지 누락 없음 보장
- **WHEN** 어떤 메시지가 POST 요청으로 201을 받아 성공적으로 저장된 이후
- **THEN** 그 시각 이후의 모든 since= 조회에서 해당 메시지는 반드시 포함되어야 한다 (DELETE된 메시지 제외)

### Requirement: 메시지 삭제 (본인만)
시스템은 DELETE /messages/{id} 요청을 메시지 작성자 본인에게만 허용해야 한다(SHALL). 팀 owner라 하더라도 타인의 메시지는 삭제할 수 없다(SHALL NOT).

#### Scenario: 본인 메시지 삭제
- **WHEN** 메시지 작성자 본인이 DELETE /messages/{id} 요청
- **THEN** 시스템은 삭제를 완료한다

#### Scenario: 타인 메시지 삭제 시도 (owner 포함)
- **WHEN** 작성자가 아닌 사용자(팀 owner 포함)가 DELETE /messages/{id} 요청
- **THEN** 시스템은 403 { error: { code: "NOT_OWNER" } }를 응답한다
