
from monorepo.mcp.connection import get_connection


def get_database_schema() -> dict:
    """Return the current database's tables and columns."""

    query = """
        SELECT
            table_schema,
            table_name,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema NOT IN (
            'information_schema',
            'pg_catalog'
        )
        ORDER BY
            table_schema,
            table_name,
            ordinal_position;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

            cur.execute("SELECT current_database()")
            database = cur.fetchone()[0]

    tables = {}

    for schema, table, column, data_type, nullable in rows:
        key = (schema, table)

        if key not in tables:
            tables[key] = {
                "schema": schema,
                "name": table,
                "columns": [],
            }

        tables[key]["columns"].append({
            "name": column,
            "type": data_type,
            "nullable": nullable == "YES",
        })

    return {
        "database": database,
        "tables": list(tables.values()),
    }
