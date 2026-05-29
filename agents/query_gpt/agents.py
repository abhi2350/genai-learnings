from typing import List
from pydantic import BaseModel
from anthropic import Anthropic
from database import get_schema, schema_to_text

client = Anthropic()
SYSTEM = "You are a SQL expert. You write precise, efficient PostgreSQL queries."


# ── Pydantic output schemas ───────────────────────────────────────────────────

class TableSelection(BaseModel):
    tables: List[str]
    reasoning: str


class ColumnInfo(BaseModel):
    column: str
    reason: str       # why this column is needed


class PrunedTable(BaseModel):
    table: str
    columns: List[ColumnInfo]


class PrunedSchema(BaseModel):
    tables: List[PrunedTable]


class GeneratedSQL(BaseModel):
    sql: str
    explanation: str  # plain-English description of what the query does


# ── Agent 1: pick relevant tables ────────────────────────────────────────────

def select_tables(question: str, all_tables: List[str]) -> TableSelection:
    table_list = ", ".join(all_tables)
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=512,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Available tables: {table_list}\n\n"
                f"Question: {question}\n\n"
                "Which tables are needed to answer this question? "
                "Only include tables that are directly required."
            ),
        }],
        output_format=TableSelection,
    )
    return response.parsed_output


# ── Agent 2: prune irrelevant columns ────────────────────────────────────────

def prune_columns(question: str, selected_tables: List[str], full_schema: dict) -> PrunedSchema:
    subset = {t: full_schema[t] for t in selected_tables if t in full_schema}
    schema_text = schema_to_text(subset)

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Schema:\n{schema_text}\n\n"
                f"Question: {question}\n\n"
                "For each table, list ONLY the columns needed to answer this question. "
                "Exclude columns that are irrelevant."
            ),
        }],
        output_format=PrunedSchema,
    )
    return response.parsed_output


# ── Agent 3: generate SQL ─────────────────────────────────────────────────────

def generate_sql(question: str, pruned: PrunedSchema) -> GeneratedSQL:
    schema_lines = []
    for t in pruned.tables:
        cols = ", ".join(c.column for c in t.columns)
        schema_lines.append(f"{t.table}({cols})")
    compact_schema = "\n".join(schema_lines)

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f"Schema:\n{compact_schema}\n\n"
                f"Question: {question}\n\n"
                "Write a single PostgreSQL SELECT query to answer this question. "
                "Return only the SQL — no markdown, no explanation in the sql field. "
                "Add a plain-English explanation in the explanation field."
            ),
        }],
        output_format=GeneratedSQL,
    )
    return response.parsed_output


# ── Full pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(question: str) -> dict:
    full_schema = get_schema()
    all_tables = list(full_schema.keys())

    # Step 1 — pick tables
    table_sel = select_tables(question, all_tables)

    # Step 2 — prune columns
    pruned = prune_columns(question, table_sel.tables, full_schema)

    # Step 3 — generate SQL
    sql_result = generate_sql(question, pruned)

    return {
        "question": question,
        "tables_used": table_sel.tables,
        "table_reasoning": table_sel.reasoning,
        "sql": sql_result.sql,
        "explanation": sql_result.explanation,
    }
