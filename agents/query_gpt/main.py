from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_schema, execute_sql, schema_to_text
from agents import run_pipeline

app = FastAPI(title="QueryGPT — Natural Language to SQL")


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(payload: QueryRequest):
    try:
        result = run_pipeline(payload.question)
        rows = execute_sql(result["sql"])
        result["rows"] = rows
        result["row_count"] = len(rows)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
def schema():
    return get_schema()


@app.get("/schema/text")
def schema_text():
    return {"schema": schema_to_text(get_schema())}


@app.get("/")
def root():
    return {
        "message": "QueryGPT — POST /query with {question}",
        "example": {"question": "Show me the top 5 best-selling products"},
    }
