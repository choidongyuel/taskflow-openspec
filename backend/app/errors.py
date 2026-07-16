from typing import Any


class AppError(Exception):
    """Application error carrying an HTTP status code and a standard error body.

    Response shape: { error: { code, message, meta? } }
    """

    def __init__(self, status_code: int, code: str, message: str, meta: dict[str, Any] | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.meta = meta
        super().__init__(message)

    @classmethod
    def validation_error(cls, message: str = "올바른 형식이 아닙니다", meta: dict[str, Any] | None = None) -> "AppError":
        return cls(400, "VALIDATION_ERROR", message, meta)

    @classmethod
    def too_long(cls, limit: int, actual: int) -> "AppError":
        return cls(
            400,
            "TOO_LONG",
            f"{limit}자 이내로 입력하세요",
            {"limit": limit, "actual": actual},
        )

    @classmethod
    def invalid_credentials(cls) -> "AppError":
        return cls(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 일치하지 않습니다")

    @classmethod
    def token_expired(cls) -> "AppError":
        return cls(401, "TOKEN_EXPIRED", "인증이 만료되었습니다")

    @classmethod
    def forbidden(cls, message: str = "권한이 없습니다") -> "AppError":
        return cls(403, "FORBIDDEN", message)

    @classmethod
    def not_owner(cls, message: str = "본인의 메시지만 삭제할 수 있습니다") -> "AppError":
        return cls(403, "NOT_OWNER", message)

    @classmethod
    def not_found(cls, message: str = "해당 항목을 찾을 수 없습니다") -> "AppError":
        return cls(404, "NOT_FOUND", message)

    @classmethod
    def email_taken(cls) -> "AppError":
        return cls(409, "EMAIL_TAKEN", "이미 가입된 이메일입니다")

    @classmethod
    def already_in_team(cls) -> "AppError":
        return cls(409, "ALREADY_IN_TEAM", "이미 다른 팀에 소속되어 있습니다")

    def to_body(self) -> dict[str, Any]:
        error: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.meta is not None:
            error["meta"] = self.meta
        return {"error": error}
