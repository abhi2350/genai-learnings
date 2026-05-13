# Task Manager API

A RESTful Task Manager API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

## Features

- Create, read, update, and delete tasks
- PostgreSQL persistence via SQLAlchemy ORM
- Pydantic v2 schema validation
- Environment-based configuration

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Pydantic v2](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)

## Project Structure

```
task_manager/
├── main.py        # FastAPI app and route definitions
├── database.py    # DB engine and session setup
├── models.py      # SQLAlchemy ORM models
└── schemas.py     # Pydantic request/response schemas
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/abhi2350/genai-learnings.git
cd genai-learnings
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/taskdb
```

### 5. Run the server

```bash
cd task_manager
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint        | Description         |
|--------|-----------------|---------------------|
| POST   | `/tasks`        | Create a new task   |
| GET    | `/tasks`        | Get all tasks       |
| GET    | `/tasks/{id}`   | Get a task by ID    |
| PATCH  | `/tasks/{id}`   | Update a task       |
| DELETE | `/tasks/{id}`   | Delete a task       |

## Interactive Docs

FastAPI provides auto-generated docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
