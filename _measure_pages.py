"""Measure each .a4-page height vs A4 1123px."""
from pathlib import Path
from playwright.sync_api import sync_playwright

html = Path("output/Aditya_Prasad_A4_Report.html").read_text(encoding="utf-8")
limit = 1123  # A4 297mm at 96dpi
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    page = browser.new_page()
    page.set_content(html, wait_until="load")
    page.emulate_media(media="print")
    rows = page.evaluate(
        """() => Array.from(document.querySelectorAll('.a4-page')).map((el, i) => ({
            i: i+1, id: el.id, h: Math.round(el.scrollHeight),
            over: el.scrollHeight > 1123
        }))"""
    )
    for r in rows:
        mark = " OVER" if r["over"] else ""
        print(f"{r['i']:2d} {r['id'] or '?':12s} {r['h']:4d}px{mark}")
    print("over count", sum(1 for r in rows if r["over"]))
    grid = page.evaluate(
        """() => {
          const el = document.querySelector('#page13 .four-col-grid, #page13 .three-col-grid');
          if (!el) return {found: false};
          const cs = getComputedStyle(el);
          return {
            found: true,
            cls: el.className,
            grid: cs.gridTemplateColumns,
            w: el.clientWidth,
            kids: el.children.length,
            h: Math.round(el.scrollHeight)
          };
        }"""
    )
    print("page13 grid", grid)
    browser.close()
