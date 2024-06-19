import os
import json
import urllib
import subprocess
from playwright.sync_api import sync_playwright, expect
from percy import percy_screenshot

USER_NAME = os.environ.get("BROWSERSTACK_USERNAME", "BROWSERSTACK_USERNAME")
ACCESS_KEY = os.environ.get("BROWSERSTACK_ACCESS_KEY", "BROWSERSTACK_ACCESS_KEY")


def test_session(capability):
    with sync_playwright() as p:
        # Setup the browser context with BrowserStack capabilities
        clientPlaywrightVersion = (
            str(subprocess.getoutput("playwright --version")).strip().split(" ")[1]
        )
        capability["client.playwrightVersion"] = clientPlaywrightVersion
        cdpUrl = "wss://cdp.browserstack.com/playwright?caps=" + urllib.parse.quote(
            json.dumps(capability)
        )
        browser = p.chromium.connect(cdpUrl)
        context = browser.new_context(viewport={"width": 1280, "height": 1024})

        # Start a new page
        page = context.new_page()

        try:
            # Navigate to the required website
            page.goto("https://bstackdemo.com/")
            expected_title_substring = "StackDemo"
            expect(page).to_have_title(expected_title_substring, timeout=30000)

            # Click on the Apple products
            page.click('//*[@id="__next"]/div/div/main/div[1]/div[1]/label/span')

            # Percy Screenshot 1
            percy_screenshot(page, name="screenshot_1")

            # Get text of current product
            item_on_page = page.text_content('//*[@id="1"]/p')

            # Click on 'Add to cart' button
            page.click('//*[@id="1"]/div[4]')

            # Check if the Cart pane is visible
            page.wait_for_selector(".float-cart__content")

            # Get text of product in cart
            item_in_cart = page.text_content(
                '//*[@id="__next"]/div/div/div[2]/div[2]/div[2]/div/div[3]/p[1]'
            )

            # Percy Screenshot 2
            # Options - Showcasing some of options supported by percy
            # {
            #   test_case: "<test case name>",
            #   full_page: True
            # }
            percy_screenshot(
                page,
                name="screenshot_2",
                options={
                    "test_case": "Product should be added in the cart",
                    "full_page": True,
                },
            )

            if item_on_page == item_in_cart:
                status = "passed"
                reason = "iPhone 12 has been successfully added to the cart!"
            else:
                status = "failed"
                reason = "iPhone 12 not added to the cart!"
            mark_test_status(status, reason, page)
        except Exception as e:
            message = f"Error occurred while executing script: {str(e.__class__.__name__)} {str(e)}"
            print(message)
            mark_test_status("failed", message, page)
        finally:
            browser.close()


def mark_test_status(status, reason, page):
    page.evaluate(
        "_ => {}",
        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"'
        + status
        + '", "reason": "'
        + reason
        + '"}}',
    )


if __name__ == "__main__":
    chrome_on_ventura = {
        "browser": "chrome",
        "browser_version": "latest",
        "os": "osx",
        "os_version": "ventura",
        "name": "Percy Playwright Example",
        "build": "percy-playwright-python-example",
        "browserstack.user": USER_NAME,
        "browserstack.key": ACCESS_KEY,
    }

    capabilities_list = [chrome_on_ventura]
    for capability in capabilities_list:
        test_session(capability)
