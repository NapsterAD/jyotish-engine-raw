"""
panchang.py — Five limbs of the Panchang from any natal (or query) longitudes.
Tithi, Karana, Nithya Yoga, Vara, Nakshatra, plus Hora lord.
Formulas: rules.md §14. Chart-agnostic.
"""

from datetime import datetime, timedelta

from ..core.constants import NAKSHATRAS, NAKSHATRA_SPAN

TITHI_SHUKLA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
]
TITHI_KRISHNA = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]
TITHI_GROUP = ["Nanda", "Bhadra", "Jaya", "Rikta", "Purna"]
TITHI_GROUP_LORD = {
    "Nanda": "Venus", "Bhadra": "Mercury", "Jaya": "Mars",
    "Rikta": "Saturn", "Purna": "Jupiter",
}

KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti"]
KARANA_FIXED = {1: "Kimstughna", 58: "Shakuni", 59: "Chatushpada", 60: "Naga"}

NITHYA_YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

DAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
VARA_CHALDEAN_INDEX = {
    "Sun": 3, "Moon": 6, "Mars": 2, "Mercury": 5,
    "Jupiter": 1, "Venus": 4, "Saturn": 0,
}


def _elongation(moon_long, sun_long):
    return (moon_long - sun_long) % 360.0


def calc_tithi(moon_long, sun_long):
    """Tithi 1-30 from Moon-Sun elongation. rules.md §14.1."""
    elong = _elongation(moon_long, sun_long)
    num = int(elong / 12.0) + 1
    if num > 30:
        num = 30
    if num < 1:
        num = 1
    if num <= 15:
        paksha = "Shukla"
        name = TITHI_SHUKLA[num - 1]
        paksha_num = num
    else:
        paksha = "Krishna"
        name = TITHI_KRISHNA[num - 16]
        paksha_num = num - 15
    group = TITHI_GROUP[(paksha_num - 1) % 5]
    return {
        "number": num,
        "paksha": paksha,
        "name": name,
        "full_name": f"{paksha} {name}",
        "group": group,
        "lord": TITHI_GROUP_LORD[group],
        "elapsed_pct": round((elong % 12.0) / 12.0 * 100.0, 4),
        "elongation": round(elong, 6),
    }


def calc_karana(moon_long, sun_long):
    """Karana 1-60 (half tithi). rules.md §14.2."""
    elong = _elongation(moon_long, sun_long)
    num = int(elong / 6.0) + 1
    if num > 60:
        num = 60
    if num < 1:
        num = 1
    if num in KARANA_FIXED:
        name = KARANA_FIXED[num]
    else:
        name = KARANA_MOVABLE[(num - 2) % 7]
    return {
        "number": num,
        "name": name,
        "elapsed_pct": round((elong % 6.0) / 6.0 * 100.0, 4),
    }


def calc_nithya_yoga(moon_long, sun_long):
    """Nithya yoga 1-27 from Moon+Sun. rules.md §14.3."""
    total = (moon_long + sun_long) % 360.0
    num = int(total / NAKSHATRA_SPAN) + 1
    if num > 27:
        num = 27
    if num < 1:
        num = 1
    return {
        "number": num,
        "name": NITHYA_YOGAS[num - 1],
        "elapsed_pct": round((total % NAKSHATRA_SPAN) / NAKSHATRA_SPAN * 100.0, 4),
    }


def calc_vara(date_str, birth_jd=None, sunrise_jd=None):
    """
    Weekday lord. If birth is before local sunrise, use the previous civil day
    (astrological Vara runs sunrise-to-sunrise). rules.md §14.4.
    """
    use_date = date_str
    if birth_jd is not None and sunrise_jd is not None and birth_jd < sunrise_jd:
        dt = datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)
        use_date = dt.strftime("%Y-%m-%d")
    dt = datetime.strptime(use_date, "%Y-%m-%d")
    sunday0 = (dt.weekday() + 1) % 7
    lord = DAY_LORDS[sunday0]
    names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return {
        "weekday": names[sunday0],
        "lord": lord,
        "index": sunday0,
        "vara_date": use_date,
    }


def calc_nakshatra_panchang(moon_long):
    """Moon nakshatra limb. rules.md §14.5."""
    longitude = moon_long % 360.0
    idx = min(int(longitude / NAKSHATRA_SPAN), 26)
    nak = NAKSHATRAS[idx]
    degree_in = longitude - idx * NAKSHATRA_SPAN
    return {
        "number": nak["num"],
        "name": nak["name"],
        "lord": nak["lord"],
        "elapsed_pct": round(degree_in / NAKSHATRA_SPAN * 100.0, 4),
    }


def calc_hora(chart):
    """
    Planetary hour at birth from local sunrise/sunset. rules.md §14.6.
    12 day horas sunrise→sunset, 12 night horas sunset→next sunrise.
    If birth is before sunrise, night horas are measured from previous sunset
    and Vara is the previous weekday.
    """
    ss = chart.sunrise_sunset or {}
    rise_jd = ss.get("sunrise_jd")
    set_jd = ss.get("sunset_jd")
    birth_jd = chart.positions.get("_jd")
    if not rise_jd or not set_jd or not birth_jd:
        return {"hora_index": None, "hora_lord": None}

    date = datetime.strptime(chart.birth_data["date"], "%Y-%m-%d")
    next_date = (date + timedelta(days=1)).strftime("%Y-%m-%d")
    prev_date = (date - timedelta(days=1)).strftime("%Y-%m-%d")
    lat = chart.birth_data["lat"]
    lon = chart.birth_data["lon"]
    tz = chart.birth_data["tz"]
    ephe = chart._ephe

    next_ss = ephe.get_sunrise_sunset(next_date, lat, lon, tz)
    next_rise = next_ss["sunrise_jd"]

    if birth_jd < rise_jd:
        prev_ss = ephe.get_sunrise_sunset(prev_date, lat, lon, tz)
        prev_set = prev_ss["sunset_jd"]
        night_dur = (rise_jd - prev_set) / 12.0
        if night_dur <= 0:
            night_dur = 1.0 / 24.0
        k = 12 + int((birth_jd - prev_set) / night_dur)
        k = min(max(k, 12), 23)
        is_day = False
        vara_date = prev_date
        hora_duration_hours = night_dur * 24.0
    elif birth_jd < set_jd:
        day_dur = (set_jd - rise_jd) / 12.0
        if day_dur <= 0:
            day_dur = 1.0 / 24.0
        k = int((birth_jd - rise_jd) / day_dur)
        k = min(max(k, 0), 11)
        is_day = True
        vara_date = chart.birth_data["date"]
        hora_duration_hours = day_dur * 24.0
    else:
        night_dur = (next_rise - set_jd) / 12.0
        if night_dur <= 0:
            night_dur = 1.0 / 24.0
        k = 12 + int((birth_jd - set_jd) / night_dur)
        k = min(max(k, 12), 23)
        is_day = False
        vara_date = chart.birth_data["date"]
        hora_duration_hours = night_dur * 24.0

    vara = calc_vara(vara_date)
    base = VARA_CHALDEAN_INDEX[vara["lord"]]
    hora_lord = CHALDEAN[(base + k) % 7]
    return {
        "hora_index": k,
        "hora_lord": hora_lord,
        "is_day_hora": is_day,
        "vara": vara,
        "duration_hours": round(hora_duration_hours, 4),
    }


def calc_panchang(chart):
    """Full panchang bundle for this native's birth moment."""
    sun = chart.positions.get("Sun", {}).get("longitude", 0.0)
    moon = chart.positions.get("Moon", {}).get("longitude", 0.0)
    ss = chart.sunrise_sunset or {}
    tithi = calc_tithi(moon, sun)
    karana = calc_karana(moon, sun)
    yoga = calc_nithya_yoga(moon, sun)
    vara = calc_vara(
        chart.birth_data["date"],
        birth_jd=chart.positions.get("_jd"),
        sunrise_jd=ss.get("sunrise_jd"),
    )
    nak = calc_nakshatra_panchang(moon)
    hora = calc_hora(chart)
    return {
        "tithi": tithi,
        "karana": karana,
        "yoga": yoga,
        "vara": vara,
        "nakshatra": nak,
        "hora": hora,
    }
