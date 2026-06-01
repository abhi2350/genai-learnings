from typing import List
from anthropic import Anthropic
from pydantic import BaseModel
from database import execute_sql, get_schema
from dotenv import load_dotenv
from langfuse import observe
from langfuse import get_client

load_dotenv()

client = Anthropic()
langfuse = get_client()

def _record_usage(response) -> None:
    langfuse.update_current_generation(
        usage_details={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
        model="claude-opus-4-7",
    )

class TableSelection(BaseModel):
      tables: List[str]
      reason: str
    
class PrunedTable(BaseModel):
    # table name + list of columns to keep
    table: str
    columns: List[str]

class PrunedSchema(BaseModel):
    # list of PrunedTable
    tables: List[PrunedTable]
  
class GeneratedSQL(BaseModel):
    sql: str
    explanation: str

@observe()
def select_tables(question: str, schema: dict) -> TableSelection:
    table_list = list(schema.keys())

    # call Claude here
    # system: "You are a SQL expert"
    # user message: give it the table names + the question, ask which tables are needed
    # output_format: TableSelection
    msg = f"Here's the query: ${question} and table names: ${table_list}. Tell me which minimum tables are needed to solve the user's query"
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system="You are a SQL expert",
        messages=[{"role": "user", "content": msg}],
        output_format=TableSelection,
    )
    _record_usage(response)
    print(response.parsed_output)
    return response.parsed_output

@observe()
def prune_columns(question: str, selected_tables: List[str], schema: dict) -> PrunedSchema:
    result = {}
    for table in selected_tables:
      if table in schema:
        result[table] = schema[table]

    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system="You are a SQL expert",
        messages=[{
            "role": "user",
            "content": (
                f"Schema with table name and respective columns:\n{result}\n\n"
                f"Question: {question}\n\n"
                "for this question, which columns from each table do you actually need?"
                "Exclude columns that are irrelevant."
            ),
        }],
        output_format=PrunedSchema,
    )
    _record_usage(response)
    return response.parsed_output

@observe()
def generate_sql(question: str, pruned: PrunedSchema) -> GeneratedSQL:
    # format pruned schema as compact text: "users(id, name), orders(user_id, total)"
    # ask Claude to write a single PostgreSQL SELECT query
    # output_format: GeneratedSQL
    text = ""
    for pruned_table in pruned.tables:
        text += f"{pruned_table.table}({', '.join(pruned_table.columns)})"
      
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        system="You are a SQL expert",
        messages=[{
            "role": "user",
            "content": (
                f"Schema with table name and respective columns:\n{text}\n\n"
                f"Question: {question}\n\n"
                "write a single PostgreSQL SELECT query."
            ),
        }],
        output_format=GeneratedSQL,
    )
    _record_usage(response)
    return response.parsed_output

@observe()
def run_pipeline(question: str) -> dict:
    schema = get_schema()
    pruned_schema = select_tables(question, schema)
    pruned_columns = prune_columns(question, pruned_schema.tables, schema)
    sql_result = generate_sql(question, pruned_columns)
    rows = execute_sql(sql_result.sql)
    return {
        "explanation": sql_result.explanation,
        "question": question,
        "rows": rows,
        "sql": sql_result.sql,
        "tables_used": pruned_columns.tables,
    }

print(run_pipeline("How many orders are in each status?"))