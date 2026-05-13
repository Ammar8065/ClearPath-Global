"""Render the assessment HTML report to a PDF byte string using Playwright."""
from __future__ import annotations

from playwright.sync_api import sync_playwright


def render_pdf(html: str) -> bytes:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                prefer_css_page_size=True,
            )
        finally:
            browser.close()
    return pdf
