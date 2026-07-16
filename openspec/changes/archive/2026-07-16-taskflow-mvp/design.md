## Context

TaskFlow는 3-5인 소규모 팀을 위한 칸반+채팅 협업 MVP다. 프로그램정의 문서(미션/페르소나/기능5종/DB4테이블/API18개/ACME/비기능요구사항)와 스토리보드 v2(42슬라이드, 화면 상태·에러 케이스·PDF원본 대비 통합본 결정 8건)를 입력으로 삼아 사전 설계가 이미 끝난 상태에서 시작한다. 이 design.md는 두 문서의 결정을 하나의 구현 가능한 아키텍처로 통합하고, 문서 간 불일치(API 개수/구성 차이 등)를 해소한 최종안을 기록한다.

프로젝트는 그린필드이며 기존 openspec/specs가 없다. Day 2 마무리까지 완성해야 하는 시간 제약이 있어 아키텍처는 최대한 단순하게 유지한다(단일 FastAPI 서버, 단일 DB, 프레임워크 없는 프론트).

## Goals / Non-Goals

**Goals:**
- 프로그램정의+스토리보드에서 확정된 DB 4테이블, API 17개, 권한 모델, 에러 표준을 정확히 구현 가능한 형태로 명세
- 로컬(SQLite) ↔ 배포(Neon Postgres) 환경 전환이 `DATABASE_URL` 하나로 가능하도록 설계
- FastAPI 자동 Swagger/ReDoc으로 API 수동 테스트 지원
- pytest로 전체 API에 대한 자동 테스트(정상 + 주요 에러 케이스) 작성 가능한 구조 확립
- 스토리보드 결정 8건(A·03) 중 Critical 4건(#1 users.team_id, #2 스크롤, #3 PATCH 분리, #4 assignee_id)을 스펙에 정확히 반영

**Non-Goals:**
- WebSocket 실시간, 알림, 파일 첨부, 전문 검색, 세분화 권한, 다국어 — 프로그램정의 Out-of-Scope 유지
- 팀 떠나기(leave) 기능 — 스토리보드 v2에서 제안됐으나 파생 복잡도(리소스 재할당) 때문에 이번 MVP에서 제외
- JWT 갱신/블랙리스트, 로그인 실패 cooldown, 채팅 재연결 exponential backoff — 모두 "Day 2 범위 외" 또는 과설계로 판단해 제외
- 프론트엔드 자동 테스트(jest 등) — 수동 확인만 유지, 자동화는 백엔드(pytest)로 한정

## Decisions

### 1. API 개수: 17개로 확정 (프로그램정의 18개, 스토리보드 18개 사이의 불일치 해소)
프로그램정의는 Auth4+Team4+Task6+Chat4=18, 스토리보드는 결정#8을 거쳐 Auth4+Team5+Task6+Chat3=18로 재구성했다. 두 안을 비교한 결과:
- `GET /messages/{id}` (프로그램정의) 대신 `GET /teams/{id}` (스토리보드, 팀 정보 단일 조회) 채택 — 더 실용적
- `DELETE /teams/{id}/leave` (스토리보드 신설)는 **제외** — MVP 범위를 넘는 파생 로직(소유권 이전, 태스크 재할당) 필요
- 결과: Auth(4) + Team(4: create/join/get/members) + Task(6) + Chat(3: get/post/delete) = **17개**

**대안 검토**: leave 기능을 포함한 18개 안도 고려했으나, "1인 1팀" 전제(Assumption)와 결합 시 "떠난 후 재합류" 흐름까지 설계해야 해 범위가 커짐. 제외하고 다음 change에서 다룰 수 있도록 Out-of-Scope에 명시.

### 2. DB 스키마 변경 2건 수용 (users.team_id, tasks.assignee_id)
스토리보드 결정 추적표(#1, #4)를 그대로 채택한다.
- `users.team_id` (FK→teams, NULL): "1인 1팀" 제약을 코드 레벨이 아닌 스키마 레벨로 강제. 로그인 후 분기(NULL→팀 선택, 아니면 칸반)의 근거가 됨
- `tasks.assignee_id` (FK→users, NULL): "내 태스크" 필터가 `creator_id`가 아닌 `assignee_id` 기준임을 명확히 함. creator≠assignee 케이스(팀원이 대신 만들어준 태스크)를 지원

**대안 검토**: `team_members` 조인 테이블로 다대다 관계를 만드는 안도 있었으나, "1인 1팀" Assumption과 DB 4테이블 제약(프로그램정의 고정) 때문에 기각. `users.team_id` 단일 컬럼이 훨씬 단순하고 제약과 일치.

### 3. 권한 검증은 FastAPI Dependency로 구현
`get_current_user` → `require_team_member(team_id)` → `require_task_owner_or_creator(task_id)` 순서의 의존성 체인으로 구성. 라우터 함수는 권한 로직을 직접 작성하지 않고 Depends로 주입받는다.
- 이유: 17개 엔드포인트 대부분이 "JWT 검증 + 팀 멤버십 검증"을 공통으로 필요로 함. 미들웨어보다 Dependency가 라우트별로 다른 세부 권한(예: creator만/owner만)을 조합하기 쉬움

### 4. 에러 처리는 커스텀 예외 + 전역 exception handler
`AppError(code, message, status_code, meta=None)` 커스텀 예외 클래스를 만들고, FastAPI의 `@app.exception_handler(AppError)`에서 표준 JSON(`{error: {code, message, meta?}}`)으로 변환한다. 각 라우트/서비스 함수는 `raise AppError.forbidden("본인의 메시지만 삭제할 수 있습니다")` 같은 헬퍼로 예외를 던진다.
- 이유: 에러 응답 표준 100% 준수(Metric)를 라우트마다 수동으로 하면 누락 위험이 크다. 중앙 핸들러 하나로 강제.

### 5. Swagger/ReDoc: FastAPI 기본 기능 그대로 사용
별도 라이브러리 설치 없이 FastAPI 앱 생성 시 `title`, `description`을 채우고, JWT Bearer 인증 스킴을 `OAuth2PasswordBearer` 또는 `HTTPBearer` 보안 스킴으로 등록해 `/docs`에서 "Authorize" 버튼으로 토큰 입력 후 바로 테스트 가능하게 한다. CORS는 `CORSMiddleware`에 허용 도메인(로컬: `http://localhost:*`, 배포: Vercel 도메인)을 명시한다.

### 6. pytest 테스트 구조: `TestClient` + SQLite 인메모리 DB
`fastapi.testclient.TestClient` + `httpx` 조합으로 테스트를 작성하고, 테스트 전용 SQLite 인메모리 DB(`sqlite:///:memory:`)로 fixture를 구성해 실제 파일 DB를 오염시키지 않는다. 각 캡페이빌리티(auth/team/kanban/chat)별로 테스트 파일을 분리한다(`test_auth.py`, `test_team.py`, `test_kanban.py`, `test_chat.py`).
- 커버리지 기준: 정상 케이스 1개 이상 + 해당 엔드포인트가 발생시킬 수 있는 4xx 에러 케이스 각 1개 이상(설계 목표, 100% 라인 커버리지는 목표하지 않음)

### 7. ORM: SQLAlchemy 2.0 스타일 + Alembic 없이 `Base.metadata.create_all()`
마이그레이션 도구(Alembic) 없이 앱 시작 시 테이블이 없으면 생성하는 방식을 택한다. MVP 규모(4테이블, 스키마 변경 거의 없음)에서 마이그레이션 도구는 과설계.
- 로컬: `sqlite:///./taskflow.db`, 배포: `DATABASE_URL` 환경변수(Neon Pooled URL)로 전환. SQLAlchemy가 두 방언을 모두 지원하므로 코드 변경 없이 동작.

## Risks / Trade-offs

- **[Risk]** JWT 갱신 없음(24h 고정) → 세션 중 강제 로그아웃 불가, 탈취 시 24h 유효 → **Mitigation**: 프로그램정의 Constraint로 이미 승인된 트레이드오프. MVP 범위에서 수용.
- **[Risk]** Alembic 없이 `create_all()`만 사용 → 향후 스키마 변경 시 마이그레이션 전략 없음 → **Mitigation**: 이번 change 범위에서는 스키마가 고정되어 있으므로 문제 없음. 후속 change에서 Alembic 도입 검토.
- **[Risk]** 5초 폴링(재시도 로직 없음) → 네트워크 일시 단절 시 사용자가 알아채지 못할 수 있음 → **Mitigation**: 프로그램정의 Assumption(동시 50명 이하, 안정적 네트워크 가정)에서 수용된 리스크. 폴링이 실패해도 다음 5초 주기에 자동 복구됨.
- **[Risk]** SQLite(로컬) ↔ Postgres(배포) 방언 차이로 로컬에서 통과한 테스트가 배포에서 실패할 가능성 → **Mitigation**: SQLAlchemy 표준 타입만 사용(TEXT, INTEGER, TIMESTAMP), DB 특화 기능(JSON 컬럼, 전문검색 등) 사용 안 함.
- **[Trade-off]** Dependency 체인 방식은 미들웨어보다 라우트마다 명시적으로 Depends를 선언해야 해 보일러플레이트가 늘어남 — 대신 라우트별 권한 차이(creator-only vs owner-or-creator)를 표현하기엔 더 명확함을 선택.

## Migration Plan

그린필드 프로젝트이므로 기존 시스템에서의 마이그레이션은 없음. 배포 절차:
1. 로컬에서 SQLite로 개발 및 pytest 통과 확인
2. Vercel 프로젝트 생성, Vercel Storage에서 Neon(Postgres) 프로비저닝 → `DATABASE_URL` 자동 주입
3. `git push` → Vercel이 FE 정적 파일 + BE(FastAPI를 서버리스 함수로) 자동 배포
4. 배포 후 `/docs`에서 수동 스모크 테스트(회원가입→로그인→팀생성→태스크생성→채팅 1턴)

## Open Questions

- 없음. 프로그램정의/스토리보드 검토 및 explore 세션에서 모든 Critical 결정 사항에 대한 합의를 마쳤음.
