"""
Whole-sign house arithmetic — the only sign↔house conversion in the engine.

House 1 = Lagna sign. Houses count zodiacally (Aries→Pisces).
Origin may be Lagna, Moon, a varga lagna, or any other sign index.

    house = ((sign_idx - origin_idx) % 12) + 1
    sign  = (origin_idx + house - 1) % 12
"""

from .constants import SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_MODALITY

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)
UPACHAYA_HOUSES = (3, 6, 10, 11)
TRISHADAYA_HOUSES = (3, 6, 11)
DUSTHANA_HOUSES = (6, 8, 12)
MARAKA_HOUSES = (2, 7)

BADHAKA_HOUSE_BY_MODALITY = {
    "Movable": 11,
    "Fixed": 9,
    "Dual": 7,
}


def _sign_idx(value):
    if isinstance(value, str):
        if value not in SIGN_INDEX:
            raise ValueError(f"unknown sign {value!r}")
        return SIGN_INDEX[value]
    idx = int(value)
    if not 0 <= idx <= 11:
        raise ValueError(f"sign index must be 0-11, got {idx}")
    return idx


def _house_num(value):
    h = int(value)
    if not 1 <= h <= 12:
        raise ValueError(f"house must be 1-12, got {h}")
    return h


def sign_to_house(sign, origin):
    """
    Whole-sign house (1-12) of `sign` counted from `origin`.
    origin is usually Lagna; also Moon, D10 lagna, etc.
    Accepts 0-based index or sign name.
    """
    return ((_sign_idx(sign) - _sign_idx(origin)) % 12) + 1


def house_to_sign_index(house_num, origin):
    """Sign index (0-11) occupying `house_num` (1-12) from `origin`."""
    return (_sign_idx(origin) + _house_num(house_num) - 1) % 12


def house_to_sign(house_num, origin):
    """Sign name occupying `house_num` from `origin`."""
    return SIGNS[house_to_sign_index(house_num, origin)]


def houses_from(target_house, origin_house):
    """
    Count of houses from `origin_house` to `target_house` (both 1-12).
    Same house → 1; opposite → 7.
    """
    return ((_house_num(target_house) - _house_num(origin_house)) % 12) + 1


def house_counted_from(start_house, count):
    """
    House reached by counting `count` bhavas from `start_house`.
    count=1 is the start itself; count=7 is the 7th.
    """
    h = _house_num(start_house)
    c = int(count)
    return ((h - 1 + c - 1) % 12) + 1


def bhavat_bhavam(house_num):
    """Bhava-from-bhava: count H houses from house H. rules.md §18."""
    h = _house_num(house_num)
    return house_counted_from(h, h)


def badhaka_house(lagna):
    """Badhaka house number from Lagna modality. rules.md §2.11."""
    sign = SIGNS[_sign_idx(lagna)]
    return BADHAKA_HOUSE_BY_MODALITY[SIGN_MODALITY[sign]]


def badhaka_sign(lagna):
    """Sign name of the Badhaka house."""
    return house_to_sign(badhaka_house(lagna), lagna)


def is_kendra_house(house_num):
    return _house_num(house_num) in KENDRA_HOUSES


def is_trikona_house(house_num):
    return _house_num(house_num) in TRIKONA_HOUSES


def is_dusthana_house(house_num):
    return _house_num(house_num) in DUSTHANA_HOUSES


def build_house_map(lagna):
    """house → {house, sign, sign_index, lord, modality}."""
    origin = _sign_idx(lagna)
    out = {}
    for h in range(1, 13):
        sidx = house_to_sign_index(h, origin)
        sign = SIGNS[sidx]
        out[h] = {
            "house": h,
            "sign": sign,
            "sign_index": sidx,
            "lord": SIGN_LORDS[sign],
            "modality": SIGN_MODALITY[sign],
        }
    return out
