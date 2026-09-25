import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

ZEPTO_URL = "https://www.zeptonow.com/"
STORAGE_STATE_FILE = "zepto_session.json"
OUTPUT_FILE = "zepto_coupons.json"

def extract_coupons(coupon_response):

    coupons = []

    widgets = (coupon_response.get("pageLayout", {}).get("widgets", []))

    for widget in widgets:

        if widget.get("widgetType") != "COUPON_CARD_WIDGET":
            continue

        data = widget.get("data", {})
        items = data.get("items", {})

        heading = items.get("heading", {})
        title = heading.get("text", "")

        coupon_button = items.get("couponButton")

        if coupon_button:

            action = coupon_button.get("action", {})
            action_meta = action.get("actionMeta", {})

            code = action_meta.get("couponCode", "")

            state = coupon_button.get("state", "")

        else:

            coupon_code_block = items.get("couponCode", {})
            coupon_code_text = coupon_code_block.get("text", "")

            if "auto-applied" in coupon_code_text.lower():
                code = ""
                state = "Auto-applied"
            else:
                code = coupon_code_text
                state = ""

        subheading = items.get("subheading", {})
        unlock_message = subheading.get("text", "")

        terms = items.get("termsAndConditions", {})
        details = terms.get("description", "")

        coupons.append({
            "title": title,
            "code": code,
            "state": state,
            "unlock_message": unlock_message,
            "details": details
        })

    return coupons


def print_coupons(coupons):

    print("\n")
    print("=" * 60)
    print("CURRENT ZEPTO OFFERS")
    print("=" * 60)

    if not coupons:
        print("No coupons found.")
        return

    for index, coupon in enumerate(coupons, start=1):

        print(f"\n{index}. {coupon['title']}")

        if coupon["code"]:
            print(f"Code: {coupon['code']}")

        if coupon["state"]:
            print(f"State: {coupon['state']}")

        if coupon["unlock_message"]:
            print(f"Unlock Message : {coupon['unlock_message']}")

        if coupon["details"]:
            print(f"Details: {coupon['details']}")

    print("\n" + "=" * 60)


def save_coupons(coupons):

    with open(OUTPUT_FILE,"w",encoding="utf-8") as file:

        json.dump(coupons,file,indent=4,ensure_ascii=False)

    print(f"\nCoupons saved to {OUTPUT_FILE}")


def main():

    with sync_playwright() as playwright:

        session_path = Path(STORAGE_STATE_FILE)

        has_session = (session_path.exists() and session_path.stat().st_size > 0)

        HEADLESS_MODE = False  # Set to False so Playwright doesn't inject '--headless'
        browser = playwright.chromium.launch(
            headless=HEADLESS_MODE,
            args=[
                "--headless=new",  # Use Chrome's new native headless mode!
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080}
        }
        if has_session:
            context_options["storage_state"] = STORAGE_STATE_FILE

        context = browser.new_context(**context_options)

        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        # --------------------------------------------------
        # OPEN ZEPTO
        # --------------------------------------------------

        print("\nOpening Zepto...")

        page.goto(ZEPTO_URL,wait_until="domcontentloaded")

        print("\nZepto opened.")

        if not HEADLESS_MODE:
            print("\nIf required, log in to your Zepto account.")
            input("\nPress Enter when you are ready to continue...")
        else:
            print("\nRunning in headless mode. Bypassing manual login prompt (relying on zepto_session.json)...")

        # --------------------------------------------------
        # ADD FIRST PRODUCT TO CART
        # --------------------------------------------------

        print("\n" + "-" * 60)
        print("ADDING FIRST PRODUCT TO CART")
        print("-" * 60)

        try:

            add_button = page.locator('button[data-mode="edlp"]:has-text("ADD")').first

            print("\nWaiting for first ADD button...")

            add_button.wait_for(state="visible",timeout=30000)

            print("First ADD button found.")

            add_button.click()

            print("Product added to cart.")

        except Exception as error:

            print("\nCould not add product to cart.")
            print("Error:", error)
            
            page.screenshot(path="debug_headless_error.png")
            print("Saved debug screenshot to debug_headless_error.png")

            browser.close()
            return

        # --------------------------------------------------
        # OPEN CART + CAPTURE CART RESPONSE
        # --------------------------------------------------

        print("\n" + "-" * 60)
        print("OPENING CART")
        print("-" * 60)

        try:

                # Give the ADD request a moment to finish
                page.wait_for_timeout(1500)

                print("\nClicking Cart...")

                # Adjust this selector if Zepto changes its cart UI.
                page.locator('button[aria-label="Cart"][data-testid="cart-btn"]').first.click()

        except Exception as error:

            print("\nCould not capture the cart response.")

            print("Error:", error)

            browser.close()
            return

        # --------------------------------------------------
        # FETCH COUPONS
        # --------------------------------------------------

        print("\n" + "-" * 60)
        print("FETCHING COUPONS")
        print("-" * 60)

        def is_coupon_response(response):

            return ("coupons/fetch-list" in response.url.lower())

        try:

            with page.expect_response(is_coupon_response,timeout=15000) as coupon_response_info:

                page.get_by_text("View coupons",exact=True).click()

            coupon_api_response = (coupon_response_info.value)

            print("\nCoupon fetch-list status:",coupon_api_response.status)

            if not coupon_api_response.ok:

                print("Coupon fetch-list request failed.")

                print(coupon_api_response.text()[:2000])

                browser.close()
                return

            coupon_response = (coupon_api_response.json())

        except Exception as error:

            print("\nError while fetching coupons:",error)

            print("\nTip: make sure the Cart page with the View coupons row is visible.")
            browser.close()
            return

        # --------------------------------------------------
        # EXTRACT COUPONS
        # --------------------------------------------------

        coupons = extract_coupons(coupon_response)

        print_coupons(coupons)

        save_coupons(coupons)

        # --------------------------------------------------
        # SAVE SESSION
        # --------------------------------------------------

        context.storage_state(path=STORAGE_STATE_FILE)
        
        if not HEADLESS_MODE:
            input("\nPress Enter to close the browser...")

        browser.close()


if __name__ == "__main__":
    main()