# Task Manager API

A full-stack AI-powered Task Manager built with **FastAPI**, **PostgreSQL**, **Claude (Sonnet)**, a **React/TypeScript** chat UI, and an **MCP server** for AI assistant integrations.

## Features

- JWT authentication (register, login)
- Create, read, update, and delete tasks (per-user)
- AI chat assistant powered by Claude Sonnet
- Streaming responses via Server-Sent Events
- Tool use — Claude can query live task stats
- RAG pipeline — ingest documents, upload PDFs, and query with vector search
- React + TypeScript chat UI with conversation history and file upload
- MCP server — expose tasks to any MCP-compatible AI client (Claude Desktop, etc.)
- Agentic loop — Claude autonomously creates, updates, and deletes tasks via tool use
- Structured output — extract typed task data from free-form text using `client.messages.parse`
- RAG evaluation — score RAG answers for faithfulness and relevance using Claude
- Docker + Docker Compose for one-command setup

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) + [PostgreSQL](https://www.postgresql.org/)
- [pgvector](https://github.com/pgvector/pgvector) — vector similarity search
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude Sonnet 4.6
- [Ollama](https://ollama.com/) (`nomic-embed-text`) — local embeddings
- [python-jose](https://github.com/mpdavis/python-jose) + [bcrypt](https://pypi.org/project/bcrypt/) — auth
- [MCP (FastMCP)](https://github.com/jlowin/fastmcp) — Model Context Protocol server

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
│   ├── mcp_server.py        # MCP server (FastMCP)
│   ├── structured_output_demo.py  # Extract tasks from text via messages.parse
│   ├── eval_rag.py          # RAG evaluation — faithfulness & relevance scoring
│   ├── alembic.ini          # Alembic config
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── migrations/
│   │   ├── env.py           # Alembic env (pgvector-aware)
│   │   └── versions/
│   │       ├── cec715623924_initial_tables.py
│   │       └── 92c71d6b9cae_add_priority_to_tasks.py
│   └── routers/
│       ├── auth.py          # /auth/register, /auth/login
│       ├── ai.py            # /ai/chat, /ai/chat/stream, /ai/chat/tools, /ai/chat/general
│       ├── rag.py           # /rag/ingest, /rag/upload, /rag/query, /rag/chat, /rag/files
│       └── agent.py         # /agent/chat — agentic loop with full task CRUD tools
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

## MCP Server

The MCP server exposes task operations as tools consumable by any MCP-compatible AI client (Claude Desktop, Cursor, etc.).

### Tools

| Tool | Description |
|------|-------------|
| `create_task` | Create a new task |
| `get_tasks` | List all tasks |
| `update_task` | Update title or done status by ID |
| `delete_task` | Delete a task by ID |
| `get_task_stats` | Get total, completed, and pending counts |

### Run the MCP server

```bash
cd task_manager
python mcp_server.py
```

### Connect to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "python",
      "args": ["/absolute/path/to/task_manager/mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/taskdb"
      }
    }
  }
}
```

## Database Migrations (Alembic)

Migrations live in `task_manager/migrations/versions/`. All commands must be run from inside `task_manager/`.

```bash
cd task_manager
```

### Apply all migrations

```bash
alembic upgrade head
```

### Roll back one migration

```bash
alembic downgrade -1
```

### Roll back to a specific revision

```bash
alembic downgrade cec715623924
```

### Roll back all migrations

```bash
alembic downgrade base
```

### Generate a new migration (autogenerate from models)

```bash
alembic revision --autogenerate -m "describe your change"
```

### View current revision

```bash
alembic current
```

### View migration history

```bash
alembic history --verbose
```

### Migration history

| Revision | Description |
|----------|-------------|
| `cec715623924` | Initial tables — users, tasks, document_chunks, uploaded_files |
| `92c71d6b9cae` | Add `priority` column to tasks |

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

### Agent (JWT required)
| Method | Endpoint       | Description                                              |
|--------|----------------|----------------------------------------------------------|
| POST   | `/agent/chat`  | Agentic loop — Claude autonomously manages tasks via tools |

## query_gpt Agent

A multi-step natural-language-to-SQL pipeline built with Claude structured output and a live PostgreSQL schema.

### How it works

1. **Table selection** — given a question, Claude picks the minimum set of tables needed
2. **Column pruning** — Claude narrows each table down to only the relevant columns
3. **SQL generation** — Claude writes a single PostgreSQL `SELECT` query from the pruned schema
4. **Execution** — the query is run against the real database and results are returned

### Run

```bash
cd agents/query_gpt
python agent_try.py
```

**Example:**

```python
run_pipeline("How many orders are in each status?")
# Returns: { sql, explanation, question, rows, tables_used }
```

### Structure

```
agents/query_gpt/
├── agent_try.py   # Pipeline: select_tables → prune_columns → generate_sql → execute
├── database.py    # get_schema() and execute_sql() via psycopg2
├── agents.py
├── main.py
└── requirements.txt
```

### Environment

```env
DATABASE_URL=postgresql://user:password@localhost:5432/yourdb
ANTHROPIC_API_KEY=your-anthropic-api-key
```

---

## Standalone Scripts

### Structured Output Demo

Extracts tasks (title, priority, done) from free-form text using `client.messages.parse` and Pydantic models.

```bash
cd task_manager
python structured_output_demo.py
```

**Example input:** `"I urgently need to buy groceries, finish the report by Friday, and call mom sometime this week"`

**Output:**
```
[○] [high] Buy groceries
[○] [high] Finish the report
[○] [low] Call mom
```

### RAG Evaluation

Scores RAG answers for faithfulness and relevance using Claude as a judge. Outputs per-answer scores and an overall summary.

```bash
cd task_manager
python eval_rag.py
```

**Metrics:**
- `score` — 1 (terrible) to 5 (perfect)
- `faithful` — is the answer grounded in the retrieved context?
- `relevant` — does it address the question?
- Summary includes average score, faithfulness rate, and relevance rate

## Interactive Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
