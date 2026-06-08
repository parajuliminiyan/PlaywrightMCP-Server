from mcp.server.fastmcp import FastMCP


mcp = FastMCP("Demo", json_response=True)


@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b


@mcp.resource("greeting:..{name}")
def get_greeting(name: str) -> str:
    return f"Hello, {name}!!"


@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a causal, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
