# Task Manager API

A full-stack AI-powered Task Manager built with **FastAPI**, **PostgreSQL**, **Claude (Sonnet)**, and a **React/TypeScript** chat UI.

## Features

- JWT authentication (register, login)
- Create, read, update, and delete tasks (per-user)
- AI chat assistant powered by Claude Sonnet
- Streaming responses via Server-Sent Events
- Tool use — Claude can query live task stats
- RAG pipeline — ingest documents, upload PDFs, and query with vector search
- React + TypeScript chat UI with conversation history and file upload
- Docker + Docker Compose for one-command setup

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) + [PostgreSQL](https://www.postgresql.org/)
- [pgvector](https://github.com/pgvector/pgvector) — vector similarity search
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude Sonnet 4.6
- [Ollama](https://ollama.com/) (`nomic-embed-text`) — local embeddings
- [python-jose](https://github.com/mpdavis/python-jose) + [bcrypt](https://pypi.org/project/bcrypt/) — auth

**Frontend**
- [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/)

## Project Structure

```
├── task_manager/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # DB engine and session
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT auth helpers
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── routers/
│       ├── auth.py          # /auth/register, /auth/login
│       ├── ai.py            # /ai/chat, /ai/chat/stream, /ai/chat/tools, /ai/chat/general
│       └── rag.py           # /rag/ingest, /rag/upload, /rag/query, /rag/chat, /rag/files
└── chat-ui/                 # React + TypeScript frontend
    └── src/
        ├── App.tsx
        ├── api/client.ts
        └── components/
            ├── ChatWindow.tsx
            ├── ChatInput.tsx
            └── FileUpload.tsx
```

## Setup

### Option 1 — Docker (recommended)

```bash
cd task_manager
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### Option 2 — Local

#### 1. Clone the repo

```bash
git clone https://github.com/abhi2350/genai-learnings.git
cd genai-learnings
```

#### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r task_manager/requirements.txt
```

#### 4. Configure environment variables

Create a `.env` file inside `task_manager/`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/taskdb
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

#### 5. Run Ollama for embeddings

```bash
ollama pull nomic-embed-text
ollama serve
```

#### 6. Run the server

```bash
cd task_manager
uvicorn main:app --reload
```

### Frontend

```bash
cd chat-ui
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

## API Endpoints

### Auth
| Method | Endpoint           | Description        |
|--------|--------------------|--------------------|
| POST   | `/auth/register`   | Register a user    |
| POST   | `/auth/login`      | Login, get JWT     |

### Tasks (JWT required)
| Method | Endpoint        | Description         |
|--------|-----------------|---------------------|
| POST   | `/tasks`        | Create a task       |
| GET    | `/tasks`        | Get all tasks       |
| GET    | `/tasks/{id}`   | Get a task by ID    |
| PATCH  | `/tasks/{id}`   | Update a task       |
| DELETE | `/tasks/{id}`   | Delete a task       |

### AI Chat (JWT required)
| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| POST   | `/ai/chat`            | Single-turn chat                         |
| POST   | `/ai/chat/stream`     | Streaming chat (SSE)                     |
| POST   | `/ai/chat/tools`      | Chat with tool use (task stats)          |
| POST   | `/ai/chat/general`    | Streaming chat with conversation history |

### RAG (JWT required)
| Method | Endpoint        | Description                          |
|--------|-----------------|--------------------------------------|
| POST   | `/rag/ingest`   | Ingest text document                 |
| POST   | `/rag/upload`   | Upload and ingest a PDF              |
| POST   | `/rag/query`    | One-shot question over documents     |
| POST   | `/rag/chat`     | Streaming chat over documents (SSE)  |
| GET    | `/rag/files`    | List uploaded files                  |

## Interactive Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
