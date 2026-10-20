from mcp.server.fastmcp import FastMCP
from monorepo.mcp.tools.schema import get_database_schema

mcp = FastMCP("monorepo")

@mcp.tool()
def hello(name: str) -> str:
    """Say hello to a user."""
    return f"Hello, {name}!"

@mcp.tool()
def inspect_database() -> dict:
    """Inspect the current PostgreSQL database and list its tables and columns."""
    return get_database_schema()

if __name__ == "__main__":
    mcp.run()
