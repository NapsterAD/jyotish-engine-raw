"""
test_report_generator.py — Unit and integration tests for the A4 Print Report Generator.
Verifies HTML structure, SVG embedding, data completeness, and file generation.
"""

import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.reports import ReportGenerator, generate_chart_report


def test_report_generation():
    print("Testing JyotishEngine A4 Print Report Generator...")
    engine = JyotishEngine()
    chart = engine.compute(
        date="2000-10-06",
        time="07:02:21",
        tz="+05:30",
        lat=23.797487,
        lon=86.305251,
        name="Aditya Prasad"
    )

    gen = ReportGenerator()
    html = gen.generate_html(chart, chart_style="north", theme="gold")

    assert "<!DOCTYPE html>" in html, "HTML doctype missing"
    assert "kundali-svg" in html, "SVG kundali chart missing"
    assert "Janma Kundali & Astro Identity" in html, "Page 1 missing"
    assert "Bhavas, Chalit, Arudhas & Special Points" in html, "Page 2 missing"
    assert "Ashtakavarga & Shadbala Strengths" in html, "Page 3 missing"
    assert "Vimshottari & Yogini Dasha Timelines" in html, "Page 4 missing"
    assert "Auspicious Yogas & Divisional Vargas" in html, "Page 5 missing"

    # Test file export
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    out_file = os.path.join(out_dir, "Aditya_Prasad_A4_Report.html")
    saved_path = chart.to_html_report(out_file)

    assert os.path.exists(saved_path), f"Saved file not found: {saved_path}"
    file_size = os.path.getsize(saved_path)
    assert file_size > 10000, f"File size too small: {file_size} bytes"

    # Test South Indian chart option
    html_south = gen.generate_html(chart, chart_style="south", theme="gold")
    assert "south-indian" in html_south, "South Indian chart class missing"

    print(f"✅ All Report Generator Tests PASSED!")
    print(f"   Generated Report: {saved_path} ({file_size / 1024:.1f} KB)")


if __name__ == "__main__":
    test_report_generation()
