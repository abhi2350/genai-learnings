# defines the tasks table
from sqlalchemy import Column, String, Boolean, ForeignKey
from database import Base

class Task(Base):
  __tablename__ = "tasks"
  
  id = Column(String, primary_key=True)
  title = Column(String, nullable=False)
  done = Column(Boolean, default=False)
  user_id = Column(String, ForeignKey("users.id"), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)