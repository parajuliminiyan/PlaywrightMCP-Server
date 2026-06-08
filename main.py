import asyncio
import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from src.tools import TOOLS
from src.handlers import handle_crawl, handle_write_test, handle_run_test

server = Server("qa-automation-mcp")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "crawl_page":
        result = await asyncio.to_thread(handle_crawl, arguments["url"])

    elif name == "write_test":
        result = await asyncio.to_thread(
            handle_write_test,
            arguments["crawl_data"],
            arguments["instruction"],
            os.path.abspath(arguments["output_dir"]),
            arguments.get("show_browser", False),
        )

    elif name == "run_test":
        test_file = arguments.get("test_file")
        result = await asyncio.to_thread(
            handle_run_test,
            arguments["crawl_data"],
            os.path.abspath(arguments["output_dir"]),
            os.path.abspath(test_file) if test_file else None,
        )

    else:
        result = f"Unknown tool: {name}"

    return [types.TextContent(type="text", text=result)]


async def main():
    print("[main] QA Automation MCP Server starting...", flush=True)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
