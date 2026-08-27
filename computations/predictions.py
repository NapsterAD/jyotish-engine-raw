"""
predictions.py — Prediction Text Engine.

Wires the CSV prediction databases from data/kundli_predictions/ into the engine.
Returns applicable prediction paragraphs for any chart.

Databases:
  Phaladesh.csv         — Planet-in-Rashi predictions (146 rows, Eng+Hindi)
  Predictions.csv       — Sign-level + general predictions (441 rows)
  Predictions-Planetwise.csv — Planet-in-Rashi detailed (119 rows)
  Predictions-Rashiwise.csv  — Rashi personality descriptions
  Varshphal.csv         — Varshaphal year predictions (annual chart)
"""

import os
import csv
from typing import Dict, List, Any, Optional

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "kundli_predictions"
)

# ═══════════════════════════════════════════
# CSV LOADERS (lazy, cached)
# ═══════════════════════════════════════════

_cache: Dict[str, Any] = {}

# Planet number mapping used in the CSVs
_PLANET_NUM = {
    1: "Sun", 2: "Moon", 3: "Mercury", 4: "Venus",
    5: "Mars", 6: "Jupiter", 7: "Saturn",
    8: "Rahu", 9: "Ketu",
    10: "Lagna", 11: "Gulika", 12: "Ascendant",
}
_PLANET_TO_NUM = {v: k for k, v in _PLANET_NUM.items()}

# Rashi number mapping
_RASHI_NUM = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
}
_RASHI_TO_NUM = {v: k for k, v in _RASHI_NUM.items()}


def _safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _load_csv(filename):
    """Load a CSV file, return list of dicts."""
    path = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    rows = []
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            break
        except Exception:
            continue
    return rows


def _get_phaladesh():
    """Load and index Phaladesh.csv by (planet_num, div, rashi)."""
    if "phaladesh" not in _cache:
        rows = _load_csv("Phaladesh.csv")
        idx = {}
        for row in rows:
            p = _safe_int(row.get("PLNT"))
            d = _safe_int(row.get("DIV"))
            r = _safe_int(row.get("RASI"))
            idx[(p, d, r)] = {
                "english": row.get("Eng", "").strip(),
                "hindi": row.get("Hin", "").strip(),
                "id": row.get("ID", ""),
            }
        _cache["phaladesh"] = idx
    return _cache["phaladesh"]


def _get_planetwise():
    """Load Predictions-Planetwise.csv indexed by (planet_num, rashi_num)."""
    if "planetwise" not in _cache:
        rows = _load_csv("Predictions-Planetwise.csv")
        idx = {}
        for row in rows:
            p = _safe_int(row.get("Planet"))
            r = _safe_int(row.get("Rashi"))
            idx[(p, r)] = {
                "english": row.get("English", "").strip(),
                "hindi": row.get("Hindi", "").strip(),
            }
        _cache["planetwise"] = idx
    return _cache["planetwise"]


def _get_predictions():
    """Load Predictions.csv indexed by ID."""
    if "predictions" not in _cache:
        rows = _load_csv("Predictions.csv")
        idx = {}
        for row in rows:
            pid = row.get("ID", "").strip()
            if pid:
                idx[pid] = {
                    "english": row.get("English", "").strip(),
                    "hindi": row.get("Hindi", "").strip(),
                }
        _cache["predictions"] = idx
    return _cache["predictions"]


def _get_rashiwise():
    """Load Predictions-Rashiwise.csv."""
    if "rashiwise" not in _cache:
        rows = _load_csv("Predictions-Rashiwise.csv")
        idx = {}
        for row in rows:
            # Try different possible column names
            rashi = row.get("Rashi", row.get("RASI", row.get("Sign", "")))
            idx[rashi.strip()] = {
                "english": row.get("English", row.get("Eng", "")).strip(),
                "hindi": row.get("Hindi", row.get("Hin", "")).strip(),
            }
        _cache["rashiwise"] = idx
    return _cache["rashiwise"]


# ═══════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════

def get_planet_in_rashi_prediction(planet: str, rashi: str, lang: str = "english") -> str:
    """
    Get prediction text for a planet in a specific rashi.

    Args:
        planet: Planet name (e.g. "Jupiter")
        rashi: Sign name (e.g. "Aries")
        lang: "english" or "hindi"

    Returns:
        Prediction text string, or empty string if not found.
    """
    p_num = _PLANET_TO_NUM.get(planet, 0)
    r_num = _RASHI_TO_NUM.get(rashi, 0)

    # Try planetwise first (more detailed)
    pw = _get_planetwise()
    entry = pw.get((p_num, r_num))
    if entry and entry.get(lang):
        return entry[lang]

    # Fallback to phaladesh (DIV=1 for Rashi chart)
    ph = _get_phaladesh()
    entry = ph.get((p_num, 1, r_num))
    if entry and entry.get(lang):
        return entry[lang]

    return ""


def get_rashi_personality(rashi: str, lang: str = "english") -> str:
    """Get personality description for a rashi/ascendant sign."""
    rw = _get_rashiwise()
    entry = rw.get(rashi, {})
    return entry.get(lang, "")


def get_prediction_by_id(pred_id: str, lang: str = "english") -> str:
    """Get a specific prediction by its CSV ID code."""
    preds = _get_predictions()
    entry = preds.get(pred_id, {})
    return entry.get(lang, "")


def calc_predictions(chart, lang: str = "english") -> Dict[str, Any]:
    """
    Generate all applicable prediction texts for a birth chart.

    Returns:
        dict with sections: lagna_personality, planet_predictions, general_insights
    """
    results = {
        "lagna_personality": "",
        "planet_predictions": {},
        "rashi_description": "",
        "total_predictions": 0,
    }

    # Lagna sign personality
    lagna_sign = chart.positions.get("Lagna", {}).get("sign", "")
    if lagna_sign:
        results["lagna_personality"] = get_rashi_personality(lagna_sign, lang)
        results["rashi_description"] = lagna_sign

    # Planet in rashi predictions
    planet_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    count = 0
    for p in planet_names:
        pos = chart.positions.get(p, {})
        if not isinstance(pos, dict):
            continue
        sign = pos.get("sign", "")
        if not sign:
            continue
        text = get_planet_in_rashi_prediction(p, sign, lang)
        if text:
            house = chart.rashi_chart.get(p, {}).get("house_rashi", 0)
            results["planet_predictions"][p] = {
                "sign": sign,
                "house": house,
                "prediction": text,
            }
            count += 1

    results["total_predictions"] = count
    return results


def format_predictions(pred_data: Dict[str, Any], max_per_planet: int = 0) -> str:
    """Format prediction data as readable text for reports."""
    lines = []
    lines.append("=" * 60)
    lines.append("PREDICTION TEXT (from Classical Sources)")
    lines.append("=" * 60)

    if pred_data.get("lagna_personality"):
        lines.append(f"\n--- Lagna ({pred_data['rashi_description']}) Personality ---")
        lines.append(pred_data["lagna_personality"])

    pp = pred_data.get("planet_predictions", {})
    if pp:
        lines.append(f"\n--- Planet-in-Sign Predictions ({len(pp)} planets) ---")
        for planet, info in pp.items():
            lines.append(f"\n{planet} in {info['sign']} (House {info['house']}):")
            text = info["prediction"]
            if max_per_planet and len(text) > max_per_planet:
                text = text[:max_per_planet] + "..."
            lines.append(f"  {text}")

    lines.append(f"\nTotal predictions loaded: {pred_data.get('total_predictions', 0)}")
    return "\n".join(lines)
