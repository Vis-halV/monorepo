from mcp.server.fastmcp import FastMCP

mcp = FastMCP("monorepo")

@mcp.tool()
def hello(name: str) -> str:
    """Say hello to a user."""
    return f"Hello, {name}!"
