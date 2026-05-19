from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Task, User
from auth import get_current_user
import anthropic
import json
import uuid
import os

router = APIRouter(prefix="/agent", tags=["agent"])
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "create_task",
        "description": "Create a new task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "done": {"type": "boolean", "default": False}
            },
            "required": ["title"]
        }
    },
    {
        "name": "get_tasks",
        "description": "Get all tasks for the current user.",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "update_task",
        "description": "Update a task by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "title": {"type": "string"},
                "done": {"type": "boolean"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "delete_task",
        "description": "Delete a task by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "get_task_stats",
        "description": "Get total, completed, and pending task counts.",
        "input_schema": {"type": "object", "properties": {}}
    }
]


def execute_tool(name: str, tool_input: dict, user_id: str, db: Session) -> str:
    if name == "create_task":
        task = Task(
            id=str(uuid.uuid4()),
            title=tool_input["title"],
            done=tool_input.get("done", False),
            user_id=user_id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return json.dumps({"id": task.id, "title": task.title, "done": task.done})

    elif name == "get_tasks":
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        return json.dumps([{"id": t.id, "title": t.title, "done": t.done} for t in tasks])

    elif name == "update_task":
        task = db.query(Task).filter(Task.id == tool_input["task_id"], Task.user_id == user_id).first()
        if not task:
            return json.dumps({"error": "Task not found"})
        if "title" in tool_input:
            task.title = tool_input["title"]
        if "done" in tool_input:
            task.done = tool_input["done"]
        db.commit()
        db.refresh(task)
        return json.dumps({"id": task.id, "title": task.title, "done": task.done})

    elif name == "delete_task":
        task = db.query(Task).filter(Task.id == tool_input["task_id"], Task.user_id == user_id).first()
        if not task:
            return json.dumps({"error": "Task not found"})
        db.delete(task)
        db.commit()
        return json.dumps({"message": f"Task {tool_input['task_id']} deleted"})

    elif name == "get_task_stats":
        total = db.query(Task).filter(Task.user_id == user_id).count()
        done = db.query(Task).filter(Task.user_id == user_id, Task.done == True).count()
        return json.dumps({"total": total, "completed": done, "pending": total - done})

    return json.dumps({"error": f"Unknown tool: {name}"})


class AgentRequest(BaseModel):
    message: str


@router.post("/chat")
def agent_chat(
    payload: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = [{"role": "user", "content": payload.message}]

    # Agentic loop — keep going until Claude stops calling tools
    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system="You are a task management agent. Use tools to complete the user's request step by step.",
            tools=TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # Claude is done — extract the final text
            for block in response.content:
                if hasattr(block, "text"):
                    return {"reply": block.text}
            return {"reply": "Done."}

        if response.stop_reason == "tool_use":
            # Execute every tool Claude requested in this round
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input, current_user.id, db)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Append Claude's response (including tool_use blocks) to history
            messages.append({"role": "assistant", "content": response.content})
            # Append all tool results as a single user message
            messages.append({"role": "user", "content": tool_results})
