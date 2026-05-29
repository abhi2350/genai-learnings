import os
from unittest import result
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


# def _connect():
#     return psycopg2.connect(os.getenv("DATABASE_URL"))


# def get_schema() -> dict[str, list[dict]]:
#     """Returns full schema: {table_name: [{column, type, nullable, foreign_key}]}"""
#     query = """
#         SELECT
#             c.table_name,
#             c.column_name,
#             c.data_type,
#             c.is_nullable,
#             kcu.column_name AS fk_column,
#             ccu.table_name  AS fk_ref_table,
#             ccu.column_name AS fk_ref_column
#         FROM information_schema.columns c
#         LEFT JOIN information_schema.key_column_usage kcu
#             ON c.table_name = kcu.table_name
#             AND c.column_name = kcu.column_name
#             AND kcu.constraint_name IN (
#                 SELECT constraint_name FROM information_schema.table_constraints
#                 WHERE constraint_type = 'FOREIGN KEY'
#             )
#         LEFT JOIN information_schema.referential_constraints rc
#             ON kcu.constraint_name = rc.constraint_name
#         LEFT JOIN information_schema.constraint_column_usage ccu
#             ON rc.unique_constraint_name = ccu.constraint_name
#         WHERE c.table_schema = 'public'
#         ORDER BY c.table_name, c.ordinal_position
#     """
#     schema: dict[str, list[dict]] = {}
#     with _connect() as conn:
#         with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
#             cur.execute(query)
#             for row in cur.fetchall():
#                 table = row["table_name"]
#                 if table not in schema:
#                     schema[table] = []
#                 col: dict = {
#                     "column": row["column_name"],
#                     "type": row["data_type"],
#                     "nullable": row["is_nullable"] == "YES",
#                 }
#                 if row["fk_ref_table"]:
#                     col["references"] = f"{row['fk_ref_table']}.{row['fk_ref_column']}"
#                 schema[table].append(col)
#     return schema


# def execute_sql(sql: str) -> list[dict]:
#     """Run a SELECT query and return rows as list of dicts."""
#     with _connect() as conn:
#         with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
#             cur.execute(sql)
#             return [dict(row) for row in cur.fetchall()]


# def schema_to_text(schema: dict[str, list[dict]]) -> str:
#     """Format schema as human-readable text for prompts."""
#     lines = []
#     for table, columns in schema.items():
#         lines.append(f"Table: {table}")
#         for col in columns:
#             ref = f"  → {col['references']}" if col.get("references") else ""
#             nullable = " (nullable)" if col["nullable"] else ""
#             lines.append(f"  - {col['column']}: {col['type']}{nullable}{ref}")
#         lines.append("")
#     return "\n".join(lines)


def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def get_schema():
    query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query)
    rows = cur.fetchall()
    results = {}
    for row in rows:
        if row[0] not in results:
            results[row[0]] = [ row[1] ]
        else:
            results[row[0]].append(row[1])
    # print(results)
    conn.close()
    return results

def execute_sql(sql: str) -> list:
    # connect, run sql, return list of dicts
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# rows = execute_sql("SELECT name, total FROM orders JOIN users ON orders.user_id = users.id")
# for row in rows:
#     print(row)