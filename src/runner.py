import os
import pytest
import sys
import io
from src.healer import heal_test, apply_healed_test, is_locator_error


def run_test(test_file: str) -> dict:

    if not os.path.exists(test_file):
        return {
            "status": "ERROR",
            "test_file": test_file,
            "message": f"Test file not found: {test_file}",
            "output": f"Test file not found: {test_file}",
            "returncode": -1,
        }

    print(f"Running test {test_file}")

    output_buffer = io.StringIO()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = output_buffer
    sys.stderr = output_buffer

    try:
        returncode = pytest.main(
            [
                test_file,
                "-v",
                "--tb=short",
                "--no-header",
                "-p",
                "no:cacheprovider",  
            ]
        )
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    output = output_buffer.getvalue()
    status = "PASSED" if returncode == 0 else "FAILED"

    report = {
        "status": status,
        "test_file": test_file,
        "output": output,
        "returncode": int(returncode),
        "healed": False,
    }

    return report


def run_test_with_healing(test_file: str, crawl_data: dict) -> dict:

    report = run_test(test_file)

    if report["status"] == "PASSED":
        return report

    output = report.get("output", "")

    if not is_locator_error(output):
        print("[runner] Test failed but not a locator error — skipping auto-heal.")
        return report

    if not crawl_data:
        print("[runner] No crawl_data — cannot auto-heal.")
        return report

    print("[runner] Locator failure detected — attempting auto-heal...")

    fixed_code = heal_test(
        failed_output=output,
        crawl_data=crawl_data,
        test_file=test_file,
    )

    if fixed_code is None:
        print("[runner] Auto-heal failed — LLM returned nothing.")
        return report

    applied = apply_healed_test(fixed_code, test_file)

    if not applied:
        print("[runner] Failed to write healed test.")
        return report

    print("[runner] Re-running healed test...")
    healed_report = run_test(test_file)
    healed_report["healed"] = True
    healed_report["original_status"] = "FAILED"
    healed_report["original_error"] = output[:500]

    return healed_report
