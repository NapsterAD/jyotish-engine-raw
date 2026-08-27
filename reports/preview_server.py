"""
preview_server.py — Lightweight interactive local web preview server for A4 reports.
Serves generated reports on localhost and opens the default browser with live controls.
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading
from typing import Optional

from ..main import JyotishEngine
from .generator import ReportGenerator


def start_preview_server(html_path: str, port: int = 8089, open_browser: bool = True):
    """
    Start a local static HTTP server to serve the report HTML and launch the browser.
    """
    directory = os.path.dirname(os.path.abspath(html_path))
    filename = os.path.basename(html_path)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def log_message(self, format, *args):
            # Suppress normal request noise
            pass

    server = socketserver.TCPServer(("", port), CustomHandler)
    url = f"http://localhost:{port}/{filename}"

    print(f"\n✨ Jyotish A4 Report Preview Server running at: {url}")
    print(f"👉 Press Ctrl+C in terminal to stop the server.\n")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping preview server...")
    finally:
        server.server_close()


def preview_chart(
    date: str,
    time: str,
    tz: str,
    lat: float,
    lon: float,
    name: str = "",
    port: int = 8089
):
    """Compute any natal, generate A4 HTML, and launch the preview server."""
    engine = JyotishEngine()
    chart = engine.compute(date=date, time=time, tz=tz, lat=lat, lon=lon, name=name)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    report_file = os.path.join(output_dir, f"{name.replace(' ', '_')}_A4_Report.html")

    chart.to_html_report(output_path=report_file)
    start_preview_server(report_file, port=port)


if __name__ == "__main__":
    print("Usage: preview_chart(date, time, tz, lat, lon, name=...)")
    print("Birth data is required — the engine has no default native.")
