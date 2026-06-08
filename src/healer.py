import re
import os
import logging
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def is_locator_error(output: str) -> bool:
    """Check if the failure is a locator/timeout issue worth healing."""
    signals = [
        "TimeoutError",
        "waiting for locator",
        "Timeout 30000ms exceeded",
        "Timeout 60000ms exceeded",
        "locator.click",
        "Locator.click",
        "locator.first",
        "strict mode violation",
        "resolved to 2 elements",
        "resolved to 3 elements",
        "Element is not visible",
        "waiting for get_by_text",
        "waiting for get_by_role",
    ]
    return any(s in output for s in signals)


def extract_failed_locator(output: str) -> str | None:
    """Pull the exact failing locator string out of pytest output."""
    match = re.search(r'waiting for locator\("(.+?)"\)', output)
    if match:
        return match.group(1)
    match = re.search(r'Locator\.[a-z]+: Timeout.*?locator\("(.+?)"\)', output)
    if match:
        return match.group(1)
    return None


def heal_test(failed_output: str, crawl_data: dict, test_file: str) -> str | None:
    if not os.path.exists(test_file):
        logging.error(f"[healer] Test file not found: {test_file}")
        return None

    with open(test_file, "r", encoding="utf-8") as f:
        current_test_code = f.read()

    failed_locator = extract_failed_locator(failed_output)

    locator_hint = (
        f"\nThe specific locator that timed out: {failed_locator}"
        if failed_locator
        else ""
    )

    prompt = f"""You are an expert QA automation engineer specializing in Playwright Python test debugging.
 
The following pytest Playwright test FAILED with a locator timeout error.
Your job is to rewrite the broken locator(s) so the test passes.
 
=== FAILING TEST CODE ===
{current_test_code}
 
=== PYTEST ERROR OUTPUT ===
{failed_output[:3000]}
{locator_hint}
 
PAGE CRAWL DATA (use this to find better locators)
PAGE URL: {crawl_data.get("url", "unknown")}
PAGE TITLE: {crawl_data.get("title", "unknown")}
 
INPUTS FOUND:
{crawl_data.get("inputs", [])}
 
BUTTONS FOUND:
{crawl_data.get("buttons", [])}
 
LINKS FOUND:
{crawl_data.get("links", [])}
 
HOW TO FIX:
 
Step 1 - Identify the broken locator from the error output above.
Step 2 - Find the same element in the crawl data using its text, role, or attributes.
Step 3 - Replace the broken locator using this priority order:
 
   Priority 1 - CSS selector:
      page.locator('tag[attribute="value"]').click()
 
   Priority 2 - get_by_role with visible name:
      page.get_by_role("button", name="Submit").click()
      page.get_by_role("link", name="Product title").click()
 
   Priority 3 - get_by_text with visible text:
      page.get_by_text("Add to cart").click()
 
RULES:

1. Use the crawl data to understand what elements exist on the page.
2. Pick the strategy above that best matches the element you need to click.
3. NEVER use XPath. Always use CSS, get_by_role, or get_by_text.
4. NEVER store a locator in a variable and call .click() separately.
   Always do it in one line: page.locator('css').click()
5. If the broken line is a variable assignment like:
      first_result = page.locator('xpath=...').first
      first_result.click()
   Replace BOTH lines with a single line using the correct locator.
6. After every click that triggers navigation add: page.wait_for_timeout(3000)
7. Change any wait_for_load_state('networkidle') to wait_for_load_state('domcontentloaded')
8. Use timeout=60000 on all wait_for_selector calls.
9. Keep all other working parts of the test exactly the same.
10. If the test uses a try/except/finally block around browser.close(), preserve that structure exactly.
 
Return ONLY the fixed Python code. No explanation. No markdown backticks.
"""

    logging.info("[healer] Asking Groq to heal the test...")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert QA automation engineer who fixes broken Playwright Python tests.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )

        fixed_code = response.choices[0].message.content.strip()

        # Strip any accidental markdown fences the LLM adds
        if fixed_code.startswith("```python"):
            fixed_code = fixed_code[len("```python") :].strip()
        if fixed_code.startswith("```"):
            fixed_code = fixed_code[len("```") :].strip()
        if fixed_code.endswith("```"):
            fixed_code = fixed_code[:-3].strip()

        return fixed_code

    except Exception as e:
        logging.error(f"[healer] Groq call failed: {e}")
        return None


def apply_healed_test(fixed_code: str, test_file: str) -> bool:
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        logging.info(f"[healer] Healed test saved to {test_file}")
        return True
    except Exception as e:
        logging.error(f"[healer] Failed to write healed test: {e}")
        return False
