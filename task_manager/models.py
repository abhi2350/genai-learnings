# defines the tasks table
from sqlalchemy import Column, String, Boolean, ForeignKey
from database import Base
from pgvector.sqlalchemy import Vector

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

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    content = Column(String, nullable=False)
    embedding = Column(Vector(768))

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    chunk_count = Column(String, nullable=False)
    created_at = Column(String, nullable=False)