## Why

소규모 팀(3-5인)이 업무 진행 상황을 칸반 보드와 팀 채팅을 한 화면에서 함께 볼 수 있는 도구가 없다. 별도의 태스크 관리 툴과 채팅 툴을 오가며 컨텍스트를 잃는 문제를 해결하기 위해, 칸반 + 폴링 기반 팀 채팅을 결합한 MVP를 만든다. Day 2 마무리 시점까지 완성 가능한 범위로 기능을 고정하고, 사전에 화면·DB·API·비기능 요구사항을 모두 확정해 구현 중 임의 결정이 발생하지 않도록 한다.

## What Changes

- 이메일/비밀번호 기반 회원가입·로그인, JWT(24h 고정, 갱신 없음, stateless logout), bcrypt 비밀번호 해시 도입
- 팀 생성 시 초대코드(`AAAA-9999` 형식) 자동 발급, 초대코드로 팀 합류, 팀 멤버 목록 조회(owner/member 역할 구분만)
- 칸반 태스크: TODO/DOING/DONE 3컬럼, 태스크 생성/조회/제목수정/상태변경(드래그)/삭제, 담당자(assignee) nullable 지정 및 필터(전체/@me/미할당)
- 팀 단위 채팅: 메시지 송신/조회(5초 폴링, `since=` 파라미터 기반 증분 조회), 본인 메시지 삭제
- 모든 API 응답 에러를 `{ error: { code, message, meta? } }` 표준 형식으로 통일
- 권한 모델 확정: 팀 owner는 모든 태스크 삭제 가능, member는 본인 생성 태스크만 삭제 가능, 비멤버는 해당 팀의 모든 엔드포인트에서 403
- FastAPI 자동 제공 Swagger(`/docs`)·ReDoc(`/redoc`) 문서를 그대로 노출해 API 수동 테스트 지원
- 백엔드 API 전체에 대해 pytest 기반 자동 테스트 코드 작성(정상 케이스 + 401/403/404/409/400 주요 에러 케이스) — **원래 프로그램정의 문서의 "테스트 자동화 없음" 방침을 이번 change에서 철회**
- Vercel(FE+BE 서버리스) + Vercel Storage(Neon Postgres) 배포, 로컬 개발은 SQLite 사용

## Capabilities

### New Capabilities
- `auth`: 회원가입, 로그인, 세션(JWT) 조회, 로그아웃 — 인증 전반
- `team-management`: 팀 생성, 초대코드 발급/합류, 멤버 목록 조회, 팀 단위 접근 권한(비멤버 403) 관리
- `kanban-tasks`: 태스크 CRUD, 상태 이동(TODO/DOING/DONE), 담당자 지정 및 필터, 삭제 권한 규칙
- `team-chat`: 팀 단위 메시지 송수신(폴링 기반), 메시지 길이 제한, 본인 메시지 삭제
- `api-docs-and-testing`: Swagger/ReDoc 문서 노출, pytest 자동 테스트 스위트 구성

### Modified Capabilities
(없음 — 그린필드 프로젝트, 기존 spec 없음)

## Impact

- **신규 백엔드**: FastAPI 앱 전체, SQLAlchemy 모델 4종(users, teams, tasks, messages), JWT 인증 미들웨어, 권한 검증 미들웨어, 에러 핸들러, pytest 테스트 스위트
- **신규 프론트엔드**: Vanilla JS + Tailwind 기반 화면 4종(로그인/회원가입, 팀 선택, 칸반, 채팅) 및 모바일 반응형(768px 미만 브레이크포인트)
- **신규 DB**: 로컬 SQLite 파일, 배포 시 Vercel Storage Neon(Postgres)로 전환(`DATABASE_URL` 환경변수 기준)
- **신규 배포 파이프라인**: Vercel 프로젝트 연결(FE 정적파일 + BE 서버리스 함수)
- **의존성 추가(백엔드)**: fastapi, uvicorn, sqlalchemy, python-jose(JWT), passlib/bcrypt, pytest, httpx(테스트 클라이언트)
- **범위 외 유지**: 알림, 파일 첨부, 전문 검색, 세분화된 권한, 다국어, WebSocket 실시간, 팀 떠나기(leave) 기능
