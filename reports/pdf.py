"""
pdf.py — Design-faithful A4 PDF from the HTML report.

Uses Playwright/Chromium print, which renders the existing CSS (Cinzel, gold
theme, SVG kundalis, @page A4) the same way a browser Print → Save PDF would.
WeasyPrint is not used: it drops grid/flex/webfont details this stylesheet needs.
"""

import os


def html_to_pdf(html: str, output_path: str, timeout_ms: int = 60000) -> str:
    """
    Render a report HTML string to an A4 PDF.

    Print media is applied so the on-screen toolbar is hidden and each
    `.a4-page` becomes one sheet, matching templates/styles/report_a4.css.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "PDF export needs Playwright. Install with: pip install playwright "
            "; python -m playwright install chromium"
        ) from exc

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:
            raise RuntimeError(
                "Chromium is not installed for Playwright. Run: "
                "python -m playwright install chromium"
            ) from exc
        page = browser.new_page()
        page.set_content(html, wait_until="load", timeout=timeout_ms)
        page.evaluate("() => document.fonts && document.fonts.ready")
        page.emulate_media(media="print")
        page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
        )
        browser.close()

    return output_path
