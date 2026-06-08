# QA Automation MCP Server

An AI-powered QA automation tool built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It crawls web pages, generates Playwright-based pytest tests using an LLM, runs them, and automatically heals failing tests — all driven by natural language instructions.

---

## How It Works

```
User Instruction
      │
      ▼
 crawl_page(url)
      │  Headless Chromium extracts all interactive elements
      ▼
write_test(crawl_data, instruction, output_dir)
      │  Groq LLM generates a pytest + Playwright test file
      ▼
 run_test(crawl_data, output_dir)
      │  Pytest executes the generated test
      │
      ├── PASS → HTML report + text summary
      │
      └── FAIL (locator/timeout error)
              │
              ▼
         Auto-Healer
              │  Groq rewrites the broken locators
              ▼
         Re-run test
              │
              └── HTML report + text summary (marked "healed")
```

---

## Features

- **Page Crawling** — Extracts inputs, buttons, and links with CSS selectors, XPaths, and metadata
- **AI Test Generation** — Converts a plain-English instruction + crawl data into a complete pytest test file
- **Automated Execution** — Runs tests programmatically with `pytest` and captures all output
- **Auto-Healing** — Detects locator/timeout failures and sends the broken test back to the LLM for repair, then re-runs automatically
- **Rich Reporting** — Generates an HTML report with screenshots and a text summary; opens in browser automatically
- **Headless or Headed** — Browser is headless by default; pass `show_browser=true` to watch it run

---

## Architecture

```
MCP-server/
├── main.py            # MCP server entry point and request dispatcher
├── pyproject.toml     # Project metadata and dependencies
├── .env               # API keys (not committed)
└── src/
    ├── tools.py       # MCP tool definitions (schemas exposed to the client)
    ├── handlers.py    # Request handlers that wire tools to logic
    ├── crawler.py     # Playwright-based page crawling
    ├── writer.py      # LLM-powered test code generation
    ├── runner.py      # Pytest execution and result parsing
    ├── healer.py      # Auto-healing logic for failing tests
    └── reporter.py    # HTML and text report generation
```

---

## MCP Tools

The server exposes three tools to any MCP-compatible client.

### `crawl_page`

Crawls a URL and returns structured data about all interactive elements on the page.

| Parameter | Type   | Description          |
|-----------|--------|----------------------|
| `url`     | string | The page URL to crawl |

**Returns:** JSON with `title`, `inputs`, `buttons`, and `links`, each containing locator strategies (CSS selector, XPath) and metadata.

---

### `write_test`

Generates a pytest + Playwright test file from crawl data and a plain-English instruction.

| Parameter    | Type    | Description                                      |
|--------------|---------|--------------------------------------------------|
| `crawl_data` | string  | JSON output from `crawl_page`                    |
| `instruction`| string  | What to test, e.g. "submit the login form"       |
| `output_dir` | string  | Root directory where test files will be saved    |
| `show_browser`| boolean | Show the browser during execution (default: false)|

**Returns:** Path to the generated test file at `{output_dir}/generated_tests/test_*.py`.

---

### `run_test`

Executes the generated test and returns a report. Automatically attempts to heal locator/timeout failures.

| Parameter   | Type   | Description                                          |
|-------------|--------|------------------------------------------------------|
| `crawl_data`| string | JSON from `crawl_page` (used for healing)            |
| `output_dir`| string | Project root directory                               |
| `test_file` | string | Path to test file (optional; defaults to last generated) |

**Returns:** Text summary + path to the HTML report at `{output_dir}/test_results/report_*.html`.

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A [Groq API key](https://console.groq.com/)
- Playwright browsers installed

---

## Installation

**1. Clone the repository**

```bash
git clone <repo-url>
cd MCP-server
```

**2. Install dependencies**

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

**3. Install Playwright browsers**

```bash
uv run playwright install chromium
```

**4. Create a `.env` file**

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Running the Server

The server communicates over **stdio**, which is the standard transport for MCP clients like Claude Code.

```bash
uv run python main.py
```

---

## Connecting to Claude Code

Add the server to your Claude Code MCP configuration (`.claude/settings.json` or `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "qa-automation": {
      "command": "uv",
      "args": ["run", "python", "main.py"],
      "cwd": "/absolute/path/to/MCP-server"
    }
  }
}
```

Once connected, you can drive the entire QA workflow through natural language in Claude Code:

> "Crawl https://example.com, then write a test that fills in the search box and clicks Submit, and run it."

---

## Generated Output

Each test run produces the following structure inside `output_dir`:

```
{output_dir}/
├── generated_tests/
│   └── test_<slug>.py          # Generated pytest test file
├── test_results/
│   └── report_YYYYMMDD_HHMMSS.html   # HTML report with screenshot
└── result.png                  # Screenshot from the last test run
```

The HTML report is opened automatically in your default browser after each run.

---

## Auto-Healing

When a test fails due to a locator or timeout error, the healer:

1. Parses the pytest output to identify the broken locator
2. Sends the original test code, the error, and the fresh crawl data to the LLM
3. Receives a rewritten version with corrected selectors (`get_by_role`, `get_by_text`, or CSS)
4. Saves the patched file and re-runs the test
5. Marks the final report with `healed: true`

Only one healing attempt is made per run. Logic errors (wrong assertions, incorrect flow) are not healed automatically.

---

## Dependencies

| Package              | Purpose                              |
|----------------------|--------------------------------------|
| `mcp` / `fastmcp`    | MCP server framework                 |
| `playwright`         | Browser automation                   |
| `pytest`             | Test execution                       |
| `pytest-playwright`  | Playwright fixtures for pytest       |
| `groq`               | LLM API for test generation/healing  |
| `python-dotenv`      | `.env` file loading                  |
| `httpx`              | Async HTTP client                    |
| `pydantic`           | Data validation                      |

---

## LLM Configuration

- **Provider:** Groq
- **Model:** `llama-3.3-70b-versatile`
- **Temperature:** `0.3` for test generation, `0.1` for healing (tighter, more deterministic)

To switch models or providers, update [src/writer.py](src/writer.py) and [src/healer.py](src/healer.py).

---

## Limitations

- Auto-healing only addresses locator and timeout errors, not test logic errors
- Only one healing attempt per test run
- Authentication and multi-step login flows are not handled automatically
- Hardcoded to Groq's `llama-3.3-70b-versatile` model

---

## License

MIT
