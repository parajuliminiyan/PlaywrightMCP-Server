from playwright.sync_api import sync_playwright


def get_xpath(element, page):
    element_id = element.get_attribute("id")
    if element_id:
        return f'//*[@id="{element_id}"]'

    element_name = element.get_attribute("name")
    if element_name:
        tag = element.evaluate("el => el.tagName.toLowerCase()")
        return f'//{tag}[@name="{element_name}"]'

    placeholder = element.get_attribute("placeholder")
    if placeholder:
        tag = element.evaluate("el => el.tagName.toLowerCase()")
        return f'//{tag}[@placeholder="{placeholder}"]'

    return page.evaluate(
        """
        (element) => {
            function getXPath(el) {
                if (el.id) return `//*[@id="${el.id}"]`;
                if (el === document.body) return '/html/body';
                let pos = 0;
                const siblings = el.parentNode.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === el) {
                        const tag = el.tagName.toLowerCase();
                        const parentPath = getXPath(el.parentNode);
                        return `${parentPath}/${tag}[${pos + 1}]`;
                    }
                    if (sibling.nodeType === 1 &&
                        sibling.tagName === el.tagName) {
                        pos++;
                    }
                }
            }
            return getXPath(element);
        }
    """,
        element,
    )


def crawl_page(url: str) -> dict:

    results = {"url": url, "title": "", "inputs": [], "buttons": [], "links": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        results["title"] = page.title()

        # --- INPUTS ---
        inputs = page.query_selector_all("input")
        for inp in inputs:
            input_type = inp.get_attribute("type") or "text"
            if input_type == "hidden":
                continue
            results["inputs"].append(
                {
                    "type": input_type,
                    "name": inp.get_attribute("name") or "",
                    "id": inp.get_attribute("id") or "",
                    "placeholder": inp.get_attribute("placeholder") or "",
                    "xpath": get_xpath(inp, page),
                }
            )

        # --- BUTTONS ---
        buttons = page.query_selector_all("button")
        for btn in buttons:
            text = btn.inner_text().strip()

            
            if not text:
                continue
            if len(text) > 30:
                continue
            if any(
                noise in text.lower()
                for noise in ["reset", "close modal", "show/hide", "shortcut"]
            ):
                continue

            results["buttons"].append(
                {
                    "text": text,
                    "type": btn.get_attribute("type") or "button",
                    "id": btn.get_attribute("id") or "",
                    "xpath": get_xpath(btn, page),
                }
            )

        # --- LINKS ---
        links = page.query_selector_all("a[href]")
        count = 0
        for link in links:
            if count >= 45:
                break
            text = link.inner_text().strip()
            href = link.get_attribute("href") or ""

        
            if not text:
                continue
            if len(text) > 40:
                continue
            if "javascript:void" in href:
                continue

            results["links"].append(
                {"text": text, "href": href, "xpath": get_xpath(link, page)}
            )
            count += 1

        browser.close()

    return results


if __name__ == "__main__":
    data = crawl_page("https://www.amazon.com")
    print(f"Title: {data['title']}")
    print(f"\nINPUTS ({len(data['inputs'])}):")
    for item in data["inputs"]:
        print(f"  {item}")
    print(f"\nBUTTONS ({len(data['buttons'])}):")
    for item in data["buttons"]:
        print(f"  {item}")
    print(f"\nLINKS ({len(data['links'])}):")
    for item in data["links"]:
        print(f"  {item}")
