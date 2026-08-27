from pathlib import Path

html = Path("output/Aditya_Prasad_A4_Report.html").read_text(encoding="utf-8")
pdf = Path("output/Aditya_Prasad_A4_Report.pdf")
print("html a4-page", html.count('class="a4-page'))
print("landscape leftover", "landscape-sheet" in html or 'a4-page landscape' in html)
print("has D24", "D24" in html, "has D60", ">D60<" in html or "D60" in html)
print("sssl_lord wiring", "sssl_lord" in html or "SSSL" in html)

try:
    from pypdf import PdfReader
    r = PdfReader(str(pdf))
    print("pdf pages", len(r.pages), "bytes", pdf.stat().st_size)
    box = r.pages[0].mediabox
    print("page0 box", float(box.width), "x", float(box.height))
    wides = 0
    for i, pg in enumerate(r.pages):
        b = pg.mediabox
        if float(b.width) > float(b.height):
            wides += 1
            print("landscape page", i + 1)
    print("landscape count", wides)
except Exception as exc:
    print("pypdf failed", exc)
