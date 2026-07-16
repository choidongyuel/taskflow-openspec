import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.errors import AppError
from app.routers import auth, messages, tasks, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TaskFlow MVP API",
    description=(
        "소규모 팀 칸반+채팅 협업 MVP 백엔드 API. "
        "인증이 필요한 엔드포인트는 우측 상단 Authorize 버튼에 "
        "`Bearer <JWT>` 형식 없이 토큰 값만 입력하면 됩니다."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=exc.to_body())


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    details = [
        {"loc": list(err.get("loc", [])), "msg": str(err.get("msg", ""))} for err in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "올바른 형식이 아닙니다",
                "meta": {"details": details},
            }
        },
    )


app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(messages.router)


@app.get("/", tags=["Health"], summary="헬스체크")
def health():
    return {"status": "ok"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    no_auth_paths = {("/auth/signup", "post"), ("/auth/login", "post")}
    for path_str, path in schema["paths"].items():
        for method_name, method in path.items():
            if method.get("tags", [None])[0] in ("Auth", "Team", "Task", "Chat") and (
                path_str,
                method_name,
            ) not in no_auth_paths:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
