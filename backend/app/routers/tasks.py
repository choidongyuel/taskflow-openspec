from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_task_or_404, require_team_member
from app.errors import AppError
from app.models import Task, Team, User
from app.schemas import TaskCreateRequest, TaskOut, TaskStatusUpdateRequest, TaskUpdateRequest

router = APIRouter(tags=["Task"])


@router.post("/teams/{team_id}/tasks", response_model=TaskOut, status_code=201, summary="태스크 생성")
def create_task(
    team_id: int,
    payload: TaskCreateRequest,
    team: Team = Depends(require_team_member),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = Task(
        team_id=team_id,
        title=payload.title,
        status="TODO",
        creator_id=current_user.id,
        assignee_id=payload.assignee_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.get("/teams/{team_id}/tasks", response_model=list[TaskOut], summary="태스크 목록 조회 (필터 지원)")
def list_tasks(
    team_id: int,
    filter: str | None = Query(default=None, description="me | unassigned"),
    team: Team = Depends(require_team_member),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.team_id == team_id)
    if filter == "me":
        query = query.filter(Task.assignee_id == current_user.id)
    elif filter == "unassigned":
        query = query.filter(Task.assignee_id.is_(None))
    tasks = query.order_by(Task.created_at.desc()).all()
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=TaskOut, summary="태스크 단일 조회")
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = get_task_or_404(task_id, db)
    if current_user.team_id != task.team_id:
        raise AppError.forbidden("이 팀의 멤버가 아닙니다")
    return TaskOut.model_validate(task)


@router.put("/tasks/{task_id}", response_model=TaskOut, summary="태스크 제목/담당자 수정")
def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_task_or_404(task_id, db)
    if current_user.team_id != task.team_id:
        raise AppError.forbidden("이 팀의 멤버가 아닙니다")

    task.title = payload.title
    task.assignee_id = payload.assignee_id
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.patch("/tasks/{task_id}/status", response_model=TaskOut, summary="태스크 상태 변경 (드래그)")
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_task_or_404(task_id, db)
    if current_user.team_id != task.team_id:
        raise AppError.forbidden("이 팀의 멤버가 아닙니다")

    task.status = payload.status
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=200, summary="태스크 삭제 (creator 또는 owner만)")
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = get_task_or_404(task_id, db)
    if current_user.team_id != task.team_id:
        raise AppError.forbidden("이 팀의 멤버가 아닙니다")

    team = db.get(Team, task.team_id)
    is_owner = team is not None and team.owner_id == current_user.id
    is_creator = task.creator_id == current_user.id
    if not (is_owner or is_creator):
        raise AppError.forbidden("본인이 생성한 태스크 또는 팀 owner만 삭제할 수 있습니다")

    db.delete(task)
    db.commit()
    return {}
