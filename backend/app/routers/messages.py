import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_team_member
from app.errors import AppError
from app.models import Message, Team, User
from app.schemas import MessageCreateRequest, MessageOut

router = APIRouter(tags=["Chat"])

MESSAGE_MAX_LENGTH = 1000


@router.post("/teams/{team_id}/messages", response_model=MessageOut, status_code=201, summary="메시지 전송")
def send_message(
    team_id: int,
    payload: MessageCreateRequest,
    team: Team = Depends(require_team_member),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(payload.content) > MESSAGE_MAX_LENGTH:
        raise AppError.too_long(MESSAGE_MAX_LENGTH, len(payload.content))

    message = Message(team_id=team_id, user_id=current_user.id, content=payload.content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return MessageOut.model_validate(message)


@router.get("/teams/{team_id}/messages", response_model=list[MessageOut], summary="메시지 조회 (폴링, since=)")
def list_messages(
    team_id: int,
    since: datetime.datetime | None = Query(default=None),
    team: Team = Depends(require_team_member),
    db: Session = Depends(get_db),
):
    query = db.query(Message).filter(Message.team_id == team_id)
    if since is not None:
        query = query.filter(Message.created_at > since)
        messages = query.order_by(Message.created_at.asc()).all()
    else:
        messages = query.order_by(Message.created_at.desc()).limit(50).all()
        messages = list(reversed(messages))
    return [MessageOut.model_validate(m) for m in messages]


@router.delete("/messages/{message_id}", status_code=200, summary="메시지 삭제 (본인만)")
def delete_message(message_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if message is None:
        raise AppError.not_found("메시지를 찾을 수 없습니다")
    if current_user.team_id != message.team_id:
        raise AppError.forbidden("이 팀의 멤버가 아닙니다")
    if message.user_id != current_user.id:
        raise AppError.not_owner()

    db.delete(message)
    db.commit()
    return {}
