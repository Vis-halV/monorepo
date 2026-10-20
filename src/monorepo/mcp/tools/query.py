from __future__ import annotations

from typing import Any

import psycopg
import sqlglot
from sqlglot import exp

from monorepo.mcp.connection import get_connection

MAX_ROWS = 100
STATEMENT_TIMEOUT_MS = 5_000

# Reject operations that can modify data, schema, permissions, or session state.
FORBIDDEN_NODE_TYPES = {
    "alter",
    "command",
    "commit",
    "copy",
    "create",
    "delete",
    "drop",
    "grant",
    "insert",
    "into",
    "lock",
    "merge",
    "pragma",
    "revoke",
    "rollback",
    "set",
    "transaction",
    "truncate",
    "update",
    "use",
}

def validate_readonly_sql(sql: str) -> str:
    """Validate one PostgreSQL read-only query and return its original SQL."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL must be a non-empty string.")

    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise ValueError("Invalid PostgreSQL SQL syntax.") from exc

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Exactly one SQL statement is allowed.")

    tree = statements[0]

    # Permit SELECT and set operations such as UNION, INTERSECT, and EXCEPT.
    if not isinstance(tree, (exp.Select, exp.Union, exp.Intersect, exp.Except)):
        raise ValueError("Only read-only SELECT queries are allowed.")

    # Inspect the complete AST, including CTE bodies and nested expressions.
    for node in tree.walk():
        if node.key.lower() in FORBIDDEN_NODE_TYPES:
            raise ValueError(
                f"SQL contains a prohibited operation: {node.key.lower()}."
            )

    return sql.strip()


def execute_readonly_query(sql: str) -> dict[str, Any]:
    """Execute one validated read-only query and return structured results."""
    validated_sql = validate_readonly_sql(sql)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Enforce read-only mode and a timeout at the database level.
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(
                    "SELECT set_config('statement_timeout', %s, true)",
                    (f"{STATEMENT_TIMEOUT_MS}ms",),
                )

                cur.execute(validated_sql)

                if cur.description is None:
                    raise ValueError("The query did not return a result set.")

                columns = [column.name for column in cur.description]
                fetched_rows = cur.fetchmany(MAX_ROWS + 1)
                truncated = len(fetched_rows) > MAX_ROWS
                fetched_rows = fetched_rows[:MAX_ROWS]

                rows = [
                    dict(zip(columns, row))
                    for row in fetched_rows
                ]

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }

    except psycopg.Error:
        # Avoid returning database details that might reveal internal information.
        raise RuntimeError(
            "The read-only database query failed. Check the SQL and database logs."
        ) from None
