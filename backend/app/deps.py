from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models import Task, Team, User
from app.security import JWTError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError.token_expired()
    try:
        user_id = decode_access_token(credentials.credentials)
    except JWTError:
        raise AppError.token_expired()
    user = db.get(User, user_id)
    if user is None:
        raise AppError.token_expired()
    return user


def require_team_member(team_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Team:
    if current_user.team_id != team_id:
        raise AppError.forbidden("이 팀의 멤버가 아닙니다")
    team = db.get(Team, team_id)
    if team is None:
        raise AppError.not_found("팀을 찾을 수 없습니다")
    return team


def get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise AppError.not_found("태스크를 찾을 수 없습니다")
    return task
