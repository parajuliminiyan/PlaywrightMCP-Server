import json
import os
from pathlib import Path

from src.crawler import crawl_page as crawl_page_fn
from src.writer import write_tests
from src.runner import run_test_with_healing
from src.reporter import format_text_report, generate_html_report


def handle_crawl(url: str) -> str:
    print(f"[crawl] {url}", flush=True)
    data = crawl_page_fn(url)
    return json.dumps(data, indent=2)


_SERVER_DIR = str(Path(__file__).resolve().parent.parent)


def _check_output_dir(output_dir: str) -> None:
    if os.path.abspath(output_dir) == os.path.abspath(_SERVER_DIR):
        print(
            f"[warning] output_dir is the MCP server directory itself ({_SERVER_DIR}). "
            "The agent may not have detected the correct project folder.",
            flush=True,
        )


def handle_write_test(
    crawl_data_str: str, instruction: str, output_dir: str, show_browser: bool
) -> str:
    _check_output_dir(output_dir)
    print(f"[write] output_dir={output_dir}", flush=True)
    crawl_data = json.loads(crawl_data_str)
    test_file = write_tests(
        crawl_data=crawl_data,
        user_prompt=instruction,
        output_dir=output_dir,
        show_browser=show_browser,
    )
    return f"Test generated and saved to: {test_file}"


def handle_run_test(crawl_data_str: str, output_dir: str, test_file: str | None = None) -> str:
    crawl_data = json.loads(crawl_data_str)
    if not test_file:
        test_file = os.path.join(output_dir, "generated_tests", "test_generated.py")
    print(f"[run] {test_file}", flush=True)

    report = run_test_with_healing(test_file=test_file, crawl_data=crawl_data)

    html_path = generate_html_report(report, output_dir)
    return format_text_report(report) + f"\n\n  HTML Report     : {html_path}"
