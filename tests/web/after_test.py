import os
import json
import urllib
import subprocess
from playwright.sync_api import sync_playwright, expect
from percy import percy_snapshot


def test_session():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 1024})

        # Start a new page
        page = context.new_page()

        try:
            # Navigate to the required website
            page.goto("https://bstackdemo.com/")
            expected_title_substring = "StackDemo"
            expect(page).to_have_title(expected_title_substring, timeout=30000)

            # Click on the Samsung products
            page.click('//*[@id="__next"]/div/div/main/div[1]/div[2]/label/span')

            # Percy Snapshot 1
            percy_snapshot(page, name="snapshot_1")

            # Get text of current product
            item_on_page = page.text_content('//*[@id="10"]/p')

            # Click on 'Add to cart' button
            page.click('//*[@id="10"]/div[4]')

            # Check if the Cart pane is visible
            page.wait_for_selector(".float-cart__content")

            # Get text of product in cart
            item_in_cart = page.text_content(
                '//*[@id="__next"]/div/div/div[2]/div[2]/div[2]/div/div[3]/p[1]'
            )

            # Percy Snapshot 2
            percy_snapshot(
                page,
                name="snapshot_2",
                test_case="Product should be added in the cart",
            )

            if item_on_page == item_in_cart:
                status = "passed"
                reason = "Galaxy S20 has been successfully added to the cart!"
            else:
                status = "failed"
                reason = "Galaxy S20 not added to the cart!"
            mark_test_status(status, reason, page)
        except Exception as e:
            message = f"Error occurred while executing script: {str(e.__class__.__name__)} {str(e)}"
            print(message)
            mark_test_status("failed", message, page)
        finally:
            browser.close()


def mark_test_status(status, reason, page):
    print(f"Test Status: {status}, Reason: {reason}")


if __name__ == "__main__":
    test_session()
