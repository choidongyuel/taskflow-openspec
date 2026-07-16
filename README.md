# TaskFlow MVP

소규모 팀(3-5인)이 칸반 보드와 팀 채팅을 한 화면에서 함께 쓰는 협업 MVP입니다.

**배포 사이트**: https://taskflow-openspec-five.vercel.app

## 기능

- **인증**: 회원가입/로그인 (JWT, 24h 만료), bcrypt 비밀번호 해시
- **팀**: 팀 생성 + 초대코드(`AAAA-9999`) 자동 발급, 초대코드로 합류, 멤버 목록
- **칸반**: TODO/DOING/DONE 3컬럼, 드래그 & 드롭, 담당자 지정, 필터(전체/@me/미할당)
- **채팅**: 팀 단위 메시지, 5초 폴링, 1000자 제한, 본인 메시지 삭제
- **API 문서**: Swagger(`/docs`), ReDoc(`/redoc`) 자동 제공

## 기술 스택

| 영역 | 스택 |
|---|---|
| Backend | FastAPI, SQLAlchemy |
| DB | 로컬: SQLite / 배포: Neon(Postgres) |
| Frontend | Vanilla JS (ES6+), Tailwind CSS (CDN) |
| 배포 | Vercel (FE + BE 단일 프로젝트, Python 서버리스 함수) |
| 테스트 | pytest (백엔드 39개 테스트) |

## 프로젝트 구조

```
.
├── backend/           # FastAPI 앱
│   ├── app/
│   │   ├── main.py        # 앱 진입점, StaticFiles 마운트, CORS, 에러 핸들러
│   │   ├── models.py       # SQLAlchemy 모델 (users/teams/tasks/messages)
│   │   ├── routers/        # auth, teams, tasks, messages
│   │   ├── security.py     # JWT / bcrypt
│   │   └── errors.py       # 표준 에러 응답 { error: { code, message } }
│   └── tests/          # pytest 테스트 스위트
├── frontend/          # Vanilla JS + Tailwind 화면 4종
│   ├── index.html         # 로그인/회원가입
│   ├── team.html           # 팀 선택
│   ├── app.html            # 칸반 + 채팅 + 멤버 (탭 전환)
│   └── js/api.js           # fetch 래퍼, 401 인터셉터
├── api/index.py       # Vercel Python 함수 진입점 (backend/app을 감쌈)
├── vercel.json        # Vercel 함수 설정
└── openspec/          # OpenSpec 스펙 문서 (proposal/design/specs/tasks, archive)
```

## 로컬 개발

### 백엔드

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본적으로 로컬 SQLite(`taskflow.db`)를 사용하며, `http://127.0.0.1:8000/docs`에서 Swagger UI로 API를 바로 테스트할 수 있습니다. 같은 서버가 `frontend/`도 StaticFiles로 함께 서빙하므로 `http://127.0.0.1:8000/index.html`로 전체 앱에 접근 가능합니다.

### 테스트

```bash
cd backend
pytest -v
```

인메모리 SQLite로 격리되어 실행되며 로컬 개발 DB(`taskflow.db`)에는 영향을 주지 않습니다.

## 배포

Vercel 프로젝트 하나에 프론트(정적 파일)와 백엔드(Python 서버리스 함수)가 함께 배포됩니다. `DATABASE_URL`은 Vercel Marketplace의 Neon 통합을 통해 자동 주입됩니다.

```bash
vercel --prod
```

## 문서

전체 요구사항, 설계 결정, 구현 태스크는 [`openspec/changes/archive/2026-07-16-taskflow-mvp/`](openspec/changes/archive/2026-07-16-taskflow-mvp/)에서, 확정된 스펙은 [`openspec/specs/`](openspec/specs/)에서 확인할 수 있습니다.
