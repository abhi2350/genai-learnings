from typing import Optional
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    done: bool = False

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    done: bool
  
    class Config:
      # tells Pydantic to read data from SQLAlchemy objects (not just dicts).
      from_attributes = True