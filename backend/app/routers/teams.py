from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_team_member
from app.errors import AppError
from app.invite_code import generate_invite_code, is_valid_invite_code_format
from app.models import Team, User
from app.schemas import TeamCreateRequest, TeamJoinRequest, TeamMemberOut, TeamOut

router = APIRouter(prefix="/teams", tags=["Team"])


@router.post("", response_model=TeamOut, status_code=201, summary="팀 생성")
def create_team(payload: TeamCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.team_id is not None:
        raise AppError.already_in_team()

    for _ in range(5):
        code = generate_invite_code()
        if not db.query(Team).filter(Team.invite_code == code).first():
            break
    else:
        raise AppError(500, "INTERNAL_ERROR", "초대코드 생성에 실패했습니다")

    team = Team(name=payload.name, invite_code=code, owner_id=current_user.id)
    db.add(team)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError(500, "INTERNAL_ERROR", "팀 생성에 실패했습니다")

    current_user.team_id = team.id
    db.commit()
    db.refresh(team)
    return TeamOut.model_validate(team)


@router.post("/join", response_model=TeamOut, summary="초대코드로 팀 합류")
def join_team(payload: TeamJoinRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not is_valid_invite_code_format(payload.invite_code):
        raise AppError.validation_error("초대코드 형식이 올바르지 않습니다 (예: FRNT-2026)")

    if current_user.team_id is not None:
        raise AppError.already_in_team()

    team = db.query(Team).filter(Team.invite_code == payload.invite_code).first()
    if team is None:
        raise AppError.not_found("해당 초대코드를 찾을 수 없습니다")

    current_user.team_id = team.id
    db.commit()
    db.refresh(team)
    return TeamOut.model_validate(team)


@router.get("/{team_id}", response_model=TeamOut, summary="팀 정보 조회")
def get_team(team_id: int, team: Team = Depends(require_team_member)):
    return TeamOut.model_validate(team)


@router.get("/{team_id}/members", response_model=list[TeamMemberOut], summary="팀 멤버 목록 조회")
def list_members(team_id: int, team: Team = Depends(require_team_member), db: Session = Depends(get_db)):
    members = db.query(User).filter(User.team_id == team_id).order_by(User.created_at.asc()).all()
    return [
        TeamMemberOut(id=m.id, email=m.email, is_owner=(m.id == team.owner_id), created_at=m.created_at)
        for m in members
    ]
