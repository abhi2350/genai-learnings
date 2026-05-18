from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Task, User
from auth import get_current_user
import anthropic
import os

router = APIRouter(prefix="/ai", tags=["ai"])
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ChatRequest(BaseModel):
    message: str

  # Tool definition — tells Claude what the tool does and what args it takes
TOOLS = [
    {
        "name": "get_task_stats",
        "description": "Get the current user's task statistics — total tasks, completed, and pending count.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def run_tool(tool_name: str, tool_input: dict, user_id: str, db: Session):
    if tool_name == "get_task_stats":
        total = db.query(Task).filter(Task.user_id == user_id).count()
        done = db.query(Task).filter(Task.user_id == user_id, Task.done == True).count()
        pending = total - done
        return {"total": total, "completed": done, "pending": pending}

@router.post("/chat")
def chat(payload: ChatRequest):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are a helpful task management assistant.",
        messages=[
            {"role": "user", "content": payload.message}
        ]
    )
    return {"reply": response.content[0].text}

@router.post("/chat/stream")
def chat_stream(payload: ChatRequest):
    def generate():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are a helpful task management assistant.",
            messages=[{"role": "user", "content": payload.message}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/chat/tools")
def chat_with_tools(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = [{"role": "user", "content": payload.message}]

    # First call — Claude may decide to use a tool
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="You are a task management assistant. Use tools to answer questions about the user's tasks.",
        tools=TOOLS,
        messages=messages
    )

    # If Claude wants to use a tool
    if response.stop_reason == "tool_use":
        tool_use_block = next(b for b in response.content if b.type == "tool_use")

        # Run the actual function
        tool_result = run_tool(tool_use_block.name, tool_use_block.input, current_user.id, db)

        # Send result back to Claude for final response
        messages += [
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": str(tool_result)
                }]
            }
        ]

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are a task management assistant. Use tools to answer questions about the user's tasks.",
            tools=TOOLS,
            messages=messages
        )

    return {"reply": response.content[0].text}