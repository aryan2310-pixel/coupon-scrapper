import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

STORAGE_STATE_FILE = "zepto_session.json"
OUTPUT_FILE = "zepto_coupons.json"
WAIT_TIMEOUT_SECONDS = 5


def extract_coupons(response_data):
    coupons = []

    widgets = response_data.get("pageLayout", {}).get("widgets", [])

    for widget in widgets:

        if widget.get("widgetType") != "COUPON_CARD_WIDGET":
            continue

        items = widget.get("data", {}).get("items", {})

        heading = items.get("heading", {})
        coupon_button = items.get("couponButton", {})

        action = coupon_button.get("action", {})
        action_meta = action.get("actionMeta", {})

        coupon_code = action_meta.get("couponCode")
        title = heading.get("text")

        state = coupon_button.get("state")

        subheading = items.get("subheading", {})
        unlock_message = subheading.get("text")

        terms = items.get("termsAndConditions", {})
        description = terms.get("description")

        coupons.append({
            "coupon_code": coupon_code,
            "title": title,
            "state": state,
            "unlock_message": unlock_message,
            "description": description
        })

    return coupons


def is_coupon_response(response):
    if "fetch-list" not in response.url:
        return False

    if "application/json" not in response.headers.get("content-type", ""):
        return False

    try:
        data = response.json()
    except Exception:
        return False

    page_type = data.get("pageLayout", {}).get("pageMeta", {}).get("pageType")
    return page_type == "COUPON"


def print_coupons(coupons):
    print("\n")
    print("=" * 70)
    print("CURRENT ZEPTO OFFERS")
    print("=" * 70)

    for index, coupon in enumerate(coupons, start=1):

        print(f"\n{index}. {coupon['title']}")

        if coupon["coupon_code"]:
            print(f"   Coupon Code : {coupon['coupon_code']}")

        if coupon["state"]:
            print(f"   Status      : {coupon['state']}")

        if coupon["unlock_message"]:
            print(f"   Requirement : {coupon['unlock_message']}")

        if coupon["description"]:
            print(f"   Details     : {coupon['description']}")

    print("\n" + "=" * 70)


def main():

    coupon_response = None
    captured_event = threading.Event()

    session_path = Path(STORAGE_STATE_FILE)
    has_session = session_path.exists() and session_path.stat().st_size > 0

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(headless=False)

        context = browser.new_context(
            storage_state=STORAGE_STATE_FILE if has_session else None
        )

        page = context.new_page()

        def handle_response(response):
            nonlocal coupon_response

            if not is_coupon_response(response):
                return

            try:
                coupon_response = response.json()
                print("\nCoupon API response captured!")
                captured_event.set()
            except Exception:
                pass

        page.on("response", handle_response)

        print("Opening Zepto...")

        page.goto("https://www.zeptonow.com/", wait_until="domcontentloaded")

        print("\nBrowser opened.")

        if not has_session:
            print("Log in to Zepto (your session will be saved for next time).")
        else:
            print("Log in if prompted (your saved session may still be valid).")

        # No timeout here - takes as long as you need to log in
        input("\nPress Enter once you're logged in and ready to open Coupons... ")

        print("Now open Cart → Coupons & Offers → Coupons.")
        print(f"Waiting up to {WAIT_TIMEOUT_SECONDS}s for the coupon API response...")

        # Returns as soon as the response is captured, instead of always
        # blocking for the full timeout
        captured_event.wait(timeout=WAIT_TIMEOUT_SECONDS)

        # Save session so you skip the manual login step next run
        context.storage_state(path=STORAGE_STATE_FILE)

        if coupon_response is None:
            print("\nCould not find the coupon fetch-list response.")
            print("Make sure you opened the Coupons page.")
        else:
            coupons = extract_coupons(coupon_response)
            print_coupons(coupons)

            Path(OUTPUT_FILE).write_text(json.dumps(coupons, indent=2))
            print(f"\nSaved to {OUTPUT_FILE}")

        print("\nPress Enter to close the browser...")
        input()

        browser.close()


if __name__ == "__main__":
    main()