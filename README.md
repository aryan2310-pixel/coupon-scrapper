# Zepto Coupon Fetcher

A small Python script that uses [Playwright](https://playwright.dev/python/) to open Zepto, add a product to your cart, open the coupons list, and capture the coupons currently available on your account. Results are printed in the terminal and saved to a JSON file.

## How It Works

1. Launches a visible Chromium browser and opens `https://www.zeptonow.com/`.
2. Reuses a saved login session (`zepto_session.json`) if one exists.
3. Pauses so you can log in and/or set your delivery location manually.
4. Adds the first available product (the first `ADD` button) to the cart.
5. Opens the cart and clicks **View coupons**.
6. Intercepts the `coupons/fetch-list` network response and parses the coupon cards from it.
7. Prints the coupons, saves them to `zepto_coupons.json`, and saves your session for next time.

Instead of scraping the rendered page, the script reads the JSON returned by Zepto's own coupon API call, so the data is structured and reliable as long as the response format stays the same.

## Requirements

- Python 3.8+
- [Playwright for Python](https://playwright.dev/python/)
- A Zepto account with a delivery location set

## Installation

```bash
# 1. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 2. Install Playwright
pip install playwright

# 3. Download the Chromium browser used by Playwright
playwright install chromium
```

## Usage

```bash
python zepto_coupons.py
```

Replace `zepto_coupons.py` with whatever you named the script.

Then follow the prompts in the terminal:

1. A browser window opens on Zepto.
2. **First run:** log in and make sure your delivery location is set so products are visible.
3. Switch back to the terminal and press **Enter**.
4. The script adds a product, opens the cart, and fetches the coupons automatically.
5. Once the results are shown, press **Enter** again to close the browser.

On later runs, your saved session is reused, so you usually won't need to log in again.

## Output

### Terminal

```
============================================================
CURRENT ZEPTO OFFERS
============================================================

1. Flat ₹50 off
Code: SAVE50
State: APPLY
Unlock Message : Add items worth ₹100 more to unlock
Details: Valid on orders above ₹299 ...
```

### `zepto_coupons.json`

A list of coupon objects:

```json
[
    {
        "title": "Flat ₹50 off",
        "code": "SAVE50",
        "state": "APPLY",
        "unlock_message": "Add items worth ₹100 more to unlock",
        "details": "Valid on orders above ₹299 ..."
    }
]
```

| Field            | Description                                                                 |
| ---------------- | --------------------------------------------------------------------------- |
| `title`          | Coupon heading                                                              |
| `code`           | Coupon code (empty for auto-applied offers)                                 |
| `state`          | Button state from the app, or `Auto-applied` for offers applied automatically |
| `unlock_message` | Message describing what's needed to unlock the coupon                       |
| `details`        | Terms and conditions text                                                   |

> The values above are illustrative. Actual content depends on your account and current offers.

## Configuration

Constants at the top of the script:

| Constant             | Default               | Purpose                          |
| -------------------- | --------------------- | -------------------------------- |
| `ZEPTO_URL`          | `https://www.zeptonow.com/` | Site to open               |
| `STORAGE_STATE_FILE` | `zepto_session.json`  | Where the login session is saved |
| `OUTPUT_FILE`        | `zepto_coupons.json`  | Where coupons are written        |

## Project Files

```
.
├── zepto_coupons.py       # The script
├── zepto_session.json     # Saved browser session (created after first successful run)
├── zepto_coupons.json     # Extracted coupons (created after each run)
└── README.md
```

## Important Notes

- **A product is added to your cart.** The script needs a non-empty cart to see coupons. Remove the item afterwards if you don't want it. The script does not place an order.
- **Keep `zepto_session.json` private.** It contains your login cookies and tokens. If you use Git, add it to `.gitignore`:
  ```
  zepto_session.json
  ```
- **The session is only saved on success.** If the script exits early because of an error, the session is not written.
- **The browser runs in headed mode** (`headless=False`) so you can log in and watch what's happening.

## Troubleshooting

| Problem                                    | What to try                                                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| "Could not add product to cart"            | Make sure you're logged in and a delivery location is set, so products with an `ADD` button are visible.     |
| "Could not capture the cart response"      | Zepto may have changed its UI. Update the cart button selector: `button[aria-label="Cart"][data-testid="cart-btn"]`. |
| "Error while fetching coupons"             | Confirm the cart is open and the **View coupons** row is visible. Try increasing the timeout (default 15 s). |
| "No coupons found"                         | The response format may have changed. Check that widgets still use the `COUPON_CARD_WIDGET` type.            |
| Session seems stale or login keeps failing | Delete `zepto_session.json` and run the script again to log in fresh.                                        |

## Limitations

- Selectors and the API response structure are tied to Zepto's current website and may break without notice.
- Coupons shown depend on your account, location, and cart contents.

## Disclaimer

This project is unofficial and is not affiliated with or endorsed by Zepto. It is intended for personal use. Automating a website may be against its terms of service, so use it responsibly and at your own risk.