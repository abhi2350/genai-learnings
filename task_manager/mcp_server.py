from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Task, Base
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

mcp = FastMCP("Task Manager")


def get_db():
    return SessionLocal()


@mcp.tool()
def create_task(title: str, done: bool = False) -> dict:
    """Create a new task."""
    db = get_db()
    try:
        task = Task(id=str(uuid.uuid4()), title=title, done=done, user_id="mcp-user")
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"id": task.id, "title": task.title, "done": task.done}
    finally:
        db.close()


@mcp.tool()
def get_tasks() -> list[dict]:
    """Get all tasks."""
    db = get_db()
    try:
        tasks = db.query(Task).all()
        return [{"id": t.id, "title": t.title, "done": t.done} for t in tasks]
    finally:
        db.close()


@mcp.tool()
def update_task(task_id: str, title: str = None, done: bool = None) -> dict:
    """Update an existing task by ID."""
    db = get_db()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        if title is not None:
            task.title = title
        if done is not None:
            task.done = done
        db.commit()
        db.refresh(task)
        return {"id": task.id, "title": task.title, "done": task.done}
    finally:
        db.close()


@mcp.tool()
def delete_task(task_id: str) -> dict:
    """Delete a task by ID."""
    db = get_db()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        db.delete(task)
        db.commit()
        return {"message": f"Task {task_id} deleted"}
    finally:
        db.close()


@mcp.tool()
def get_task_stats() -> dict:
    """Get task statistics — total, completed, and pending count."""
    db = get_db()
    try:
        total = db.query(Task).count()
        done = db.query(Task).filter(Task.done == True).count()
        return {"total": total, "completed": done, "pending": total - done}
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
