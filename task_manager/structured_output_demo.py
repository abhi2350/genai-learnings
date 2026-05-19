from typing import List
from pydantic import BaseModel
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class Task(BaseModel):
    title: str
    done: bool
    priority: str  # "high", "medium", "low"


class TaskExtraction(BaseModel):
    tasks: List[Task]


def extract_tasks(text: str) -> TaskExtraction:
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system="Extract tasks from the user's message. Infer priority from urgency words.",
        messages=[{"role": "user", "content": text}],
        output_format=TaskExtraction,
    )
    print(response.parsed_output)
    return response.parsed_output


if __name__ == "__main__":
    result = extract_tasks(
        "I urgently need to buy groceries, finish the report by Friday, and call mom sometime this week"
    )

    for task in result.tasks:
        status = "✓" if task.done else "○"
        print(f"[{status}] [{task.priority}] {task.title}")
