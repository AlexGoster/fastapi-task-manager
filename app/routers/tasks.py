"""Task CRUD routes with filtering and pagination."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Task, User
from app.schemas import TaskCreate, TaskUpdate, TaskListResponse, TaskResponse
from app.auth import decode_access_token

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def get_current_user_id(token: str = Depends(lambda r: r), db: AsyncSession = Depends(get_db)) -> int:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(User.__table__.select().where(User.id == int(payload["sub"])))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db), user_id: Annotated[int, Depends(get_current_user_id)] = 0):
    if user_id == 0:
        raise HTTPException(status_code=401, detail="Unauthorized")
    db_task = Task(**task.model_dump(exclude_none=True), owner_id=user_id)
    db.add(db_task)
    await db.flush()
    await db.refresh(db_task)
    return db_task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status_filter: str | None = Query(default=None, pattern="^(pending|in_progress|done|archived)$"),
    priority_filter: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: Annotated[int, Depends(get_current_user_id)] = 0,
):
    if user_id == 0:
        raise HTTPException(status_code=401, detail="Unauthorized")
    stmt = select(Task).where(Task.owner_id == user_id)
    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    if priority_filter:
        stmt = stmt.where(Task.priority == priority_filter)
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()
    stmt = stmt.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return TaskListResponse(items=tasks, total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db), user_id: Annotated[int, Depends(get_current_user_id)] = 0):
    if user_id == 0:
        raise HTTPException(status_code=401, detail="Unauthorized")
    task = await db.get(Task, task_id)
    if not task or task.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, db: AsyncSession = Depends(get_db), user_id: Annotated[int, Depends(get_current_user_id)] = 0):
    if user_id == 0:
        raise HTTPException(status_code=401, detail="Unauthorized")
    task = await db.get(Task, task_id)
    if not task or task.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task_update.model_dump(exclude_none=True).items():
        setattr(task, key, value)
    await db.flush()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db), user_id: Annotated[int, Depends(get_current_user_id)] = 0):
    if user_id == 0:
        raise HTTPException(status_code=401, detail="Unauthorized")
    task = await db.get(Task, task_id)
    if not task or task.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
