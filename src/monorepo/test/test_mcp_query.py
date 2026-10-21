import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_query_tool_through_mcp():
    project_root = Path(__file__).resolve().parents[3]

    server = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--directory",
            str(project_root),
            "python",
            "-m",
            "monorepo.mcp.server",
        ],
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}

            assert "hello" in tool_names
            assert "inspect_database" in tool_names
            assert "execute_readonly_query_tool" in tool_names

            result = await session.call_tool(
                "execute_readonly_query_tool",
                {"sql": "SELECT email FROM public.users LIMIT 5"},
            )

            assert not result.isError, result.content

            # FastMCP should return the structured query result.
            assert result.structuredContent is not None

            data = result.structuredContent
            assert data["columns"] == ["email"]
            assert data["rows"] == []
            assert data["row_count"] == 0
            assert data["truncated"] is False
