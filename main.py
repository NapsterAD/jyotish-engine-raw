"""
main.py — Single entry point for JyotishEngine.

Any civil birth data computes a full chart. Formulas live in rules.md;
nothing is hard-wired to one native.

    from jyotish_engine.main import JyotishEngine
    engine = JyotishEngine()
    chart = engine.compute(date, time, tz, lat, lon, name="")
    # chart.panchang, chart.combustion, chart.yuddha, chart.badhaka
    # chart.jaimini_drishti, chart.kp, chart.sade_sati_for(date)
"""

import os
from .core.chart import BirthChart


class JyotishEngine:
    """
    Top-level interface for the Jyotish calculation engine.
    100% offline — no internet required.
    """

    def __init__(self, ephe_path=None, ayanamsha="lahiri"):
        """
        Initialize the engine.
        
        Args:
            ephe_path: Path to Swiss Ephemeris .se1 data files.
                       If None, checks default locations then falls back to Moshier.
            ayanamsha: "lahiri" (default), "raman", "krishnamurti", etc.
        """
        # Try to find ephemeris files if path not specified
        if ephe_path is None:
            candidates = [
                os.path.join(os.path.dirname(__file__), "data", "ephe"),
                os.path.join(os.path.expanduser("~"), "sweph", "ephe"),
                r"C:\sweph\ephe",
            ]
            for candidate in candidates:
                if os.path.isdir(candidate):
                    ephe_path = candidate
                    break

        self._ephe_path = ephe_path
        self._ayanamsha = ayanamsha

    def compute(self, date, time, tz, lat, lon, name=""):
        """
        Compute a complete birth chart.
        
        Args:
            date: "YYYY-MM-DD"
            time: "HH:MM:SS"
            tz: "+05:30" or timezone string
            lat: latitude (float)
            lon: longitude (float)
            name: person's name (optional, for reports)
            
        Returns:
            BirthChart object with all computed data
        """
        chart = BirthChart(
            date=date, time=time, tz=tz,
            lat=lat, lon=lon, name=name,
            ayanamsha=self._ayanamsha,
            ephe_path=self._ephe_path
        )
        return chart

    def generate_report(self, chart_or_data, output_path=None, chart_style="north", theme="gold"):
        """
        Generate a 5-page A4 report. HTML by default; PDF if output_path ends with .pdf
        (Chromium print — keeps the gold A4 design, SVG kundalis, and webfonts).
        Accepts either a BirthChart object or a dict with birth details.
        """
        if isinstance(chart_or_data, BirthChart):
            chart = chart_or_data
        elif isinstance(chart_or_data, dict):
            chart = self.compute(
                date=chart_or_data["date"],
                time=chart_or_data["time"],
                tz=chart_or_data["tz"],
                lat=chart_or_data["lat"],
                lon=chart_or_data["lon"],
                name=chart_or_data.get("name", "")
            )
        else:
            raise ValueError("chart_or_data must be a BirthChart or dict of birth parameters")

        return chart.to_html_report(output_path=output_path, chart_style=chart_style, theme=theme)


# ═══════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Jyotish engine: compute a natal from civil birth data (rules.md formulas)."
    )
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--time", required=True, help="HH:MM:SS")
    parser.add_argument("--tz", required=True, help="e.g. +05:30")
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--name", default="")
    args = parser.parse_args()
    engine = JyotishEngine()
    chart = engine.compute(
        date=args.date, time=args.time, tz=args.tz,
        lat=args.lat, lon=args.lon, name=args.name,
    )
    print(chart.summary())
