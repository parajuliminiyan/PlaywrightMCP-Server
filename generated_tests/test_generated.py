import pytest
from playwright.sync_api import sync_playwright

def test_wells_fargo_business_line_of_credit_application():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.wellsfargo.com")
        page.wait_for_load_state("domcontentloaded")

        page.locator('a[href="/biz/"]').click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        page.locator('li.ps-fat-nav-subitem a[href="/biz/business-credit/"]').hover()
        page.wait_for_timeout(2000)

        page.locator('a.l3-product-tile[href="/biz/business-credit/"]').click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        page.get_by_role("link", name="Apply now").first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        page.get_by_role("button", name="Apply as guest").click()
        page.wait_for_timeout(3000)
        page.wait_for_load_state("domcontentloaded")

        page.locator('[class*="Control__control"]').click()
        page.wait_for_timeout(1000)
        page.locator('li[class*="Option__option"]:has-text("Sole Proprietor")').click()
        page.wait_for_timeout(1500)

        page.get_by_role("radio", name="Yes").click()
        page.wait_for_timeout(1000)

        page.locator('text="Agree and continue"').click()
        page.wait_for_timeout(3000)
        page.wait_for_load_state("domcontentloaded")

        assert page.get_by_text("verify your identity", exact=False).is_visible()

        assert page.locator('input#taxId').is_visible()
        assert page.locator('input#mobilePhone').is_visible()

        page.locator('input#taxId').fill("365432150")
        page.wait_for_timeout(500)

        page.locator('input#mobilePhone').fill("8049016538")
        page.wait_for_timeout(500)

        page.get_by_role("button", name="Agree and continue").click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        page.get_by_role("button", name="Cancel").click()
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="Yes, cancel").click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        assert page.get_by_text("canceled your application", exact=False).is_visible()

        page.screenshot(path='result.png')

        browser.close()