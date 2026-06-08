import base64
import datetime
import html as html_mod
import os
import webbrowser


def extract_pytest_summary(output: str) -> str:
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if stripped.startswith("=") and (
            "passed" in stripped or "failed" in stripped or "error" in stripped
        ):
            return stripped.strip("= ").strip()
    return ""


def format_text_report(report: dict) -> str:
    sep = "=" * 52
    status = report["status"]
    status_icon = (
        "PASSED [OK]"
        if status == "PASSED"
        else "FAILED [!!]"
        if status == "FAILED"
        else "ERROR [!!]"
    )
    summary = extract_pytest_summary(report.get("output", ""))

    lines = [
        sep,
        "  TEST RUN REPORT",
        sep,
        f"  Status      : {status_icon}",
        f"  Test File   : {report['test_file']}",
        f"  Auto-Healed : {'YES' if report.get('healed') else 'NO'}",
    ]

    if report.get("healed"):
        original = report.get("original_error", "").strip()
        if original:
            lines.append(f"  Original Error (first line): {original.splitlines()[0]}")

    if summary:
        lines.append(f"  Pytest Summary: {summary}")

    lines.append(sep)

    if status != "PASSED":
        lines.append("")
        lines.append("  FAILURE OUTPUT:")
        lines.append("")
        output_lines = report.get("output", "").splitlines()
        failure_block = [
            line
            for line in output_lines
            if line.strip() and not line.startswith("collecting")
        ]
        lines.extend(f"  {line}" for line in failure_block)
        lines.append("")
        lines.append(sep)
    else:
        lines.append("")
        lines.append("  All assertions passed. Screenshot saved to result.png")
        lines.append(sep)

    return "\n".join(lines)


def _build_html(
    report: dict, screenshot_b64: str | None, summary: str, timestamp: str
) -> str:
    status = report["status"]
    is_passed = status == "PASSED"
    status_label = (
        "PASSED" if is_passed else ("FAILED" if status == "FAILED" else "ERROR")
    )
    status_color = "#10b981" if is_passed else "#ef4444"
    healed = report.get("healed", False)
    run_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    if screenshot_b64:
        caption = "Final screenshot" if is_passed else "Screenshot at point of failure"
        screenshot_html = f"""
    <div class="card">
      <div class="card-header">Screenshot</div>
      <div class="card-body screenshot">
        <p class="caption">{caption}</p>
        <img src="data:image/png;base64,{screenshot_b64}" alt="test screenshot" />
      </div>
    </div>"""
    else:
        screenshot_html = """
    <div class="card">
      <div class="card-header">Screenshot</div>
      <div class="card-body"><p class="no-screenshot">No screenshot captured.</p></div>
    </div>"""

    failure_html = ""
    if not is_passed:
        output_lines = report.get("output", "").splitlines()
        failure_text = "\n".join(
            line
            for line in output_lines
            if line.strip() and not line.startswith("collecting")
        )
        failure_html = f"""
    <div class="card">
      <div class="card-header" style="color:#ef4444;">Failure Output</div>
      <div class="card-body">
        <pre>{html_mod.escape(failure_text)}</pre>
      </div>
    </div>"""

    healed_row = ""
    if healed:
        original = report.get("original_error", "").strip()
        first_line = original.splitlines()[0] if original else ""
        healed_row = f"""
        <tr><td>Original Error</td><td class="mono">{html_mod.escape(first_line)}</td></tr>"""

    status_class = "summary-ok" if is_passed else "summary-fail"
    healed_class = "healed-yes" if healed else "healed-no"
    healed_text = "YES" if healed else "NO"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Report — {status_label}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;color:#1a1a2e}}
.header{{background:#1a1a2e;color:#fff;padding:22px 40px;display:flex;align-items:center;gap:16px}}
.header h1{{font-size:20px;font-weight:600;letter-spacing:.3px}}
.badge{{padding:5px 16px;border-radius:20px;font-weight:700;font-size:13px;letter-spacing:1px;background:{status_color};color:#fff}}
.ts{{margin-left:auto;font-size:12px;color:#94a3b8}}
.container{{max-width:980px;margin:28px auto;padding:0 20px}}
.card{{background:#fff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.07);margin-bottom:22px;overflow:hidden}}
.card-header{{padding:13px 22px;border-bottom:1px solid #e5e7eb;font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:#6b7280}}
.card-body{{padding:22px}}
table{{width:100%;border-collapse:collapse}}
td{{padding:9px 0;border-bottom:1px solid #f3f4f6;font-size:14px;vertical-align:top}}
td:first-child{{color:#6b7280;width:170px;font-weight:500}}
td:last-child{{font-weight:500;word-break:break-all}}
.mono{{font-family:'Courier New',monospace;font-size:12px;font-weight:400}}
.healed-yes{{color:#f59e0b;font-weight:700}}
.healed-no{{color:#10b981;font-weight:700}}
pre{{background:#0f172a;color:#e2e8f0;padding:18px;border-radius:8px;font-size:12px;overflow-x:auto;white-space:pre-wrap;word-break:break-word;line-height:1.65}}
.screenshot img{{max-width:100%;border-radius:8px;border:1px solid #e5e7eb;margin-top:10px}}
.caption{{font-size:13px;color:#6b7280;margin-bottom:8px}}
.no-screenshot{{color:#9ca3af;font-style:italic;font-size:14px}}
.summary-ok{{color:#10b981;font-weight:700}}
.summary-fail{{color:#ef4444;font-weight:700}}
</style>
</head>
<body>
<div class="header">
  <h1>Test Run Report</h1>
  <span class="badge">{status_label}</span>
  <span class="ts">{run_time}</span>
</div>
<div class="container">
  <div class="card">
    <div class="card-header">Details</div>
    <div class="card-body">
      <table>
        <tr><td>Status</td><td class="{status_class}">{status_label}</td></tr>
        <tr><td>Test File</td><td class="mono">{report["test_file"]}</td></tr>
        <tr><td>Run Time</td><td>{run_time}</td></tr>
        <tr><td>Auto-Healed</td><td class="{healed_class}">{healed_text}</td></tr>
        <tr><td>Pytest Summary</td><td class="mono">{summary}</td></tr>
        {healed_row}
      </table>
    </div>
  </div>
  {failure_html}
  {screenshot_html}
</div>
</body>
</html>"""


def generate_html_report(report: dict, output_dir: str) -> str:
    """Write HTML report to test_results/. Returns the report file path."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(output_dir, "test_results")
    os.makedirs(results_dir, exist_ok=True)

    screenshot_path = os.path.join(output_dir, "result.png")
    screenshot_b64 = None
    if os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as f:
            screenshot_b64 = base64.b64encode(f.read()).decode("utf-8")

    summary = extract_pytest_summary(report.get("output", ""))
    html = _build_html(report, screenshot_b64, summary, timestamp)

    report_path = os.path.join(results_dir, f"report_{timestamp}.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(report_path)
    return report_path
