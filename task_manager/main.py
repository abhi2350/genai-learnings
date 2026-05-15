from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid
from routers import auth
from auth import get_current_user

from database import engine, get_db, Base
from models import Task, User
from schemas import TaskCreate, TaskResponse, TaskUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI()
all_tasks: List[Task] = []

app.include_router(auth.router)

@app.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = Task(id=str(uuid.uuid4()), title=payload.title, done=payload.done, user_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@app.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Task).filter(Task.user_id == current_user.id).all()

@app.get("/tasks/{id}", response_model=TaskResponse)
def get_task(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == id, Task.user_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/tasks/{id}", response_model=TaskResponse)
def update_task(id: str, payload: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == id, Task.user_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.title is not None:
        task.title = payload.title
    if payload.done is not None:
        task.done = payload.done
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{id}", response_model=TaskResponse)
def delete_task(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == id, Task.user_id == current_user.id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return task