## 1. 프로젝트 초기 설정

- [x] 1.1 백엔드 디렉토리 구조 생성 (FastAPI 앱, 라우터, 모델, 서비스 레이어 분리)
- [x] 1.2 의존성 설치 (fastapi, uvicorn, sqlalchemy, python-jose, bcrypt, pytest, httpx)
- [ ] 1.3 프론트엔드 디렉토리 구조 생성 (HTML 페이지 4종 + JS + Tailwind 설정)
- [x] 1.4 `DATABASE_URL` 환경변수 기반 SQLAlchemy 엔진 설정 (로컬 기본값: sqlite:///./taskflow.db)
- [x] 1.5 FastAPI 앱 초기화 (title/description 설정, CORSMiddleware 등록 - 로컬/배포 도메인 허용)

## 2. DB 모델 및 공통 인프라

- [x] 2.1 SQLAlchemy 모델 4종 작성: users(id, email, password_hash, team_id FK nullable, created_at)
- [x] 2.2 teams 모델 작성 (id, name, invite_code UNIQUE, owner_id FK, created_at)
- [x] 2.3 tasks 모델 작성 (id, team_id FK, title, status, creator_id FK, assignee_id FK nullable, created_at)
- [x] 2.4 messages 모델 작성 (id, team_id FK, user_id FK, content, created_at)
- [x] 2.5 앱 시작 시 `Base.metadata.create_all()`로 테이블 자동 생성 로직 추가
- [x] 2.6 커스텀 예외 클래스 `AppError(code, message, status_code, meta=None)` 작성 및 헬퍼(forbidden/not_found/validation_error 등) 추가
- [x] 2.7 전역 exception handler 등록 (`{ error: { code, message, meta? } }` 표준 응답 변환)
- [x] 2.8 JWT 발급/검증 유틸리티 작성 (24h 만료, HS256 등 알고리즘 선택)
- [x] 2.9 bcrypt 해시/검증 유틸리티 작성

## 3. 인증 (auth capability)

- [x] 3.1 `get_current_user` FastAPI Dependency 작성 (JWT 검증, 만료 시 401 TOKEN_EXPIRED)
- [x] 3.2 POST /auth/signup 구현 (이메일/비밀번호 검증, bcrypt 해시, 중복 이메일 409)
- [x] 3.3 POST /auth/login 구현 (자격 증명 검증, 동일 메시지로 401 처리)
- [x] 3.4 GET /auth/me 구현
- [x] 3.5 POST /auth/logout 구현 (stateless, 200 반환)
- [x] 3.6 auth 관련 pytest 작성: signup 정상/이메일형식오류/비밀번호짧음/이메일중복, login 정상/자격증명오류, me 정상/토큰만료

## 4. 팀 관리 (team-management capability)

- [x] 4.1 초대코드 생성 유틸리티 작성 (`^[A-Z]{4}-[0-9]{4}$` 형식)
- [x] 4.2 `require_team_member(team_id)` Dependency 작성 (비멤버 403 FORBIDDEN)
- [x] 4.3 POST /teams 구현 (팀 생성, 초대코드 자동 발급, owner_id/team_id 갱신, 이미 소속 시 409)
- [x] 4.4 POST /teams/join 구현 (초대코드 검증: 형식 400/미존재 404/중복소속 409)
- [x] 4.5 GET /teams/{id} 구현 (멤버만 조회 가능)
- [x] 4.6 GET /teams/{id}/members 구현 (email, owner 여부 포함)
- [x] 4.7 team-management pytest 작성: 팀생성 정상/중복소속, 합류 정상/형식오류/미존재/중복소속, 정보조회 정상/비멤버403, 멤버목록 정상

## 5. 칸반 태스크 (kanban-tasks capability)

- [x] 5.1 POST /teams/{id}/tasks 구현 (제목 1-100자 검증, creator_id 자동 설정, assignee_id 선택)
- [x] 5.2 GET /teams/{id}/tasks 구현 (필터: 전체/@me(assignee_id 기준)/미할당, created_at desc 정렬)
- [x] 5.3 GET /tasks/{id} 구현 (단일 상세)
- [x] 5.4 PUT /tasks/{id} 구현 (제목/담당자만 수정, status 제외)
- [x] 5.5 PATCH /tasks/{id}/status 구현 (TODO/DOING/DONE 리터럴 검증, 그 외 값 400)
- [x] 5.6 DELETE /tasks/{id} 구현 (creator 본인 또는 team owner만 허용, 그 외 403)
- [x] 5.7 kanban-tasks pytest 작성: 생성 정상/비멤버403, 목록조회 전체/me필터/미할당필터, 단일조회, 제목수정, 상태변경 정상/잘못된값400, 삭제 creator/owner/권한없음403

## 6. 팀 채팅 (team-chat capability)

- [x] 6.1 POST /teams/{id}/messages 구현 (1-1000자 검증, 초과 시 400 TOO_LONG)
- [x] 6.2 GET /teams/{id}/messages 구현 (`since=` 파라미터, 없으면 최근 50개, 시간순 정렬)
- [x] 6.3 DELETE /messages/{id} 구현 (작성자 본인만 허용, owner도 예외 없이 403 NOT_OWNER)
- [x] 6.4 team-chat pytest 작성: 전송 정상/1000자초과/비멤버403, 조회 최초/since증분, 삭제 본인/타인403(owner 포함)

## 7. API 문서 및 테스트 인프라 (api-docs-and-testing capability)

- [x] 7.1 FastAPI 앱에 JWT Bearer 보안 스킴 등록 (Swagger UI Authorize 버튼에서 토큰 입력 가능하도록)
- [x] 7.2 /docs, /redoc 접근 확인 및 각 엔드포인트 summary/description 채우기
- [x] 7.3 pytest용 인메모리 SQLite fixture 구성 (`sqlite:///:memory:`, 세션별 격리, 실제 taskflow.db 미영향 확인)
- [x] 7.4 conftest.py 작성 (TestClient, DB 세션, 인증된 사용자/토큰 생성 헬퍼 fixture)
- [x] 7.5 전체 pytest 스위트 실행 및 17개 엔드포인트 전부 최소 1 정상 + 1 에러 케이스 커버 확인

## 8. 프론트엔드 - 인증 및 팀 선택 화면

- [ ] 8.1 로그인/회원가입 화면 구현 (Vanilla JS + Tailwind, validation 클라이언트측 이메일형식/8자이상)
- [ ] 8.2 JWT localStorage 저장/읽기/삭제 유틸리티 작성
- [ ] 8.3 401 응답 시 자동 로그인 페이지 redirect 인터셉터 작성
- [ ] 8.4 팀 선택 화면 구현 (팀 만들기, 초대코드 입력+합류, team_id NULL 강제 진입 로직)

## 9. 프론트엔드 - 칸반 화면

- [ ] 9.1 칸반 3컬럼 레이아웃 구현 (TODO/DOING/DONE, empty state 포함)
- [ ] 9.2 태스크 카드 생성 인라인 입력 구현 (담당자 선택 포함)
- [ ] 9.3 HTML5 native drag & drop 구현 (드롭 시 PATCH /tasks/{id}/status 호출)
- [ ] 9.4 카드 상세/수정 모달 구현 (제목/상태/담당자 수정, 삭제 버튼 - 권한 없으면 숨김)
- [ ] 9.5 필터(전체/@me/미할당) UI 및 API 연동 구현
- [ ] 9.6 768px 미만 모바일 반응형 구현 (컬럼 스와이프, 카드 길게 누르기 메뉴, FAB 버튼)

## 10. 프론트엔드 - 채팅 화면

- [ ] 10.1 채팅 화면 레이아웃 구현 (말풍선, 발신자+시각 표시, empty state)
- [ ] 10.2 5초 setInterval 폴링 구현 (`since=` 파라미터로 증분 조회)
- [ ] 10.3 메시지 입력 및 1000자 카운터/전송 버튼 disable 구현
- [ ] 10.4 본인 메시지 호버 삭제 메뉴 구현
- [ ] 10.5 모바일 반응형 채팅 화면 구현 (풀스크린, 키보드 대응)

## 11. 배포 준비

- [ ] 11.1 Vercel 프로젝트 연결 및 Vercel Storage에서 Neon(Postgres) 프로비저닝
- [ ] 11.2 FastAPI를 Vercel 서버리스 함수로 배포하는 설정 작성 (vercel.json 등)
- [ ] 11.3 프론트 정적 파일 Vercel 배포 설정
- [ ] 11.4 배포 후 CORS 허용 도메인을 실제 Vercel 도메인으로 갱신
- [ ] 11.5 배포 후 수동 스모크 테스트 (회원가입→로그인→팀생성→태스크생성→채팅 1턴, /docs 접근 확인)
