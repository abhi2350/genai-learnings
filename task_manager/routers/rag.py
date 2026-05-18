from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import DocumentChunk, UploadedFile, User
from auth import get_current_user
import anthropic
import ollama
import uuid
import os
from pypdf import PdfReader
from io import BytesIO
from datetime import datetime

router = APIRouter(prefix="/rag", tags=["rag"])
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_embedding(text: str) -> list[float]:
    response = ollama.embeddings(model="nomic-embed-text", prompt=text)
    return response["embedding"]

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return " ".join(page.extract_text() or "" for page in reader.pages)

class IngestRequest(BaseModel):
    filename: str
    content: str

class ChatMessage(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []

@router.post("/ingest")
def ingest_document(
    payload: IngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chunks = chunk_text(payload.content)
    for chunk in chunks:
        embedding = get_embedding(chunk)
        doc = DocumentChunk(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=payload.filename,
            content=chunk,
            embedding=embedding
        )
        db.add(doc)
    db.commit()
    return {"message": f"Ingested {len(chunks)} chunks from {payload.filename}"}

@router.post("/query")
def query_documents(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query_embedding = get_embedding(payload.question)

    results = db.execute(text("""
        SELECT content, 1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM document_chunks
        WHERE user_id = :user_id
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT 3
    """), {"embedding": str(query_embedding), "user_id": current_user.id}).fetchall()

    if not results:
        raise HTTPException(status_code=404, detail="No documents found. Ingest some first.")

    context = "\n\n".join([row.content for row in results])

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Answer the user's question using ONLY the context provided. If the answer isn't in the context, say so.",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {payload.question}"
        }]
    )

    return {
        "answer": response.content[0].text,
        "sources": [{"content": row.content[:100] + "...", "similarity": round(row.similarity, 3)} for row in results]
    }

  # Upload PDF
@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()
    text = extract_pdf_text(contents)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    chunks = chunk_text(text)

    for chunk in chunks:
        embedding = get_embedding(chunk)
        db.add(DocumentChunk(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=file.filename,
            content=chunk,
            embedding=embedding
        ))

    db.add(UploadedFile(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        filename=file.filename,
        chunk_count=str(len(chunks)),
        created_at=datetime.now().isoformat()
    ))

    db.commit()
    return {"filename": file.filename, "chunks": len(chunks)}

# Chat with streamingThank you.
@router.post("/chat")
def chat(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query_embedding = get_embedding(payload.question)

    results = db.execute(text("""
        SELECT content, 1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM document_chunks
        WHERE user_id = :user_id
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT 5
    """), {"embedding": str(query_embedding), "user_id": current_user.id}).fetchall()

    if not results:
        raise HTTPException(status_code=404, detail="No documents found. Upload a PDF first.")

    context = "\n\n".join([row.content for row in results])

    messages = [{"role": m.role, "content": m.content} for m in payload.history]
    messages.append({"role": "user", "content": payload.question})

    def generate():
        with claude.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=f"Answer questions using ONLY the context below. If the answer isn't in the context, say so.\n\nCONTEXT:\n{context}",
            messages=messages
        ) as stream:
            for chunk in stream.text_stream:
                yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# List uploaded files
@router.get("/files")
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).all()
    return files