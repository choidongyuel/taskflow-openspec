# auth Specification

## Purpose
TBD - synced from taskflow-mvp change.

## Requirements

### Requirement: 회원가입
시스템은 이메일과 비밀번호로 신규 계정을 생성해야 한다(SHALL). 비밀번호는 bcrypt로 해시하여 저장해야 하며(SHALL) 평문으로 저장해서는 안 된다(SHALL NOT). 이메일 형식이 유효하지 않거나 비밀번호가 8자 미만이면 400 VALIDATION_ERROR를 반환해야 한다. 이미 존재하는 이메일이면 409 EMAIL_TAKEN을 반환해야 한다. 성공 시 201과 함께 JWT를 발급해야 한다.

#### Scenario: 정상 회원가입
- **WHEN** 사용자가 유효한 이메일과 8자 이상 비밀번호로 POST /auth/signup 요청
- **THEN** 시스템은 users 테이블에 bcrypt 해시된 비밀번호로 레코드를 생성하고 201 + JWT를 응답한다

#### Scenario: 이메일 형식 오류
- **WHEN** 사용자가 형식에 맞지 않는 이메일(예: user@invalid)로 가입 요청
- **THEN** 시스템은 400 { error: { code: "VALIDATION_ERROR" } }를 응답한다

#### Scenario: 비밀번호 너무 짧음
- **WHEN** 사용자가 8자 미만 비밀번호로 가입 요청
- **THEN** 시스템은 400 { error: { code: "VALIDATION_ERROR" } }를 응답한다

#### Scenario: 이메일 중복
- **WHEN** 사용자가 이미 가입된 이메일로 가입 요청
- **THEN** 시스템은 409 { error: { code: "EMAIL_TAKEN" } }를 응답한다

### Requirement: 로그인
시스템은 이메일과 비밀번호를 검증하여 유효하면 JWT(만료 24시간)를 발급해야 한다(SHALL). 자격 증명이 틀린 경우 이메일 존재 여부를 노출해서는 안 되며(SHALL NOT), 이메일 부재/비밀번호 불일치 모두 동일한 401 INVALID_CREDENTIALS 메시지를 반환해야 한다.

#### Scenario: 정상 로그인
- **WHEN** 사용자가 올바른 이메일+비밀번호로 POST /auth/login 요청
- **THEN** 시스템은 200과 함께 { token, user: { id, email, team_id } }를 응답한다

#### Scenario: 자격 증명 불일치
- **WHEN** 사용자가 존재하지 않는 이메일 또는 틀린 비밀번호로 로그인 요청
- **THEN** 시스템은 401 { error: { code: "INVALID_CREDENTIALS" } }를 응답하며 두 경우 메시지가 동일하다

### Requirement: 현재 사용자 조회
시스템은 유효한 JWT로 요청 시 현재 로그인한 사용자 정보(id, email, team_id)를 반환해야 한다(SHALL).

#### Scenario: 유효한 토큰으로 조회
- **WHEN** 유효한 JWT를 Authorization 헤더에 담아 GET /auth/me 요청
- **THEN** 시스템은 200과 함께 현재 사용자 정보를 응답한다

#### Scenario: 토큰 만료 또는 누락
- **WHEN** 만료되었거나 존재하지 않는 토큰으로 GET /auth/me 요청
- **THEN** 시스템은 401 { error: { code: "TOKEN_EXPIRED" } }를 응답한다

### Requirement: 로그아웃 (stateless)
시스템은 로그아웃 요청 시 서버 측에 토큰 블랙리스트를 유지하지 않고(SHALL NOT) 200을 반환해야 한다(SHALL). 실제 토큰 폐기는 클라이언트가 저장소에서 토큰을 삭제하는 방식으로 처리한다.

#### Scenario: 로그아웃 요청
- **WHEN** 인증된 사용자가 POST /auth/logout 요청
- **THEN** 시스템은 200 {}을 응답하고 해당 토큰은 만료 시각(24h) 전까지 여전히 유효하다
</content>
</invoke>
