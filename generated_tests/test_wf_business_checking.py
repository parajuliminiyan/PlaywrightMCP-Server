import re
import pytest
from playwright.sync_api import sync_playwright, expect


def test_wells_fargo_initiate_business_checking_application():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # ── Step 1: Navigate to wellsfargo.com ──────────────────────────────
        page.goto("https://www.wellsfargo.com")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # ── Step 2: Click the Business tab ──────────────────────────────────
        page.locator('a[href="/biz/"]').first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # ── Step 3: Hover over "Checking" to open the dropdown ──────────────
        page.locator('a[href="/biz/checking/"]').first.hover()
        page.wait_for_timeout(1500)

        # ── Step 4: Click "Initiate Business Checking" ───────────────────────
        page.locator('a[href="/biz/checking/initiate/"]').first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # ── Step 5: Handle zip code prompt if present ────────────────────────
        zip_input = page.locator(
            'input[placeholder*="ZIP" i], input[id*="zip" i], input[name*="zip" i]'
        )
        if zip_input.count() > 0:
            try:
                zip_input.first.wait_for(state="visible", timeout=3000)
                zip_input.first.fill("20120")
                page.wait_for_timeout(500)
                page.locator('button:has-text("Continue")').first.click()
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception:
                pass  # zip code prompt did not appear

        # ── Step 6: Click the "Open now" button ─────────────────────────────
        # The link href is: /wf/product/apply?prodSet=BISAPP2K&prodCode=BISCHK-C1
        # Use text matching to avoid CSS issues with '?' in the href
        open_now = page.get_by_role("link", name=re.compile(r"open now", re.IGNORECASE))
        open_now.first.wait_for(state="visible", timeout=10000)
        open_now.first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        # ── Step 7: Click "Apply as Guest" ──────────────────────────────────
        apply_guest = page.get_by_role(
            "button", name=re.compile(r"apply as guest", re.IGNORECASE)
        )
        if apply_guest.count() == 0:
            apply_guest = page.get_by_role(
                "link", name=re.compile(r"apply as guest", re.IGNORECASE)
            )
        apply_guest.first.wait_for(state="visible", timeout=15000)
        apply_guest.first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # ── Step 8: Enter "Tea and Coffee" in Legal business name field ──────
        legal_name = page.locator(
            'input[placeholder*="Legal business name" i], '
            'input[id*="businessName"], input[id*="legalName"], '
            'input[name*="businessName"], input[name*="legalName"]'
        ).first
        legal_name.wait_for(state="visible", timeout=10000)
        legal_name.fill("Tea and Coffee")
        page.wait_for_timeout(500)

        # ── Step 9: Select "Sole Proprietor" from business structure ─────────
        # Try react-select style first
        react_dropdown = page.locator(
            '[class*="__control"], [class*="Control__control"]'
        )
        if react_dropdown.count() > 0:
            react_dropdown.first.click()
            page.wait_for_timeout(800)
            page.locator(
                '[class*="__option"]:has-text("Sole Proprietor"), '
                '[class*="Option__option"]:has-text("Sole Proprietor")'
            ).first.click()
        else:
            # Native <select>
            page.locator('select').first.select_option(label="Sole Proprietor")
        page.wait_for_timeout(800)

        # ── Step 10: Click the "Yes" radio button ────────────────────────────
        yes_radio = page.locator(
            'input[type="radio"][value="yes"], '
            'input[type="radio"][value="Yes"], '
            'input[type="radio"][value="Y"], '
            'input[type="radio"][value="true"]'
        )
        if yes_radio.count() > 0:
            yes_radio.first.click()
        else:
            # Try by label
            page.locator('label').filter(has_text=re.compile(r"^Yes$")).locator('input[type="radio"]').first.click()
        page.wait_for_timeout(500)

        # ── Step 11: Click "Agree and Continue" ─────────────────────────────
        page.get_by_role(
            "button", name=re.compile(r"agree and continue", re.IGNORECASE)
        ).first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        # ── Step 12: Verify identity page ────────────────────────────────────
        expect(
            page.get_by_text("Now, let's verify your identity", exact=False)
        ).to_be_visible(timeout=15000)

        ssn_field = page.locator(
            'input[placeholder*="SSN or ITIN" i], '
            'input[placeholder*="SSN" i], '
            'input[id="taxId"], '
            'input[name="taxId"]'
        ).first
        ssn_field.wait_for(state="visible", timeout=10000)
        expect(ssn_field).to_be_visible()

        phone_field = page.locator('#mobilePhone')
        phone_field.wait_for(state="visible", timeout=10000)
        expect(phone_field).to_be_visible()

        # ── Step 13: Fill SSN and phone fields ───────────────────────────────
        ssn_field.fill("365432150")
        page.wait_for_timeout(500)
        phone_field.fill("8049016538")
        page.wait_for_timeout(500)

        # ── Step 14: Click "Agree and Continue" ──────────────────────────────
        page.get_by_role(
            "button", name=re.compile(r"agree and continue", re.IGNORECASE)
        ).first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        # ── Step 15: Click Cancel ─────────────────────────────────────────────
        page.get_by_role(
            "button", name=re.compile(r"^cancel$", re.IGNORECASE)
        ).first.click()
        page.wait_for_timeout(2000)

        # ── Step 16: Click "Yes, Cancel" in the popup ────────────────────────
        page.get_by_role(
            "button", name=re.compile(r"yes,?\s*cancel", re.IGNORECASE)
        ).first.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(3000)

        # ── Step 17: Verify cancellation ─────────────────────────────────────
        expect(
            page.get_by_text("We've canceled your application", exact=False)
        ).to_be_visible(timeout=15000)

        page.screenshot(path="F:/AI/MCP-server/test_results/wf_business_checking_result.png")
        context.close()
        browser.close()
