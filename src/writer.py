import re
from groq import Groq
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found. Make sure it is in your .env file.")

client = Groq(api_key=api_key)


def _slug_from_prompt(prompt: str) -> str:
    words = re.sub(r"[^a-z0-9 ]", "", prompt.lower()).split()
    slug = "_".join(words[:8])
    return f"test_{slug}"


def write_tests(
    crawl_data: dict,
    user_prompt: str,
    output_dir: str = None,
    show_browser: bool = False,
) -> str:

    headless_value = "False" if show_browser else "True"
    output_dir = output_dir or os.getcwd()

    prompt = f"""You are an expert QA automation engineer.
You write pytest tests using Playwright in Python.

I have crawled a webpage and found these interactive elements with their locators:

PAGE URL: {crawl_data["url"]}
PAGE TITLE: {crawl_data["title"]}

INPUTS FOUND:
{crawl_data["inputs"]}

BUTTONS FOUND:
{crawl_data["buttons"]}

LINKS FOUND:
{crawl_data["links"]}

USER INSTRUCTION:
{user_prompt}

Write a complete pytest Playwright test based on the instruction above.

LOCATOR RULES - follow these strictly:
1. Always prefer CSS selectors over XPath.
2. If CSS is not reliable, use get_by_role with the element's role and name.
3. If get_by_role is not reliable, use get_by_text with the visible text.
4. Never store a locator in a variable and call .click() on it separately.
   Always do it in one line like: page.locator('css').click()
5. After every major action add: page.wait_for_load_state('domcontentloaded')
6. After every click that triggers navigation add: page.wait_for_timeout(3000)
7. Use timeout=60000 on all wait_for_selector calls.
8. Launch the browser with headless={headless_value} exactly as written.
9. Always capture a screenshot even when the test fails. Structure the browser section like this:
   browser = p.chromium.launch(headless={headless_value})
   page = browser.new_page()
   try:
       # ... all test steps and assertions here ...
       page.screenshot(path=r'{output_dir}\result.png')
   except Exception:
       page.screenshot(path=r'{output_dir}\result.png')
       raise
   finally:
       browser.close()
10. Add a comment above each step explaining what it does.

Return ONLY the Python code. No explanation. No markdown backticks.
"""

    print("Sending data to Groq.....")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an expert QA automation engineer who writes pytest Playwright tests in Python.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    test_code = response.choices[0].message.content

    # Strip markdown fences if LLM adds them
    test_code = test_code.strip()
    if test_code.startswith("```python"):
        test_code = test_code[len("```python") :].strip()
    if test_code.startswith("```"):
        test_code = test_code[len("```") :].strip()
    if test_code.endswith("```"):
        test_code = test_code[:-3].strip()

    os.makedirs(os.path.join(output_dir, "generated_tests"), exist_ok=True)
    filename = _slug_from_prompt(user_prompt) + ".py"
    test_file = os.path.join(output_dir, "generated_tests", filename)

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"Test saved to {test_file}")
    return test_file
