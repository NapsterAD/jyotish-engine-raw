"""
synthesis.py — Flatten every engine layer into JSON for LLM / report synthesis.
PDF is the human layout; this file is the raw-data contract.
"""

import json
from datetime import datetime


def _safe(obj, depth=0):
    """JSON-serialize engine dicts (drop JDs that are floats already)."""
    if depth > 8:
        return None
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).startswith("_") and k not in ("_jd", "_ayanamsha"):
                continue
            out[str(k)] = _safe(v, depth + 1)
        return out
    if isinstance(obj, (list, tuple)):
        return [_safe(x, depth + 1) for x in obj]
    if hasattr(obj, "isoformat"):
        try:
            return obj.isoformat()
        except Exception:
            return str(obj)
    return str(obj)


def build_synthesis_pack(chart):
    """
    One dict with every natal layer the engine can compute for this native.
    Safe to json.dump. Designed as the input to any synthesis / LLM pass.
    """
    now = datetime.now().strftime("%Y-%m-%d")
    current = {}
    try:
        current = chart.get_current_dasha(now) or {}
    except Exception as exc:
        current = {"error": str(exc)}

    def grab(label, fn):
        try:
            return fn()
        except Exception as exc:
            return {"error": f"{label}: {exc}"}

    pack = {
        "meta": {
            "generated": now,
            "purpose": "Raw natal data for synthesis. Not a prediction.",
            "ayanamsha": chart.birth_data.get("ayanamsha"),
            "ayanamsha_value": chart.positions.get("_ayanamsha"),
        },
        "birth": dict(chart.birth_data),
        "sunrise_sunset": _safe(chart.sunrise_sunset),
        "panchang": _safe(chart.panchang),
        "positions": _safe({
            k: v for k, v in chart.positions.items()
            if k in ["Lagna"] + list(chart.rashi_chart.keys()) or not str(k).startswith("_")
        }),
        "lordships": _safe(chart.lordships),
        "functional_nature": _safe(chart.functional_nature),
        "rashi": _safe(chart.rashi_chart),
        "chalit": _safe(chart.chalit_chart),
        "aspects": _safe(chart.aspects),
        "house_map_rashi": _safe(chart.get_house_map("rashi")),
        "house_map_chalit": _safe(chart.get_house_map("chalit")),
        "special_lagnas": _safe(chart.special_lagnas),
        "karakas_7": _safe(chart.karakas),
        "karakas_8": _safe(chart.karakas_8),
        "karakamsa": _safe(chart.karakamsa),
        "arudhas": _safe(chart.arudhas),
        "special_points": _safe(chart.special_points),
        "sahams": _safe(chart.sahams),
        "ashtakavarga": _safe({
            "sav": chart.ashtakavarga.get("sav"),
            "bav": chart.ashtakavarga.get("bav"),
            "row_totals": chart.ashtakavarga.get("row_totals"),
            "sodhya": {
                p: {k: v for k, v in block.items() if k != "reduced"}
                for p, block in (chart.ashtakavarga.get("sodhya") or {}).items()
                if isinstance(block, dict)
            },
        }),
        "shadbala": _safe(chart.shadbala),
        "ishta_kashta": _safe(chart.ishta_kashta),
        "avasthas_baladi": _safe(chart.avasthas),
        "jagradadi": grab("jagradadi", lambda: chart.jagradadi),
        "deeptadi": grab("deeptadi", lambda: chart.deeptadi),
        "bhava_bala": _safe(chart.bhava_bala),
        "yogas": _safe({
            "formed": chart.yogas.get("formed"),
            "not_formed": [
                y.get("name") for y in (chart.yogas.get("not_formed") or [])
                if isinstance(y, dict)
            ],
            "total_formed": chart.yogas.get("total_formed"),
            "total_checked": chart.yogas.get("total_checked"),
        }),
        "kp": _safe({
            "planets": chart.kp.get("planets"),
            "equal_cusps": chart.kp.get("equal_cusps"),
            "occupancy": chart.kp.get("occupancy"),
            "ruling_planets": chart.kp.get("ruling_planets") or chart.kp_ruling_planets(),
        }),
        "kp_significators": {
            str(h): _safe(chart.kp_significators(h)) for h in range(1, 13)
        },
        "vimshottari_md": _safe([
            {
                "lord": md.get("lord"),
                "start": md.get("start_date"),
                "end": md.get("end_date"),
                "years": md.get("duration_years"),
            }
            for md in chart.dashas
        ]),
        "current_vimshottari": _safe(current),
        "yogini_md": _safe([
            {
                "yogini": yd.get("yogini"),
                "planet": yd.get("planet"),
                "start": yd.get("start_date"),
                "end": yd.get("end_date"),
                "years": yd.get("years") or yd.get("balance_used"),
            }
            for yd in chart.yogini_dasha
            if yd.get("level") == "Major"
        ][:16]),
        "vargas": _safe({
            k: v for k, v in chart.vargas.items() if not str(k).startswith("_")
        }),
        "vargottama": _safe(chart.vargas.get("_vargottama")),
        "combustion": grab("combustion", lambda: chart.combustion),
        "yuddha": grab("yuddha", lambda: chart.yuddha),
        "badhaka": grab("badhaka", lambda: chart.badhaka),
        "jaimini_drishti": grab("jaimini_drishti", lambda: chart.jaimini_drishti),
        "sade_sati_today": grab("sade_sati", lambda: chart.sade_sati_for(now)),
        "pranapada": grab("pranapada", lambda: chart.pranapada),
        "pushkara": grab("pushkara", lambda: chart.pushkara),
        "nava_tara": grab("nava_tara", lambda: chart.nava_tara),
        "bhavat_bhavam": grab("bhavat_bhavam", lambda: chart.bhavat_bhavam),
        "ayurdaya": grab("ayurdaya", lambda: chart.ayurdaya),
        "grahan": grab("grahan", lambda: chart.grahan),
        "sensitive": grab("sensitive", lambda: {
            k: chart.sensitive.get(k)
            for k in ("navamsa_64", "drekkana_22")
        }),
        "nadi": grab("nadi", lambda: chart.nadi),
        "lal_kitab": grab("lal_kitab", lambda: chart.lal_kitab),
        "marriage_timing": grab("marriage_timing", lambda: chart.marriage_timing()),
        "kakshyas": grab("kakshyas", lambda: chart.kakshyas),
        "vimsopaka": grab("vimsopaka", lambda: chart.vimsopaka),
        "graha_arudhas": grab("graha_arudhas", lambda: chart.graha_arudhas),
        "current_vimshottari_5": grab(
            "vimshottari_5",
            lambda: chart.get_current_dasha(now, levels=5),
        ),
        "kakshya_timing_natal": grab(
            "kakshya_timing",
            lambda: {p: chart.kakshya_timing(p) for p in
                     ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]},
        ),
        "sav_by_house": grab(
            "sav_by_house",
            lambda: chart.ashtakavarga.get("by_house"),
        ),
    }

    # Trim dasha_systems to MD lists only (full AD trees are huge)
    try:
        ds = chart.dasha_systems
        pack["dasha_systems"] = {
            name: _safe({
                k: (v[:12] if k == "periods" and isinstance(v, list) else v)
                for k, v in (block.items() if isinstance(block, dict) else [])
            }) if isinstance(block, dict) else _safe(block[:12] if isinstance(block, list) else block)
            for name, block in ds.items()
            if name != "vimshottari"
        }
        pack["dasha_systems"]["vimshottari_current"] = _safe(current)
    except Exception as exc:
        pack["dasha_systems"] = {"error": str(exc)}

    # Named yoga stamps are hints, not facts. Keep them labeled as such.
    if "yogas" in pack:
        pack["derived_yoga_hints"] = pack.pop("yogas")

    return pack


def build_advanced_pack(chart, from_date=None):
    """
    Full raw-calculation sidecar for AI synthesis: KP chains, extra lagnas,
    dated calendars, dasha MD lists. No predictions.
    """
    base = build_synthesis_pack(chart)

    def grab(label, fn):
        try:
            return fn()
        except Exception as exc:
            return {"error": f"{label}: {exc}"}

    base["meta"]["purpose"] = (
        "Raw natal + dated calculation pack for AI synthesis. Not a prediction."
    )
    base["meta"]["contract"] = {
        "facts": "longitudes, houses, KP chains, calendars, strengths, vargas, dashas",
        "derived_yoga_hints": "named yoga stamps — re-verify from facts + school texts",
        "not_included": "remedies, event-window prose, confidence scores",
    }
    base["kp_advanced"] = grab("kp_advanced", lambda: chart.kp_advanced)
    base["extra_points"] = grab("extra_points", lambda: chart.extra_points)
    base["time_pack"] = grab("time_pack", lambda: chart.get_time_pack(from_date=from_date))
    base["raw_layers"] = grab("raw_layers", lambda: chart.raw_layers)
    # Full MD lists (not truncated) for the timing systems AI cross-checks
    try:
        ds = chart.dasha_systems
        keep = ("ashtottari", "narayana", "drigdasa", "chara", "yogini",
                "kalachakra", "sudasa", "lagna_kendradi")
        full = {}
        for name in keep:
            block = ds.get(name)
            if isinstance(block, dict):
                full[name] = _safe({
                    k: v for k, v in block.items()
                    if k != "periods" or True
                })
                periods = block.get("periods")
                if isinstance(periods, list):
                    full[name]["periods"] = _safe([
                        {kk: vv for kk, vv in p.items()
                         if kk not in ("start_jd", "end_jd", "sub_periods")}
                        if isinstance(p, dict) else p
                        for p in periods[:40]
                    ])
            elif isinstance(block, list):
                full[name] = _safe([
                    {kk: vv for kk, vv in p.items()
                     if kk not in ("start_jd", "end_jd", "sub_periods")}
                    if isinstance(p, dict) else p
                    for p in block[:40]
                ])
        base["dasha_md_full"] = full
    except Exception as exc:
        base["dasha_md_full"] = {"error": str(exc)}
    return base


def save_synthesis_json(chart, output_path):
    pack = build_synthesis_pack(chart)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2, default=str)
    return output_path


def save_advanced_json(chart, output_path, from_date=None):
    pack = build_advanced_pack(chart, from_date=from_date)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pack, f, ensure_ascii=False, indent=2, default=str)
    return output_path
