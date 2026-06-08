from mcp import types

TOOLS: list[types.Tool] = [
    types.Tool(
        name="crawl_page",
        description="Crawl a webpage and extract all interactive elements like inputs, buttons and links with their locators. Always call this first before writing a test.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL of the webpage to crawl.",
                }
            },
            "required": ["url"],
        },
    ),
    types.Tool(
        name="write_test",
        description="Generate a pytest Playwright test based on crawl data and a user instruction. Always call crawl_page first to get the crawl_data. Returns the path to the generated test file — pass it as test_file when calling run_test.",
        inputSchema={
            "type": "object",
            "properties": {
                "crawl_data": {
                    "type": "string",
                    "description": "The crawl data returned by crawl_page as a JSON string.",
                },
                "instruction": {
                    "type": "string",
                    "description": "What the test should do.",
                },
                "output_dir": {
                    "type": "string",
                    "description": "The absolute path of the project the user is currently working in — this is where tests and reports will be saved. Use your working directory context to determine this. In Claude Code CLI this is the directory you were launched from. In VS Code it is the workspace root. Never use the MCP server's own directory. Never ask the user for it.",
                },
                "show_browser": {
                    "type": "boolean",
                    "description": "If true the browser opens visibly during the test. Default is false.",
                },
            },
            "required": ["crawl_data", "instruction", "output_dir"],
        },
    ),
    types.Tool(
        name="run_test",
        description="Run the generated pytest Playwright test. Automatically heals the test if it fails due to a locator error. Always call write_test first.",
        inputSchema={
            "type": "object",
            "properties": {
                "crawl_data": {
                    "type": "string",
                    "description": "The crawl data returned by crawl_page as a JSON string. Needed for auto-healing.",
                },
                "output_dir": {
                    "type": "string",
                    "description": "The absolute path of the project the user is currently working in. Must be the same value passed to write_test. Use your working directory context — never use the MCP server's own directory.",
                },
                "test_file": {
                    "type": "string",
                    "description": "Absolute path to the test file to run. Use the path returned by write_test. If omitted, falls back to test_generated.py.",
                },
            },
            "required": ["crawl_data", "output_dir"],
        },
    ),
]
