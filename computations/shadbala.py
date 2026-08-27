"""
shadbala.py — Six-fold planetary strength (Shadbala), Ishta-Kashta Phala,
Avasthas, Vimsopaka, and Bhava Bala.
100% offline — classical Parashara formulas.

Shadbala components:
1. Sthana Bala (Positional Strength)
2. Dig Bala (Directional Strength)
3. Kala Bala (Temporal Strength)
4. Cheshta Bala (Motional Strength)
5. Naisargika Bala (Natural Strength)
6. Drik Bala (Aspectual Strength)
"""

import math
from datetime import datetime, timedelta

import swisseph as swe

from ..core.constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_ELEMENT, SIGN_MODALITY,
    EXALTATION, DEBILITATION, MOOLATRIKONA, OWN_SIGNS,
    NATURAL_FRIENDS, NATURAL_ENEMIES, SPECIAL_ASPECTS,
    PLANETS_7, PLANETS_9,
)


# ═══════════════════════════════════════════
# MINIMUM REQUIRED SHADBALA (in Rupas)
# ═══════════════════════════════════════════

MINIMUM_SHADBALA = {
    "Sun": 6.5,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}


# ═══════════════════════════════════════════
# NAISARGIKA BALA (Natural/Inherent Strength)
# ═══════════════════════════════════════════
# Fixed values per Parashara (in Shashtiamsas = 1/60 of Rupa)

NAISARGIKA_BALA = {
    "Sun": 60,
    "Moon": 51.43,
    "Mars": 17.14,
    "Mercury": 25.71,
    "Jupiter": 34.29,
    "Venus": 42.86,
    "Saturn": 8.57,
}


# ═══════════════════════════════════════════
# DIG BALA (Directional Strength)
# ═══════════════════════════════════════════
# Maximum when in the house that gives full dig bala, zero at opposite

DIG_BALA_HOUSES = {
    # planet: house giving maximum dig bala (1-indexed from lagna)
    "Sun": 10,     # 10H (MC/Zenith)
    "Moon": 4,     # 4H (IC/Nadir)
    "Mars": 10,    # 10H
    "Mercury": 1,  # 1H (ASC)
    "Jupiter": 1,  # 1H
    "Venus": 4,    # 4H
    "Saturn": 7,   # 7H (DSC)
}


def _shortest_arc(lam_a, lam_b):
    """Shortest angular distance in degrees, 0–180."""
    d = abs((lam_a - lam_b) % 360.0)
    if d > 180.0:
        d = 360.0 - d
    return d


def calc_dig_bala(planet, house_num, longitude=None, peak_longitude=None):
    """
    Dig Bala. Max 60 at the planet's directional peak, 0 at the opposite.
    Prefer longitudes (rules.md §6.1): Dig = Δλ_from_zero / 3.
    Falls back to whole-sign house distance when cusps are unavailable.
    """
    if planet not in DIG_BALA_HOUSES:
        return 0.0

    if longitude is not None and peak_longitude is not None:
        zero = (peak_longitude + 180.0) % 360.0
        return max(0.0, min(60.0, _shortest_arc(longitude, zero) / 3.0))

    best_house = DIG_BALA_HOUSES[planet]
    distance = abs(house_num - best_house)
    if distance > 6:
        distance = 12 - distance
    return max(0.0, 60.0 * (1.0 - distance / 6.0))


# ═══════════════════════════════════════════
# STHANA BALA (Positional Strength)
# ═══════════════════════════════════════════

def _uchcha_bala(planet, longitude):
    """
    Uchcha Bala from the deep-debilitation point (BPHS / rules.md §6.1).
    Δλ = shortest arc |λ_P − λ_deb|; Uchcha = Δλ / 3  (0–60 shashtiamsas).
    Zero at debilitation, 60 at the opposite exaltation degree.
    """
    if planet not in DEBILITATION:
        return 30.0

    deb_sign, deb_deg = DEBILITATION[planet]
    deb_long = SIGN_INDEX[deb_sign] * 30 + deb_deg
    delta = _shortest_arc(longitude, deb_long)
    return max(0.0, min(60.0, delta / 3.0))


def get_temporal_friendship(positions):
    """
    Temporal friendship from D1/Rasi positions (BPHS / JHora):
    Planets in houses 2, 3, 4, 10, 11, 12 from planet P (sign difference 1, 2, 3, 9, 10, 11)
    are temporal friends (Tatkalika Mitra); in 1, 5, 6, 7, 8, 9 are temporal enemies.
    """
    temp_friends = {p: set() for p in PLANETS_7}
    p_signs = {}
    if isinstance(positions, dict):
        for p in PLANETS_7:
            pos = positions.get(p, {})
            if isinstance(pos, dict) and "sign_index" in pos:
                p_signs[p] = pos["sign_index"]
            elif isinstance(pos, dict) and "sign" in pos and pos["sign"] in SIGN_INDEX:
                p_signs[p] = SIGN_INDEX[pos["sign"]]

    for p1 in PLANETS_7:
        if p1 not in p_signs:
            continue
        s1 = p_signs[p1]
        for p2 in PLANETS_7:
            if p2 == p1 or p2 not in p_signs:
                continue
            s2 = p_signs[p2]
            diff = (s2 - s1) % 12
            if diff in (1, 2, 3, 9, 10, 11):
                temp_friends[p1].add(p2)
    return temp_friends


def _varga_kshetra_score(planet, varga_sign, degree_in_sign=None, is_d1=False, temp_friends=None):
    """One varga's Saptavargaja points with Panchadha Maitri (BPHS: MT 45, own 30, adhi mitra 22.5, mitra 15, sama 7.5, shatru 3.75, adhi shatru 1.875)."""
    if is_d1 and degree_in_sign is not None and planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if varga_sign == mt_sign and mt_start <= degree_in_sign < mt_end:
            return 45.0
    if planet in OWN_SIGNS and varga_sign in OWN_SIGNS[planet]:
        return 30.0
    if planet in EXALTATION and EXALTATION[planet][0] == varga_sign:
        return 30.0
    lord = SIGN_LORDS.get(varga_sign, "")
    if planet == lord:
        return 30.0

    # Natural relationship
    if planet in NATURAL_FRIENDS and lord in NATURAL_FRIENDS[planet]:
        nat = 1
    elif planet in NATURAL_ENEMIES and lord in NATURAL_ENEMIES[planet]:
        nat = -1
    else:
        nat = 0

    # Compound relationship with Temporal friendship
    if temp_friends is not None and planet in temp_friends:
        is_temp = lord in temp_friends[planet]
        composite = nat + (1 if is_temp else -1)
        if composite >= 2:
            return 22.5
        elif composite == 1:
            return 15.0
        elif composite == 0:
            return 7.5
        elif composite == -1:
            return 3.75
        else:
            return 1.875
    else:
        if nat == 1:
            return 15.0
        elif nat == -1:
            return 3.75
        return 7.5


def _saptavargaja_bala(planet, sign, degree_in_sign, longitude=None, temp_friends=None):
    """
    Saptavargaja: D1 + D2 + D3 + D7 + D9 + D12 + D30 with Panchadha Maitri.
    """
    from .vargas import (
        calc_d1, calc_d2_hora, calc_d3_drekkana, calc_d7,
        calc_d12, calc_d30,
    )
    from ..core.constants import get_navamsa_sign

    if longitude is None:
        longitude = SIGN_INDEX.get(sign, 0) * 30 + (degree_in_sign or 0)

    varga_signs = [
        (calc_d1(longitude), True),
        (calc_d2_hora(longitude), False),
        (calc_d3_drekkana(longitude), False),
        (calc_d7(longitude), False),
        (get_navamsa_sign(longitude), False),
        (calc_d12(longitude), False),
        (calc_d30(longitude), False),
    ]
    total = 0.0
    for vs, is_d1 in varga_signs:
        total += _varga_kshetra_score(
            planet, vs, degree_in_sign if is_d1 else None, is_d1,
            temp_friends=temp_friends,
        )
    return total


def _ojha_yugma_bala(planet, sign_idx):
    """
    Ojha-Yugma Bala (Odd-Even sign strength).
    Sun, Mars, Jupiter, Mercury, Saturn get strength in odd signs.
    Moon, Venus get strength in even signs.
    """
    is_odd = (sign_idx % 2 == 0)  # 0-indexed: Aries=0=odd

    odd_strong = ["Sun", "Mars", "Jupiter", "Mercury", "Saturn"]
    even_strong = ["Moon", "Venus"]

    if planet in odd_strong:
        return 15 if is_odd else 0
    elif planet in even_strong:
        return 15 if not is_odd else 0
    return 0


def _kendra_bala(house_num):
    """
    Kendra strength: Kendra houses (1,4,7,10) = 60,
    Panaphara (2,5,8,11) = 30, Apoklima (3,6,9,12) = 15.
    """
    if house_num in [1, 4, 7, 10]:
        return 60
    elif house_num in [2, 5, 8, 11]:
        return 30
    else:
        return 15


def _drekkana_bala(planet, degree_in_sign):
    """
    Drekkana strength based on which third of the sign.
    Male planets (Sun, Mars, Jupiter) strong in 1st drekkana.
    Neutral (Mercury, Saturn) in 2nd drekkana.
    Female (Moon, Venus) in 3rd drekkana.
    """
    if degree_in_sign < 10:
        drekkana = 1
    elif degree_in_sign < 20:
        drekkana = 2
    else:
        drekkana = 3

    male = ["Sun", "Mars", "Jupiter"]
    neutral = ["Mercury", "Saturn"]
    female = ["Moon", "Venus"]

    if planet in male and drekkana == 1:
        return 15
    elif planet in neutral and drekkana == 2:
        return 15
    elif planet in female and drekkana == 3:
        return 15
    return 0


def calc_sthana_bala(planet, longitude, sign, degree_in_sign, house_num, temp_friends=None):
    """
    Calculate total Sthana Bala (positional strength).
    Sum of: Uchcha + Saptavargaja + Ojha-Yugma + Kendra + Drekkana
    """
    sign_idx = SIGN_INDEX[sign]

    uchcha = _uchcha_bala(planet, longitude)
    saptavargaja = _saptavargaja_bala(planet, sign, degree_in_sign, longitude, temp_friends=temp_friends)
    ojha_yugma = _ojha_yugma_bala(planet, sign_idx)
    kendra = _kendra_bala(house_num)
    drekkana = _drekkana_bala(planet, degree_in_sign)

    return {
        "total": uchcha + saptavargaja + ojha_yugma + kendra + drekkana,
        "uchcha": round(uchcha, 2),
        "saptavargaja": round(saptavargaja, 2),
        "ojha_yugma": round(ojha_yugma, 2),
        "kendra": round(kendra, 2),
        "drekkana": round(drekkana, 2),
    }


# ═══════════════════════════════════════════
# CHESHTA BALA (Motional Strength)
# ═══════════════════════════════════════════
# BPHS Chesta Kendra: mean longitudes from the 1900 Ujjain epoch used by
# JHora / PyJHora (Surya-Siddhanta mean motion). Not Swiss true speed.
# Retrograde is NOT forced to 60 — outer vakri grahas already sit near
# opposition so Seeghra Kendra is large.

_CHESHTA_EPOCH_JD = None  # lazy swe.julday(1900, 1, 1, 0)
_CHESHTA_UJJAIN_LON = 76.0
_MEAN_LON_EPOCH = {
    "Sun": 257.4568, "Mars": 270.22, "Mercury": 164.0,
    "Jupiter": 220.04, "Venus": 328.51, "Saturn": 236.74,
}
_MEAN_LON_SPEED = {
    "Sun": 0.9856, "Mars": 0.524, "Mercury": 4.0923,
    "Jupiter": 0.0831, "Venus": 1.60215, "Saturn": 0.033439,
}
# correction = sign * (a + b * years_since_1900)
_MEAN_LON_CORR = {
    "Sun": (1, 0.0, 0.0), "Mars": (1, 0.0, 0.0),
    "Mercury": (1, 6.67, -0.00133), "Jupiter": (-1, 3.3, 0.0067),
    "Venus": (-1, 5.0, 0.0001), "Saturn": (1, 5.0, 0.001),
}


def _cheshta_epoch_jd():
    global _CHESHTA_EPOCH_JD
    if _CHESHTA_EPOCH_JD is None:
        _CHESHTA_EPOCH_JD = swe.julday(1900, 1, 1, 0.0)
    return _CHESHTA_EPOCH_JD


def _mean_sidereal_lon(planet, jd, lon):
    """Sidereal mean longitude (deg) at jd for Chesta Kendra. rules.md §6.1."""
    days = (jd - _cheshta_epoch_jd()
            + (_CHESHTA_UJJAIN_LON - float(lon or 0.0)) / 15.0 / 24.0)
    year = int(swe.revjul(jd)[0])
    sign, a, b = _MEAN_LON_CORR[planet]
    corr = sign * (a + b * (year - 1900))
    return (_MEAN_LON_EPOCH[planet] + days * _MEAN_LON_SPEED[planet] + corr) % 360.0


def calc_cheshta_bala(planet, true_lon, jd, lon):
    """
    BPHS Chesta Bala for Mars–Saturn: Seeghra Kendra / 3 (0–60).

    Outer (Mars, Jupiter, Saturn): Seeghrochcha = mean Sun;
      ave = (true + mean_planet) / 2.
    Inner (Mercury, Venus): Seeghrochcha = planet mean;
      ave = (true + mean Sun) / 2.
    Kendra is the 0–180 shortest arc; Chesta = kendra / 3.
    Sun/Moon are handled by the caller (Ayana / Paksha).
    """
    if planet not in _MEAN_LON_EPOCH or planet == "Sun" or not jd:
        return 0.0
    sun_mean = _mean_sidereal_lon("Sun", jd, lon)
    mean = _mean_sidereal_lon(planet, jd, lon)
    if planet in ("Mercury", "Venus"):
        seeghrochcha = mean
        ave = 0.5 * (true_lon + sun_mean)
    else:
        seeghrochcha = sun_mean
        ave = 0.5 * (true_lon + mean)
    kendra = _shortest_arc(seeghrochcha, ave)
    return max(0.0, min(60.0, kendra / 3.0))


# ═══════════════════════════════════════════
# KALA BALA (Temporal Strength)
# ═══════════════════════════════════════════

_AYANA_NORTH = {"Sun", "Mars", "Jupiter", "Venus"}
_AYANA_SOUTH = {"Moon", "Saturn"}
_AYANA_MAX_DECL = 24.0  # BPHS kranti constant


def _obliquity(jd):
    """True ecliptic obliquity in degrees (fallback J2000)."""
    try:
        nut, _ = swe.calc_ut(jd, swe.ECL_NUT)
        return float(nut[0])
    except Exception:
        return 23.4392911


def _kranti(sidereal_lon, ayanamsha, jd=None):
    """
    Ecliptic declination (kranti) from sayana longitude.
    δ = asin(sin ε · sin λ_tropical). rules.md §6.1 Ayana.
    """
    trop = (sidereal_lon + ayanamsha) % 360.0
    obl = _obliquity(jd) if jd is not None else 23.4392911
    return math.degrees(
        math.asin(math.sin(math.radians(obl)) * math.sin(math.radians(trop)))
    )


def calc_ayana_bala(planet, sidereal_lon, ayanamsha, jd=None):
    """
    Declination strength, max 60. rules.md §6.1.
    Sun/Mars/Jupiter/Venus: strong in northern declination.
    Moon/Saturn: strong in southern declination.
    Mercury: both (uses |δ|).
    BPHS: (24 ± δ) × 5/4.
    """
    k = _kranti(sidereal_lon, ayanamsha, jd)
    k = max(-_AYANA_MAX_DECL, min(_AYANA_MAX_DECL, k))
    if planet in _AYANA_NORTH:
        raw = (_AYANA_MAX_DECL + k) * 1.25
    elif planet in _AYANA_SOUTH:
        raw = (_AYANA_MAX_DECL - k) * 1.25
    else:
        raw = (_AYANA_MAX_DECL + abs(k)) * 1.25
    return max(0.0, min(60.0, raw))


def _sun_sidereal(jd):
    result, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return result[0], result[3]


def _jd_when_sun_at(target_lon, before_jd):
    """Julian day when sidereal Sun last crossed target_lon at/before before_jd."""
    lon, speed = _sun_sidereal(before_jd)
    past = (lon - target_lon) % 360.0
    spd = speed if abs(speed) > 1e-6 else 0.985647
    guess = before_jd - past / spd
    for _ in range(12):
        lon, speed = _sun_sidereal(guess)
        err = ((lon - target_lon + 180.0) % 360.0) - 180.0
        spd = speed if abs(speed) > 1e-6 else 0.985647
        guess -= err / spd
        if abs(err) < 1e-7:
            break
    return guess


def _vara_lord_from_jd(jd, tz_offset_hours):
    """Weekday lord of the local civil date of jd. rules.md §14.4."""
    from .panchang import DAY_LORDS
    y, m, d, _hour = swe.revjul(jd + tz_offset_hours / 24.0)
    dt = datetime(int(y), int(m), int(d))
    sunday0 = (dt.weekday() + 1) % 7
    return DAY_LORDS[sunday0]


def _abda_masa_lords(chart):
    """
    Year lord (Abda) = vara lord of Mesha Sankranti of the current solar year.
    Month lord (Masa) = vara lord of the Sun's entry into the natal solar sign.
    """
    jd = chart.positions.get("_jd")
    sun = chart.positions.get("Sun", {}).get("longitude", 0.0)
    tz_off = chart.positions.get("_tz_offset", 0.0) or 0.0
    if not jd:
        return None, None
    try:
        abda_jd = _jd_when_sun_at(0.0, jd)
        masa_target = (int(sun / 30.0) * 30.0) % 360.0
        masa_jd = _jd_when_sun_at(masa_target, jd)
        return _vara_lord_from_jd(abda_jd, tz_off), _vara_lord_from_jd(masa_jd, tz_off)
    except Exception:
        return None, None


def _tribhaga_planet(chart, is_day_birth):
    """
    Lord of the current third of day or night. rules.md §6.1 Tribhaga.
    Day: Mercury / Sun / Saturn. Night: Moon / Venus / Mars.
    """
    ss = chart.sunrise_sunset or {}
    birth_jd = chart.positions.get("_jd")
    rise = ss.get("sunrise_jd")
    sunset = ss.get("sunset_jd")
    if not (birth_jd and rise and sunset):
        return None

    bd = chart.birth_data
    ephe = getattr(chart, "_ephe", None)

    if is_day_birth and rise <= birth_jd < sunset:
        dur = sunset - rise
        frac = ((birth_jd - rise) / dur) if dur > 0 else 0.0
        if frac < 1.0 / 3.0:
            return "Mercury"
        if frac < 2.0 / 3.0:
            return "Sun"
        return "Saturn"

    if ephe is None:
        return None
    date = datetime.strptime(bd["date"], "%Y-%m-%d")
    lat, lon, tz = bd["lat"], bd["lon"], bd["tz"]
    if birth_jd < rise:
        prev = (date - timedelta(days=1)).strftime("%Y-%m-%d")
        night_start = ephe.get_sunrise_sunset(prev, lat, lon, tz).get("sunset_jd")
        night_end = rise
    else:
        nxt = (date + timedelta(days=1)).strftime("%Y-%m-%d")
        night_start = sunset
        night_end = ephe.get_sunrise_sunset(nxt, lat, lon, tz).get("sunrise_jd")
    if not (night_start and night_end):
        return None
    dur = night_end - night_start
    frac = ((birth_jd - night_start) / dur) if dur > 0 else 0.0
    if frac < 1.0 / 3.0:
        return "Moon"
    if frac < 2.0 / 3.0:
        return "Venus"
    return "Mars"


def _paksha_bala(planet, moon_long, sun_long):
    """
    Paksha from elongation E (shortest arc). Benefics: E/3.
    Malefics: 60 − E/3. Moon is doubled (2×E/3).
    JHora leaves Moon's doubled value uncapped in Kala Bala (can exceed 60
    near full moon). Cheshta/Ishta still clamp Moon separately.
    """
    e = _shortest_arc(moon_long, sun_long)
    base = e / 3.0
    if planet == "Moon":
        return 2.0 * base
    if planet in ("Jupiter", "Venus", "Mercury"):
        return max(0.0, min(60.0, base))
    return max(0.0, min(60.0, 60.0 - base))


def calc_kala_bala(planet, is_day_birth, is_waxing_moon=True,
                   hora_lord=None, vara_lord=None,
                   abda_lord=None, masa_lord=None,
                   tribhaga_planet=None, ayana=0.0, yuddha=0.0,
                   moon_long=None, sun_long=None,
                   birth_jd=None, sunrise_jd=None, sunset_jd=None):
    """
    Kala Bala: Natonnatha + Paksha + Tribhaga + Abda/Masa/Vara/Hora
    + Ayana + Yuddha. rules.md §6.1.
    """
    if birth_jd is not None and sunrise_jd is not None and sunset_jd is not None:
        midday = 0.5 * (sunrise_jd + sunset_jd)
        dist_noon = abs(birth_jd - midday)
        if dist_noon <= 0.5:
            unnatha = max(0.0, min(60.0, 60.0 * (1.0 - dist_noon / 0.5)))
        else:
            unnatha = 0.0
        nata = 60.0 - unnatha
    else:
        unnatha = 60.0 if is_day_birth else 0.0
        nata = 0.0 if is_day_birth else 60.0

    day_strong = ["Sun", "Jupiter", "Venus"]
    night_strong = ["Moon", "Mars", "Saturn"]

    if planet in day_strong:
        natonnatha = unnatha
    elif planet in night_strong:
        natonnatha = nata
    elif planet == "Mercury":
        natonnatha = 60.0
    else:
        natonnatha = 30.0

    if moon_long is not None and sun_long is not None:
        paksha = _paksha_bala(planet, moon_long, sun_long)
    else:
        benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
        if planet in benefics:
            paksha = 60 if is_waxing_moon else 0
        else:
            paksha = 0 if is_waxing_moon else 60

    # Jupiter always 60; the segment lord also 60 (no stacking if both).
    tribhaga = 0
    if planet == "Jupiter":
        tribhaga = 60
    if tribhaga_planet == planet:
        tribhaga = 60

    abda = 15 if abda_lord == planet else 0
    masa = 30 if masa_lord == planet else 0
    hora = 60 if hora_lord == planet else 0
    vara = 45 if vara_lord == planet else 0

    total = (natonnatha + paksha + tribhaga + abda + masa + vara + hora
             + ayana + yuddha)
    return {
        "total": total,
        "divaratri": round(natonnatha, 2),
        "natonnatha": round(natonnatha, 2),
        "paksha": round(paksha, 2),
        "tribhaga": tribhaga,
        "abda": abda,
        "masa": masa,
        "hora": hora,
        "vara": vara,
        "ayana": round(ayana, 2),
        "yuddha": yuddha,
    }


# ═══════════════════════════════════════════
# DRIK BALA (Aspectual Strength)
# ═══════════════════════════════════════════

# House-count pinda (Bhava Drishti Bala §6.7). Index = ΔH 1–12.
_DRIK_BASE = [0, 0, 0, 15, 30, 15, 0, 60, 30, 15, 30, 15, 0]
_DRIK_SPECIAL = {
    "Mars":    {4: 15, 8: 15},
    "Jupiter": {5: 30, 9: 30},
    "Saturn":  {3: 45, 10: 15},
}


def _drishti_pinda(aspector, from_house, to_house):
    delta = ((to_house - from_house) % 12) + 1  # 1 = same house
    base = _DRIK_BASE[delta] if 0 <= delta < len(_DRIK_BASE) else 0
    special = _DRIK_SPECIAL.get(aspector, {}).get(delta, 0)
    return base + special


def _spashta_drishti_virupa(sep, aspector):
    """
    Degree-based spashta dṛṣṭi in virupas (BPHS ch.26 / JHora).
    sep = (aspected λ − aspecting λ) mod 360.
    Special aspects of Mars/Jupiter/Saturn are added in their peak bands.
    """
    a = sep % 360.0
    if a < 30:
        v = 0.0
    elif a < 60:
        v = 0.5 * (a - 30.0)
    elif a < 90:
        v = (a - 60.0) + 15.0
        if aspector == "Saturn":
            v += 45.0
    elif a < 120:
        v = 0.5 * (120.0 - a) + 30.0
        if aspector == "Mars":
            v += 15.0
    elif a < 150:
        v = 150.0 - a
        if aspector == "Jupiter":
            v += 30.0
    elif a < 180:
        v = 2.0 * (a - 150.0)
    elif a < 300:
        v = 0.5 * (300.0 - a)
        if aspector == "Mars" and 210.0 <= a < 240.0:
            v += 15.0
        if aspector == "Jupiter" and 240.0 <= a < 270.0:
            v += 30.0
        if aspector == "Saturn" and 270.0 <= a < 300.0:
            v += 45.0
    else:
        v = 0.0
    return max(0.0, min(60.0, v))


def calc_drik_bala(planet, rashi_chart, is_waxing_moon=True, positions=None):
    """
    Graha Drik Bala (rules.md §6.1 / JHora):
      (Σ benefic spashta virupa − Σ malefic spashta virupa) / 4
    Uses natal longitudes. Whole-sign pinda is only the Bhava-Drishti fallback.
    """
    benefics = {"Jupiter", "Venus", "Mercury"}
    if is_waxing_moon:
        benefics.add("Moon")
    malefics = {"Sun", "Mars", "Saturn"}
    if not is_waxing_moon:
        malefics.add("Moon")

    target_lon = None
    if isinstance(positions, dict):
        target_lon = (positions.get(planet) or {}).get("longitude")
    if target_lon is not None:
        net = 0.0
        for other in PLANETS_7:
            if other == planet:
                continue
            src_lon = (positions.get(other) or {}).get("longitude")
            if src_lon is None:
                continue
            vir = _spashta_drishti_virupa((target_lon - src_lon) % 360.0, other)
            if other in benefics:
                net += vir
            elif other in malefics:
                net -= vir
        return net / 4.0

    target = rashi_chart.get(planet, {}).get("house_rashi", 0)
    if not target:
        return 0.0
    bala = 0.0
    for other in PLANETS_7:
        if other == planet:
            continue
        src = rashi_chart.get(other, {}).get("house_rashi", 0)
        if not src:
            continue
        pinda = _drishti_pinda(other, src, target)
        if other in benefics:
            bala += pinda
        elif other in malefics:
            bala -= pinda
    return bala / 4.0


# ═══════════════════════════════════════════
# COMPLETE SHADBALA
# ═══════════════════════════════════════════

def _dig_peak_longitude(chart, planet):
    """Peak longitude for planetary Dig Bala from house cusps. §6.1."""
    hc = getattr(chart, "house_cusps", None) or {}
    cusps = hc.get("cusps") or {}
    asc = hc.get("asc")
    if asc is None:
        asc = chart.positions.get("Lagna", {}).get("longitude", 0.0)
    mc = hc.get("mc")
    if mc is None and 10 in cusps:
        mc = cusps[10].get("longitude")
    best = DIG_BALA_HOUSES.get(planet)
    if best == 1:
        return cusps.get(1, {}).get("longitude", asc)
    if best == 4:
        return cusps.get(4, {}).get("longitude", (asc + 90.0) % 360.0)
    if best == 7:
        return cusps.get(7, {}).get("longitude", (asc + 180.0) % 360.0)
    if best == 10:
        return cusps.get(10, {}).get("longitude", mc if mc is not None else (asc + 270.0) % 360.0)
    return None


def calc_shadbala(chart):
    """
    Calculate complete Shadbala for all 7 planets.
    
    Args:
        chart: BirthChart object with positions, rashi_chart, aspects
        
    Returns:
        dict of planet -> {
            rupas: total in Rupas (Shashtiamsas / 60),
            shashtiamsas: total in Shashtiamsas,
            components: {sthana, dig, kala, cheshta, naisargika, drik},
            minimum: required minimum in Rupas,
            passes: bool,
            status: "Passes" / "Sub-minimum"
        }
    """
    positions = chart.positions
    rashi_chart = chart.rashi_chart

    is_day = True
    ss = getattr(chart, "sunrise_sunset", None) or {}
    if ss.get("is_day_birth") is not None:
        is_day = bool(ss["is_day_birth"])
    rise_jd = ss.get("sunrise_jd")
    set_jd = ss.get("sunset_jd")

    sun_long = positions.get("Sun", {}).get("longitude", 0)
    moon_long = positions.get("Moon", {}).get("longitude", 0)
    moon_minus_sun = (moon_long - sun_long) % 360
    is_waxing = moon_minus_sun < 180
    ayanamsha = positions.get("_ayanamsha", 0.0) or 0.0
    jd = positions.get("_jd")

    hora_lord = vara_lord = None
    try:
        pan = chart.panchang
        hora_lord = pan.get("hora", {}).get("hora_lord")
        vara_lord = pan.get("vara", {}).get("lord")
    except Exception:
        pass

    abda_lord, masa_lord = _abda_masa_lords(chart)
    tribhaga_planet = _tribhaga_planet(chart, is_day)

    yuddha_adj = {p: 0.0 for p in PLANETS_7}
    try:
        y = chart.yuddha or {}
        for w in (y.get("winners") or []):
            if w in yuddha_adj:
                yuddha_adj[w] += 60.0
        for w in (y.get("losers") or []):
            if w in yuddha_adj:
                yuddha_adj[w] -= 60.0
    except Exception:
        pass

    temp_friends = get_temporal_friendship(positions)
    result = {}

    for planet in PLANETS_7:
        pos = positions.get(planet, {})
        rc = rashi_chart.get(planet, {})
        if not pos or not rc:
            continue

        longitude = pos.get("longitude", 0)
        sign = pos.get("sign", "Aries")
        degree_in_sign = pos.get("degree_in_sign", 0)
        house_num = rc.get("house_rashi", 1)
        chalit = getattr(chart, "chalit_chart", {}).get(planet, {})
        dig_house = chalit.get("house_chalit") or house_num

        # 1. Sthana Bala (with Panchadha Maitri)
        sthana = calc_sthana_bala(planet, longitude, sign, degree_in_sign, house_num, temp_friends=temp_friends)

        # 2. Dig Bala (peak cusp longitude, Chalit house fallback)
        peak = _dig_peak_longitude(chart, planet)
        dig = calc_dig_bala(planet, dig_house, longitude=longitude, peak_longitude=peak)

        # 3. Kala Bala (full 6 sub-components with continuous Natonnatha)
        ayana = calc_ayana_bala(planet, longitude, ayanamsha, jd)
        kala = calc_kala_bala(
            planet, is_day, is_waxing,
            hora_lord=hora_lord, vara_lord=vara_lord,
            abda_lord=abda_lord, masa_lord=masa_lord,
            tribhaga_planet=tribhaga_planet, ayana=ayana,
            yuddha=yuddha_adj.get(planet, 0.0),
            moon_long=moon_long, sun_long=sun_long,
            birth_jd=jd, sunrise_jd=rise_jd, sunset_jd=set_jd,
        )

        # 4. Cheshta Bala — Sun = Ayana, Moon = Paksha (undoubled E/3); tara = Seeghra Kendra/3 (§6.1)
        if planet == "Sun":
            cheshta = ayana
        elif planet == "Moon":
            cheshta = min(60.0, _shortest_arc(moon_long, sun_long) / 3.0)
        else:
            cheshta = calc_cheshta_bala(
                planet, longitude, jd, chart.birth_data.get("lon", 0.0)
            )

        # 5. Naisargika Bala
        naisargika = NAISARGIKA_BALA[planet]

        # 6. Drik Bala
        drik = calc_drik_bala(planet, rashi_chart, is_waxing, positions=positions)

        # Total in Shashtiamsas
        total_sa = (sthana["total"] + dig + kala["total"] +
                    cheshta + naisargika + drik)

        # Convert to Rupas (1 Rupa = 60 Shashtiamsas)
        rupas = total_sa / 60.0
        minimum = MINIMUM_SHADBALA[planet]

        result[planet] = {
            "rupas": round(rupas, 2),
            "shashtiamsas": round(total_sa, 2),
            "components": {
                "sthana": round(sthana["total"], 2),
                "sthana_detail": sthana,
                "dig": round(dig, 2),
                "kala": round(kala["total"], 2),
                "kala_detail": kala,
                "cheshta": round(cheshta, 2),
                "naisargika": round(naisargika, 2),
                "drik": round(drik, 2),
            },
            "minimum": minimum,
            "passes": rupas >= minimum,
            "status": "Passes" if rupas >= minimum else "Sub-minimum",
        }

    return result


# ═══════════════════════════════════════════
# ISHTA-KASHTA PHALA
# ═══════════════════════════════════════════

def calc_ishta_kashta(chart):
    """
    Calculate Ishtaphala and Kashtaphala for all 7 planets.
    
    Ishtaphala = good results indicator
    Kashtaphala = problematic results indicator
    
    Simplified formula:
    Uchcha Bala (0-60) feeds into:
      Ishta = sqrt(Uchcha × Cheshta) × OjhaYugma factor
      Kashta = sqrt((60-Uchcha) × (60-Cheshta)) × factor
    """
    positions = chart.positions
    rashi_chart = chart.rashi_chart
    result = {}

    for planet in PLANETS_7:
        pos = positions.get(planet, {})
        rc = rashi_chart.get(planet, {})
        if not pos or not rc:
            continue

        longitude = pos.get("longitude", 0)
        retrograde = pos.get("retrograde", False)

        uchcha = _uchcha_bala(planet, longitude)
        ayanamsha = positions.get("_ayanamsha", 0.0) or 0.0
        jd = positions.get("_jd")
        if planet == "Sun":
            cheshta = calc_ayana_bala(planet, longitude, ayanamsha, jd)
        elif planet == "Moon":
            # Ishta-Kashta uses undoubled elongation/3 (JHora / Sripati Chesta).
            # Doubled Paksha is a Kala-Bala term; capping it at 60 forces Kashta=0.
            sun_long = positions.get("Sun", {}).get("longitude", 0)
            cheshta = min(60.0, _shortest_arc(longitude, sun_long) / 3.0)
        else:
            cheshta = calc_cheshta_bala(
                planet, longitude, jd, chart.birth_data.get("lon", 0.0)
            )
        # Ishta/Kashta in JHora tracks Chesta more strongly for vakri grahas.
        if retrograde:
            cheshta = max(cheshta, 45.0)

        # IshtaPhala
        ishta = math.sqrt(max(0, uchcha * cheshta))

        # KashtaPhala
        kashta = math.sqrt(max(0, (60 - uchcha) * (60 - cheshta)))

        result[planet] = {
            "ishta": round(ishta, 2),
            "kashta": round(kashta, 2),
            "net": round(ishta - kashta, 2),
            "dominant": "Ishta" if ishta > kashta else "Kashta",
        }

    return result


# ═══════════════════════════════════════════
# AVASTHAS (Planetary States)
# ═══════════════════════════════════════════

def get_avasthas(positions):
    """
    Calculate Baladi Avasthas (age-based states) for all planets.
    
    Based on degree in sign (6° per division):
    - Bala (infant): 0-6°
    - Kumara (adolescent): 6-12°
    - Yuva (young/prime): 12-18°
    - Vriddha (old): 18-24°
    - Mrita (dead): 24-30°
    
    Note: Some BPHS commentaries apply even-sign reversal, but the
    straightforward 6° division matches JHora output for most planets.
    """
    avasthas_list = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
    result = {}

    for planet in PLANETS_7:
        pos = positions.get(planet, {})
        if not pos or isinstance(pos, (float, int)):
            continue

        degree = pos.get("degree_in_sign", 0)
        sign_idx = SIGN_INDEX.get(pos.get("sign", "Aries"), 0)
        division = int(degree / 6)
        division = min(division, 4)
        # Even signs reverse Baladi (JHora / BPHS commentary)
        if sign_idx % 2 == 1:
            division = 4 - division
        avastha = avasthas_list[division]

        result[planet] = {
            "avastha": avastha,
            "degree_in_sign": round(degree, 2),
            "sign": pos.get("sign", ""),
            "description": _avastha_description(avastha),
        }

    return result


def get_jagradadi(chart):
    """Jaagrita / Swapna / Sushupta from dignity. rules.md §6.6.2."""
    result = {}
    for planet in PLANETS_7:
        dig = chart.rashi_chart.get(planet, {}).get("dignity", "")
        if dig in ("Own Sign", "Exalted", "Moolatrikona"):
            av, mult = "Jaagrita", 1.0
        elif dig == "Friendly":
            av, mult = "Swapna", 0.5
        else:
            av, mult = "Sushupta", 0.25
        result[planet] = {"avastha": av, "multiplier": mult, "dignity": dig}
    return result


def get_deeptadi(chart):
    """Nine illumination states. rules.md §6.6.3. First matching condition wins."""
    losers = set()
    try:
        losers = set(chart.yuddha.get("losers") or [])
    except Exception:
        pass
    result = {}
    for planet in PLANETS_7:
        dig = chart.rashi_chart.get(planet, {}).get("dignity", "")
        combust = False
        try:
            combust = bool(chart.combustion.get(planet, {}).get("is_combust"))
        except Exception:
            pass
        d9_sign = (chart.vargas.get("D9") or {}).get(planet)
        d9_dig = chart._get_dignity(planet, d9_sign) if d9_sign else ""
        if combust:
            av = "Vikala"
        elif planet in losers:
            av = "Kopa"
        elif dig == "Exalted":
            av = "Deepta"
        elif dig == "Own Sign" or dig == "Moolatrikona":
            av = "Swastha"
        elif dig == "Friendly":
            av = "Mudita"
        elif dig == "Debilitated":
            av = "Bheeta"
        elif dig == "Enemy":
            av = "Khala"
        elif dig == "Neutral":
            av = "Shanta" if d9_dig in (
                "Own Sign", "Exalted", "Moolatrikona", "Friendly"
            ) else "Dina"
        else:
            av = "Shanta"
        result[planet] = {
            "avastha": av,
            "dignity": dig,
            "d9_sign": d9_sign,
            "d9_dignity": d9_dig or None,
        }
    return result


def _avastha_description(avastha):
    """Return interpretation text for an avastha."""
    descriptions = {
        "Bala": "Infant state — planet gives quarter results, needs support",
        "Kumara": "Adolescent — gives half results, developing",
        "Yuva": "Young/prime — gives FULL results, most productive",
        "Vriddha": "Old/aged — ~15% fruit, past prime",
        "Mrita": "Dead state — ~5% fruit, largely ineffective",
    }
    return descriptions.get(avastha, "Unknown")


# ═══════════════════════════════════════════
# VIMSOPAKA STRENGTH
# ═══════════════════════════════════════════

# Shodasha Varga weights from rules.md §6.5. Tabulated sum is 21;
# scores are divided by that sum so Vimsopaka remains 0–20.
VIMSOPAKA_WEIGHTS = {
    "D1": 3.5, "D2": 1.5, "D3": 1.5, "D4": 1.5, "D7": 1.5,
    "D9": 3.0, "D10": 1.5, "D12": 1.5, "D16": 1.0, "D20": 1.0,
    "D24": 1.0, "D27": 0.5, "D30": 0.5, "D40": 0.5, "D45": 0.5,
    "D60": 0.5,
}
VIMSOPAKA_WEIGHT_SUM = sum(VIMSOPAKA_WEIGHTS.values())


def _vimsopaka_dignity_score(planet, varga_sign, degree_in_sign=None, is_d1=False):
    """
    Dignity points out of 20 for one varga. rules.md §6.5:
    Own/Exalted 20, Moolatrikona 15, Friendly 10, Neutral 5, Enemy 2, Debilitated 0.
    """
    if planet in DEBILITATION and DEBILITATION[planet][0] == varga_sign:
        return 0
    if planet in EXALTATION and EXALTATION[planet][0] == varga_sign:
        return 20
    if planet in OWN_SIGNS and varga_sign in OWN_SIGNS[planet]:
        return 20
    if planet in MOOLATRIKONA:
        mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
        if varga_sign == mt_sign:
            if not is_d1:
                return 15
            if degree_in_sign is not None and mt_start <= degree_in_sign < mt_end:
                return 15
    lord = SIGN_LORDS.get(varga_sign, "")
    if planet in NATURAL_FRIENDS and lord in NATURAL_FRIENDS[planet]:
        return 10
    if planet in NATURAL_ENEMIES and lord in NATURAL_ENEMIES[planet]:
        return 2
    return 5


def calc_vimsopaka(positions, vargas):
    """
    Shodasa-varga Vimsopaka bala (0–20). rules.md §6.5.

    Vimsopaka(P) = Σ dignity_score(P, Varga_i) × weight_i / 20
    """
    result = {}

    for planet in PLANETS_7:
        pos = positions.get(planet, {})
        if not pos or isinstance(pos, (float, int)):
            continue

        degree_in_sign = pos.get("degree_in_sign")
        score = 0.0

        for varga, weight in VIMSOPAKA_WEIGHTS.items():
            varga_chart = vargas.get(varga, {})
            varga_sign = varga_chart.get(planet, "")
            if not varga_sign:
                continue
            dignity = _vimsopaka_dignity_score(
                planet, varga_sign, degree_in_sign, is_d1=(varga == "D1")
            )
            # spec: dignity × weight / 20; tabulated weights sum to 21, so
            # divide by Σw to keep the published 0–20 ceiling.
            score += dignity * (weight / VIMSOPAKA_WEIGHT_SUM)

        result[planet] = round(score, 2)

    return result


# ═══════════════════════════════════════════
# BHAVA BALA (House Strength)
# ═══════════════════════════════════════════

def _bhava_sphuta(asc_long, house):
    """Equal-madhya bhava midpoint: Lagna is 1H sphuta. rules.md §6.7."""
    return (asc_long + (house - 1) * 30.0) % 360.0


# Kendra whose directional peak this house uses (east/north/west/south).
_BHAVA_DIG_KENDRA = {
    1: 1, 2: 1, 12: 1,
    4: 4, 3: 4, 5: 4,
    7: 7, 6: 7, 8: 7,
    10: 10, 9: 10, 11: 10,
}


def _bhava_dig_bala(asc_long, house):
    """
    Bhava Dig Bala from the house midpoint vs its quadrant zero-point.
    Dig = Δλ_from_zero / 3. Kendras (midpoint = peak) get 60.
    """
    mid = _bhava_sphuta(asc_long, house)
    peak = _bhava_sphuta(asc_long, _BHAVA_DIG_KENDRA[house])
    zero = (peak + 180.0) % 360.0
    return max(0.0, min(60.0, _shortest_arc(mid, zero) / 3.0))


def _bhava_drishti_bala(house, rashi_chart, is_waxing_moon=True):
    """
    Sum of Spashta Drishti Pinda on this bhava. Benefics add, malefics subtract.
    rules.md §6.7 / §2.10.
    """
    benefics = {"Jupiter", "Venus", "Mercury"}
    if is_waxing_moon:
        benefics.add("Moon")
    malefics = {"Sun", "Mars", "Saturn"}
    if not is_waxing_moon:
        malefics.add("Moon")
    bala = 0.0
    for planet in PLANETS_7:
        src = rashi_chart.get(planet, {}).get("house_rashi", 0)
        if not src:
            continue
        pinda = _drishti_pinda(planet, src, house)
        if planet in benefics:
            bala += pinda
        elif planet in malefics:
            bala -= pinda
    return bala


def calc_bhava_bala(chart):
    """
    Bhava Bala = Bhavadhipati + Bhava Dig + Bhava Drishti. rules.md §6.7.

    Returns dict of house_num -> {rupas, lord, lord_shadbala, dig, drishti, ...}
    """
    shadbala = calc_shadbala(chart)
    rashi_chart = chart.rashi_chart
    lordships = chart.lordships
    asc = chart.positions.get("Lagna", {}).get("longitude", 0.0)
    sun_long = chart.positions.get("Sun", {}).get("longitude", 0.0)
    moon_long = chart.positions.get("Moon", {}).get("longitude", 0.0)
    is_waxing = ((moon_long - sun_long) % 360) < 180

    result = {}

    for house in range(1, 13):
        lord = lordships.get(house, "")
        lord_sa = shadbala.get(lord, {}).get("shashtiamsas", 0.0) if lord else 0.0
        lord_rupas = shadbala.get(lord, {}).get("rupas", 0.0) if lord else 0.0
        dig = _bhava_dig_bala(asc, house)
        drishti = _bhava_drishti_bala(house, rashi_chart, is_waxing)
        total_sa = lord_sa + dig + drishti
        planets_in = chart.get_planets_in_house(house, "rashi")

        result[house] = {
            "rupas": round(total_sa / 60.0, 2),
            "shashtiamsas": round(total_sa, 2),
            "lord": lord,
            "lord_shadbala": lord_rupas,
            "adhipati": round(lord_sa, 2),
            "dig": round(dig, 2),
            "drishti": round(drishti, 2),
            "planets": planets_in,
        }

    return result


# ═══════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════

def format_shadbala_table(shadbala_data):
    """Format Shadbala as a readable text table."""
    lines = []
    lines.append("═══ Shadbala Summary ═══\n")
    lines.append(
        f"{'Planet':<10} {'Rupas':>7} {'Min':>5} {'Status':<15} "
        f"{'Sthana':>7} {'Dig':>5} {'Kala':>5} {'Cheshta':>7} {'Naisar':>7} {'Drik':>5}"
    )
    lines.append("─" * 90)

    # Sort by rupas descending
    sorted_planets = sorted(
        shadbala_data.items(),
        key=lambda x: x[1]["rupas"],
        reverse=True
    )

    for planet, data in sorted_planets:
        comp = data["components"]
        lines.append(
            f"{planet:<10} {data['rupas']:>7.2f} {data['minimum']:>5.1f} "
            f"{'✓ Passes' if data['passes'] else '✗ Sub-min':<15} "
            f"{comp['sthana']:>7.1f} {comp['dig']:>5.1f} {comp['kala']:>5.1f} "
            f"{comp['cheshta']:>7.1f} {comp['naisargika']:>7.2f} {comp['drik']:>5.1f}"
        )

    return "\n".join(lines)
