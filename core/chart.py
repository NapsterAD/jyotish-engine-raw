"""
chart.py — Birth chart assembly: lordships, dignity, house placement, aspects, chalit.
Combines ephemeris positions with astrological rules.
Integrates computation modules: vargas, dashas, ashtakavarga, shadbala.
"""

from .constants import (
    SIGNS, SIGN_INDEX, SIGN_LORDS, SIGN_ELEMENT, SIGN_MODALITY,
    EXALTATION, DEBILITATION, MOOLATRIKONA, OWN_SIGNS,
    NATURAL_FRIENDS, NATURAL_ENEMIES, SPECIAL_ASPECTS,
    PLANETS_7, PLANETS_9,
    get_house_lordships, get_functional_nature, get_navamsa_sign
)
from .ephemeris import Ephemeris
from .mapping import sign_to_house, house_counted_from, house_to_sign


class BirthChart:
    """Complete birth chart with positions, lordships, dignities, aspects,
    vargas, dashas, ashtakavarga, and shadbala."""

    def __init__(self, date, time, tz, lat, lon, name="",
                 ayanamsha="lahiri", ephe_path=None):
        """
        Build a complete birth chart.
        
        Args:
            date: "YYYY-MM-DD"
            time: "HH:MM:SS"
            tz: "+05:30" or "IST (+5:30)"
            lat, lon: birth coordinates
            name: person's name (for reports)
            ayanamsha: "lahiri" (default)
            ephe_path: path to Swiss Ephemeris .se1 files
        """
        from .inputs import normalize_birth_inputs
        date, time, _tz_hours, lat, lon, ayanamsha = normalize_birth_inputs(
            date, time, tz, lat, lon, ayanamsha
        )
        self.birth_data = {
            "date": date, "time": time, "tz": tz,
            "lat": lat, "lon": lon, "name": name or "",
            "ayanamsha": ayanamsha,
        }

        # Initialize ephemeris
        self._ephe = Ephemeris(ephe_path=ephe_path, ayanamsha=ayanamsha)

        # Core data — computed on init
        self.positions = self._ephe.get_planet_positions(date, time, tz, lat, lon)
        self.house_cusps = self._ephe.get_house_cusps(date, time, tz, lat, lon)
        self.sunrise_sunset = self._ephe.get_sunrise_sunset(date, lat, lon, tz)
        birth_jd = self.positions.get("_jd")
        rise_jd = self.sunrise_sunset.get("sunrise_jd")
        set_jd = self.sunrise_sunset.get("sunset_jd")
        if birth_jd and rise_jd and set_jd:
            self.sunrise_sunset["is_day_birth"] = rise_jd <= birth_jd < set_jd
        self.special_lagnas = self._ephe.get_special_lagnas(date, time, tz, lat, lon)

        # ── Auditability metadata ──────────────────────────────
        # Every chart self-documents exact conventions used, so
        # cross-validation mismatches are impossible to miss.
        self.birth_data["resolved_tz_offset_hours"] = _tz_hours
        self.birth_data["ayanamsha_value_deg"] = round(
            self.positions.get("_ayanamsha", 0.0), 6
        )
        self.birth_data["node_type"] = "mean"  # engine default (rules.md §1.3)
        self.birth_data["house_system"] = "equal_bhava"  # rashi = whole-sign
        self.birth_data["sunrise_method"] = "geometric"  # disc center, no refraction
        self.birth_data["julian_day"] = birth_jd

        # Derived data
        self.lagna_sign = self.positions["Lagna"]["sign"]
        self.lagna_index = SIGN_INDEX[self.lagna_sign]
        self.lordships = get_house_lordships(self.lagna_sign)
        self.functional_nature = get_functional_nature(self.lagna_sign)

        # Build rashi chart
        self.rashi_chart = self._build_rashi_chart()
        self.chalit_chart = self._build_chalit_chart()
        self.aspects = self._compute_aspects()

        # Lazy-computed caches (populated on first access)
        self._vargas = None
        self._dashas_vim = None
        self._dashas_yogini = None
        self._ashtakavarga = None
        self._shadbala = None
        self._avasthas = None
        self._ishta_kashta = None
        self._bhava_bala = None
        self._karakas_7 = None
        self._karakas_8 = None
        self._arudhas = None
        self._special_points = None
        self._yogas = None
        self._kakshyas = None
        self._kp = None
        self._panchang = None
        self._combustion = None
        self._yuddha = None
        self._badhaka = None
        self._jaimini_drishti = None
        self._dasha_systems = None
        self._sensitive = None
        self._nadi = None
        self._lal_kitab = None
        self._jagradadi = None
        self._deeptadi = None
        self._vimsopaka = None
        self._graha_arudhas = None
        self._dashas_vim5 = None
        self._raw_layers = None
        self._extra_points = None
        self._kp_advanced = None
        self._time_pack = None
        self._time_pack_key = None
        self._varsha_cache = None
        self._abcd_cache = None
        self._dhoomadi_upagrahas = None
        self._fertility_sphutas = None
        self._vaiseshikamsa = None
        self._sayanadi_avasthas = None
        self._pindayu_ayurdaya = None
        self._avasthas_complete = None
        self._sudarshana = None
        self._sbc = None
        self._career = None
        self._wealth = None
        self._medical = None
        self._nakshatra_bundle = None
        self._predictions = None
        self._nabhasa_yogas = None
        self._raja_yogas_ext = None

    # ═══════════════════════════════════════════
    # LAZY PROPERTIES — Computation Modules
    # ═══════════════════════════════════════════

    @property
    def vargas(self):
        """All 20 varga charts (D1-D60). Computed on first access."""
        if self._vargas is None:
            from ..computations.vargas import calc_all_vargas
            self._vargas = calc_all_vargas(self.positions)
        return self._vargas

    @property
    def dashas(self):
        """Vimshottari dasha table (MD/AD/PD). Computed on first access."""
        if self._dashas_vim is None:
            from ..computations.dashas import calc_vimshottari
            moon_long = self.positions.get("Moon", {}).get("longitude", 0)
            birth_jd = self.positions.get("_jd", 0)
            self._dashas_vim = calc_vimshottari(moon_long, birth_jd, levels=3)
        return self._dashas_vim

    @property
    def vimshottari(self):
        """Alias for dashas (Vimshottari MD/AD/PD)."""
        return self.dashas

    @property
    def vimshottari_5(self):
        """Vimshottari through Prana (MD/AD/PD/SD/PAD)."""
        if self._dashas_vim5 is None:
            from ..computations.dashas import calc_vimshottari
            moon_long = self.positions.get("Moon", {}).get("longitude", 0)
            birth_jd = self.positions.get("_jd", 0)
            self._dashas_vim5 = calc_vimshottari(moon_long, birth_jd, levels=5)
        return self._dashas_vim5

    @property
    def yogini_dasha(self):
        """Yogini dasha table. Computed on first access."""
        if self._dashas_yogini is None:
            from ..computations.dashas import calc_yogini
            moon_long = self.positions.get("Moon", {}).get("longitude", 0)
            birth_jd = self.positions.get("_jd", 0)
            self._dashas_yogini = calc_yogini(moon_long, birth_jd, formula="B")
        return self._dashas_yogini

    @property
    def ashtakavarga(self):
        """BAV + SAV data. Computed on first access."""
        if self._ashtakavarga is None:
            from ..computations.ashtakavarga import (
                calc_bav, calc_sav, calc_row_totals, calc_sodhya_pinda, calc_sav_by_house,
                check_sav_patterns, calc_patel_sensitive_points,
            )
            bav = calc_bav(self.positions)
            sav = calc_sav(bav)
            sodhya = calc_sodhya_pinda(bav, self.positions)
            self._ashtakavarga = {
                "bav": bav,
                "sav": sav,
                "row_totals": calc_row_totals(bav),
                "patterns": check_sav_patterns(sav, self.lagna_index),
                "sodhya": sodhya,
                "by_house": calc_sav_by_house(bav, self.lagna_index),
                "patel_points": calc_patel_sensitive_points(bav, sodhya, self.positions),
            }
        return self._ashtakavarga

    @property
    def shadbala(self):
        """Six-fold planetary strength. Computed on first access."""
        if self._shadbala is None:
            from ..computations.shadbala import calc_shadbala
            self._shadbala = calc_shadbala(self)
        return self._shadbala

    @property
    def avasthas(self):
        """Baladi avasthas. Computed on first access."""
        if self._avasthas is None:
            from ..computations.shadbala import get_avasthas
            self._avasthas = get_avasthas(self.positions)
        return self._avasthas

    @property
    def ishta_kashta(self):
        """Ishta-Kashta Phala. Computed on first access."""
        if self._ishta_kashta is None:
            from ..computations.shadbala import calc_ishta_kashta
            self._ishta_kashta = calc_ishta_kashta(self)
        return self._ishta_kashta

    @property
    def bhava_bala(self):
        """House strength. Computed on first access."""
        if self._bhava_bala is None:
            from ..computations.shadbala import calc_bhava_bala
            self._bhava_bala = calc_bhava_bala(self)
        return self._bhava_bala

    @property
    def vimsopaka(self):
        """Shodasa-varga Vimsopaka bala (0–20). rules.md §6.5."""
        if self._vimsopaka is None:
            from ..computations.shadbala import calc_vimsopaka
            self._vimsopaka = calc_vimsopaka(self.positions, self.vargas)
        return self._vimsopaka

    def get_current_dasha(self, target_date=None, levels=3):
        """Active Vimshottari for a date. levels=5 includes Sookshma and Prana."""
        from ..computations.dashas import get_current_dasha
        table = self.vimshottari_5 if levels >= 5 else self.dashas
        return get_current_dasha(table, target_date)

    @property
    def kp(self):
        """KP bundle: planet SSL, equal cusps, occupancy, ruling planets."""
        if self._kp is None:
            from ..computations.kp import calc_kp_bundle
            self._kp = calc_kp_bundle(self)
        return self._kp

    def kp_significators(self, house_num, system="placidus"):
        from ..computations.kp import abcd_significators
        return abcd_significators(self, house_num, system)

    def kp_fruitful(self, houses, deny_houses=None, system="placidus"):
        from ..computations.kp import fruitful_significators
        return fruitful_significators(self, houses, deny_houses, system)

    def kp_ruling_planets(self, date=None):
        from ..computations.kp import ruling_planets
        return ruling_planets(self, date)

    # ═══════════════════════════════════════════
    # UNIVERSAL CALCULATORS (any native)
    # ═══════════════════════════════════════════

    @property
    def panchang(self):
        """Tithi, Karana, Nithya Yoga, Vara, Nakshatra, Hora at birth."""
        if self._panchang is None:
            from ..computations.panchang import calc_panchang
            self._panchang = calc_panchang(self)
        return self._panchang

    @property
    def combustion(self):
        """Asta / Dagdha flags for every graha of this native."""
        if self._combustion is None:
            from ..computations.graha_state import calc_combustion
            self._combustion = calc_combustion(self)
        return self._combustion

    @property
    def yuddha(self):
        """Graha Yuddha pairs (Mars/Mercury/Jupiter/Venus/Saturn, orb 1°)."""
        if self._yuddha is None:
            from ..computations.graha_state import calc_graha_yuddha
            self._yuddha = calc_graha_yuddha(self)
        return self._yuddha

    @property
    def badhaka(self):
        """Badhaka house and Badhakesh from this Lagna's modality."""
        if self._badhaka is None:
            from ..computations.graha_state import calc_badhaka
            self._badhaka = calc_badhaka(self)
        return self._badhaka

    @property
    def jaimini_drishti(self):
        """Jaimini rashi drishti: signs and planets aspected by each graha."""
        if self._jaimini_drishti is None:
            from ..computations.graha_state import calc_jaimini_drishti
            self._jaimini_drishti = calc_jaimini_drishti(self)
        return self._jaimini_drishti

    def sade_sati_for(self, date, time="12:00:00", tz=None):
        """
        Sade-Sati / Ashtama Shani / Kantaka Shani on `date` vs this natal Moon.
        """
        from ..computations.transits import calc_sade_sati
        tz = tz or self.birth_data["tz"]
        t_pos = self._ephe.get_planet_positions(
            date, time, tz, self.birth_data["lat"], self.birth_data["lon"]
        )
        sat_long = t_pos.get("Saturn", {}).get("longitude", 0.0)
        moon_long = self.positions.get("Moon", {}).get("longitude", 0.0)
        return calc_sade_sati(moon_long, sat_long)

    @property
    def dasha_systems(self):
        """All 15 dasha systems from rules.md §4."""
        if self._dasha_systems is None:
            from ..computations.rasi_dashas import calc_all_dasha_systems
            self._dasha_systems = calc_all_dasha_systems(self)
        return self._dasha_systems

    @property
    def sensitive(self):
        """Pranapada, Pushkara, 64th Nav, 22nd Drekkana, Nava-Tara, Ayurdaya."""
        if self._sensitive is None:
            from ..computations.sensitive import calc_sensitive_bundle
            self._sensitive = calc_sensitive_bundle(self)
        return self._sensitive

    @property
    def pranapada(self):
        return self.sensitive["pranapada"]

    @property
    def pushkara(self):
        return self.sensitive["pushkara"]

    @property
    def nava_tara(self):
        return self.sensitive["nava_tara"]

    @property
    def bhavat_bhavam(self):
        return self.sensitive["bhavat_bhavam"]

    @property
    def ayurdaya(self):
        return self.sensitive["ayurdaya"]

    @property
    def grahan(self):
        return self.sensitive["grahan"]

    @property
    def sahams(self):
        return self.special_points.get("sahams", {})

    @property
    def nadi(self):
        if self._nadi is None:
            from ..computations.nadi import calc_nadi
            self._nadi = calc_nadi(self)
        return self._nadi

    @property
    def lal_kitab(self):
        if self._lal_kitab is None:
            from ..computations.lal_kitab import calc_lal_kitab
            self._lal_kitab = calc_lal_kitab(self)
        return self._lal_kitab

    @property
    def jagradadi(self):
        if self._jagradadi is None:
            from ..computations.shadbala import get_jagradadi
            self._jagradadi = get_jagradadi(self)
        return self._jagradadi

    @property
    def deeptadi(self):
        if self._deeptadi is None:
            from ..computations.shadbala import get_deeptadi
            self._deeptadi = get_deeptadi(self)
        return self._deeptadi

    def marriage_timing(self, date=None):
        from ..computations.timing import calc_marriage_timing
        return calc_marriage_timing(self, date)

    def dasha_lord_strength(self, lord):
        from ..computations.rasi_dashas import dasha_lord_strength
        return dasha_lord_strength(self, lord)

    # ═══════════════════════════════════════════
    # Phase 2 — Jaimini + Special
    # ═══════════════════════════════════════════

    @property
    def karakas(self):
        """7-planet Chara Karakas (KN Rao scheme). Computed on first access."""
        if self._karakas_7 is None:
            from ..computations.karakas import calc_chara_karakas_7
            self._karakas_7 = calc_chara_karakas_7(self.positions)
        return self._karakas_7

    @property
    def karakas_8(self):
        """8-planet Chara Karakas (incl. Rahu). Computed on first access."""
        if self._karakas_8 is None:
            from ..computations.karakas import calc_chara_karakas_8
            self._karakas_8 = calc_chara_karakas_8(self.positions)
        return self._karakas_8

    @property
    def karakamsa(self):
        """Karakamsa sign (AK's Navamsa). Computed on first access."""
        from ..computations.karakas import get_karakamsa
        return get_karakamsa(self.positions, self.karakas)

    @property
    def arudhas(self):
        """All 12 Arudha Padas (A1-A12). Computed on first access."""
        if self._arudhas is None:
            from ..computations.arudhas import calc_all_arudhas
            self._arudhas = calc_all_arudhas(self)
        return self._arudhas

    @property
    def graha_arudhas(self):
        """Arudha of the sign each graha occupies. rules.md §7.3."""
        if self._graha_arudhas is None:
            from ..computations.arudhas import calc_graha_arudhas
            self._graha_arudhas = calc_graha_arudhas(self)
        return self._graha_arudhas

    @property
    def special_points(self):
        """Yogi/BB/Sahams/Fortuna. Computed on first access."""
        if self._special_points is None:
            from ..computations.special_points import calc_all_special_points
            self._special_points = calc_all_special_points(self)
        return self._special_points

    @property
    def sensitive_points_bundle(self):
        """Pranapada, Pushkara, 64th Navamsa, 22nd Drekkana, Gandanta & Sandhis (rules.md §15, §24, §33)."""
        if self._sensitive is None:
            from ..computations.sensitive import calc_sensitive_bundle
            self._sensitive = calc_sensitive_bundle(self)
        return self._sensitive

    @property
    def sensitive(self):
        """Alias for sensitive_points_bundle."""
        return self.sensitive_points_bundle

    @property
    def yogas(self):
        """All yoga checks (core + nabhasa + raja/dhana/aristha). Computed on first access."""
        if self._yogas is None:
            from ..computations.yogas import check_all_yogas
            self._yogas = check_all_yogas(self)
        return self._yogas

    @property
    def nabhasa_yogas(self):
        """32 Nabhasa Yogas (Ashraya, Dala, Akriti, Sankhya). Computed on first access."""
        if self._nabhasa_yogas is None:
            from ..computations.yogas_nabhasa import check_all_nabhasa_yogas
            self._nabhasa_yogas = check_all_nabhasa_yogas(self)
        return self._nabhasa_yogas

    @property
    def raja_yogas_extended(self):
        """Extended Raja/Dhana/Aristha/Sannyasa yogas. Computed on first access."""
        if self._raja_yogas_ext is None:
            from ..computations.yogas_raja import check_all_raja_yogas
            self._raja_yogas_ext = check_all_raja_yogas(self)
        return self._raja_yogas_ext

    @property
    def nakshatra_bundle(self):
        """Nakshatra predictive engine: activation ages, nava-tara, pushkara/mrityu, profiles."""
        if self._nakshatra_bundle is None:
            from ..computations.nakshatra_engine import calc_nakshatra_bundle
            self._nakshatra_bundle = calc_nakshatra_bundle(self)
        return self._nakshatra_bundle

    @property
    def predictions(self):
        """Classical prediction texts from CSV databases. Computed on first access."""
        if self._predictions is None:
            from ..computations.predictions import calc_predictions
            self._predictions = calc_predictions(self)
        return self._predictions

    # ═══════════════════════════════════════════
    # Phase 3 — Transits + Tajika + Matching + Kakshya
    # ═══════════════════════════════════════════

    @property
    def kakshyas(self):
        """Kakshya positions for all natal planets. Computed on first access."""
        if self._kakshyas is None:
            from ..computations.kakshya import calc_natal_kakshyas
            self._kakshyas = calc_natal_kakshyas(self)
        return self._kakshyas

    def transits_for(self, date, time="12:00:00", tz=None):
        """
        Transit snapshot for `date` against this natal. Timezone defaults to
        the native's birth tz — never a hardcoded locale.
        """
        from ..computations.transits import calc_full_transit_report
        tz = tz or self.birth_data.get("tz") or "+00:00"
        return calc_full_transit_report(date, self, time, tz)

    # ═══════════════════════════════════════════
    # Phase 3 — Classical Extensions (BPHS & JHora)
    # ═══════════════════════════════════════════

    @property
    def dhoomadi_upagrahas(self):
        """5 Non-Luminous Upagrahas (Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu). BPHS Ch. 3."""
        if self._dhoomadi_upagrahas is None:
            from ..computations.classical_extensions import calc_dhoomadi_upagrahas
            sun_lon = self.positions.get("Sun", {}).get("longitude", 0.0)
            self._dhoomadi_upagrahas = calc_dhoomadi_upagrahas(sun_lon)
        return self._dhoomadi_upagrahas

    @property
    def fertility_and_longevity_sphutas(self):
        """Beeja, Kshetra, Santhana Tithi, Tri-Sphuta, Chatur-Sphuta, Prana, Deha, Mrityu Sphutas."""
        if self._fertility_sphutas is None:
            from ..computations.classical_extensions import calc_fertility_and_longevity_sphutas
            self._fertility_sphutas = calc_fertility_and_longevity_sphutas(self)
        return self._fertility_sphutas

    @property
    def vaiseshikamsa(self):
        """Vaiseshikamsa dignity scales in Dasa Varga and Shodasa Varga (BPHS Ch. 6)."""
        if self._vaiseshikamsa is None:
            from ..computations.classical_extensions import calc_vaiseshikamsa
            self._vaiseshikamsa = calc_vaiseshikamsa(self)
        return self._vaiseshikamsa

    @property
    def sayanadi_avasthas(self):
        """12 Sayanadi activity avasthas for all 9 planets (BPHS Ch. 45)."""
        if self._sayanadi_avasthas is None:
            from ..computations.classical_extensions import calc_sayanadi_avasthas
            self._sayanadi_avasthas = calc_sayanadi_avasthas(self)
        return self._sayanadi_avasthas

    @property
    def pindayu_ayurdaya(self):
        """Detailed Classical Pindayu longevity with all 3 BPHS reductions."""
        if self._pindayu_ayurdaya is None:
            from ..computations.classical_extensions import calc_pindayu_detailed
            self._pindayu_ayurdaya = calc_pindayu_detailed(self)
        return self._pindayu_ayurdaya

    def sign_ingresses(self, planet, start_date, end_date, step_days=1):
        """Sign-change dates for a planet in [start_date, end_date]."""
        from ..computations.transits import find_sign_ingress
        return find_sign_ingress(
            planet, start_date, end_date,
            ephe_path=getattr(self._ephe, "_ephe_path", None),
            ayanamsha=self.birth_data.get("ayanamsha", "lahiri"),
            step_days=step_days,
            chart=self,
        )

    @property
    def extra_points(self):
        """Indu / Tithi / Viparita / Mrityu lagnas + varga lagna facts."""
        if self._extra_points is None:
            from ..computations.extra_lagnas import calc_extra_points_bundle
            self._extra_points = calc_extra_points_bundle(self)
        return self._extra_points

    @property
    def kp_advanced(self):
        """SSL tables, ABCD matrix, cuspal interlinks, star chains."""
        if self._kp_advanced is None:
            from ..computations.kp import calc_kp_advanced
            self._kp_advanced = calc_kp_advanced(self)
        return self._kp_advanced

    @property
    def raw_layers(self):
        """Vargas-with-degrees, nakshatra depth, ingresses, PD trees, drik."""
        if self._raw_layers is None:
            from ..computations.raw_layers import calc_raw_layers
            self._raw_layers = calc_raw_layers(self)
        return self._raw_layers

    def get_time_pack(self, from_date=None, months=36, tara_years=20, eclipse_years=5):
        """
        Dated calendars (varsha, monthly gochara, eclipses, tara, BB).
        Canonical window is 36 months / 20 tara years / 5 eclipse years so PDF
        and JSON share one compute. Smaller requests reuse a cached superset.
        """
        from datetime import datetime
        if from_date is None:
            from_date = datetime.now().strftime("%Y-%m-%d")
        months = int(months)
        tara_years = int(tara_years)
        eclipse_years = int(eclipse_years)
        key = (from_date, months, tara_years, eclipse_years)
        cached = self._time_pack
        ckey = self._time_pack_key
        if cached is not None and ckey is not None:
            c_from, c_m, c_t, c_e = ckey
            if c_from == from_date and c_m >= months and c_t >= tara_years and c_e >= eclipse_years:
                if (c_m, c_t, c_e) == (months, tara_years, eclipse_years):
                    return cached
                return {
                    "from_date": cached.get("from_date"),
                    "varshaphala": cached.get("varshaphala"),
                    "monthly_gochara": (cached.get("monthly_gochara") or [])[:months],
                    "eclipses": cached.get("eclipses"),
                    "tara_bala_years": {
                        **(cached.get("tara_bala_years") or {}),
                        "years": ((cached.get("tara_bala_years") or {}).get("years") or [])[:tara_years],
                    },
                    "bhrigu_bindu_windows": cached.get("bhrigu_bindu_windows"),
                    "bav_peak_signs": cached.get("bav_peak_signs"),
                }
        from ..computations.time_pack import calc_time_pack
        self._time_pack = calc_time_pack(
            self, from_date=from_date, months=months,
            tara_years=tara_years, eclipse_years=eclipse_years,
        )
        self._time_pack_key = key
        return self._time_pack

    @property
    def time_pack(self):
        """Canonical dated calendars (36 months / 20 tara years / 5 eclipse years)."""
        return self.get_time_pack()

    @property
    def avasthas_complete(self):
        """Complete 4-tier Parashara Avasthas (Baladi, Jagradadi, Deeptadi, Shayanadi)."""
        if self._avasthas_complete is None:
            from ..computations.avasthas import calc_complete_avasthas
            self._avasthas_complete = calc_complete_avasthas(self)
        return self._avasthas_complete

    @property
    def sudarshana_chakra(self):
        """Sudarshana Chakra Dasha (Triple-Lagna yearly and monthly progression). rules.md §27."""
        if self._sudarshana is None:
            from ..computations.sudarshana import calc_sudarshana_chakra_dasha
            self._sudarshana = calc_sudarshana_chakra_dasha(self)
        return self._sudarshana

    @property
    def sarvatobhadra_chakra(self):
        """Sarvatobhadra Chakra 81-grid sensitive points & Vedhas. rules.md §28."""
        if self._sbc is None:
            from ..computations.sbc import calc_sarvatobhadra_chakra
            self._sbc = calc_sarvatobhadra_chakra(self)
        return self._sbc

    @property
    def career_profile(self):
        """Career & Profession analysis (D10, 10L, AmK, gov score). rules.md §29."""
        if self._career is None:
            from ..computations.career import calc_career_profile
            self._career = calc_career_profile(self)
        return self._career

    @property
    def wealth_profile(self):
        """Wealth & Dhana determination (Dhana score, Indu Lagna, SAV ratios). rules.md §30."""
        if self._wealth is None:
            from ..computations.wealth import calc_wealth_profile
            self._wealth = calc_wealth_profile(self)
        return self._wealth

    @property
    def medical_profile(self):
        """Medical astrology & Ayurvedic Tridosha constitution scoring. rules.md §31."""
        if self._medical is None:
            from ..computations.medical import calc_medical_profile
            self._medical = calc_medical_profile(self)
        return self._medical

    def kakshya_timing(self, planet, sign=None):
        """Days per kakshya while `planet` transits a sign (natal sign if omitted)."""
        from ..computations.kakshya import calc_kakshya_timing
        from .constants import SIGN_INDEX
        pos = self.positions.get(planet, {})
        if sign is None:
            sign_idx = pos.get("sign_index", 0)
        elif isinstance(sign, str):
            sign_idx = SIGN_INDEX[sign]
        else:
            sign_idx = int(sign)
        speed = abs(pos.get("speed") or 0) or None
        return calc_kakshya_timing(planet, sign_idx, speed)

    def varshaphala(self, year):
        """
        Build a Tajika Varshaphala (annual chart) for a given year.

        Args:
            year: target year (e.g. 2026)

        Returns:
            dict with varsha_chart, varshesha, tajika_yogas
        """
        if self._varsha_cache is None:
            self._varsha_cache = {}
        year = int(year)
        hit = self._varsha_cache.get(year)
        if hit is not None:
            return hit
        from ..computations.tajika import calc_tajika_analysis
        result = calc_tajika_analysis(
            self.birth_data, year,
            ayanamsha=self.birth_data.get("ayanamsha", "lahiri"),
            natal_sun_long=self.positions["Sun"]["longitude"],
            natal_lagna_idx=self.lagna_index,
            ephe=self._ephe,
        )
        self._varsha_cache[year] = result
        return result

    def match_with(self, other_chart):
        """
        Calculate Ashtakoota Guna Milan with another chart.

        Args:
            other_chart: another BirthChart object

        Returns:
            dict with ashtakoota scores, manglik comparison
        """
        from ..computations.matching import calc_matching_score
        return calc_matching_score(self, other_chart)

    def to_html_report(self, output_path=None, chart_style="north", theme="gold"):
        """
        Generate a publication-grade multi-page A4 print HTML report.

        Args:
            output_path: Optional file path to save the HTML. If None, returns the HTML string.
            chart_style: "north" (Diamond) or "south" (Square)
            theme: "gold", "navy", or "monochrome"

        Returns:
            HTML string or saved file path if output_path provided.
        """
        from ..reports.generator import ReportGenerator
        gen = ReportGenerator()
        if output_path:
            if str(output_path).lower().endswith(".pdf"):
                return gen.save_pdf(self, output_path, chart_style=chart_style, theme=theme)
            return gen.save_html(self, output_path, chart_style=chart_style, theme=theme)
        return gen.generate_html(self, chart_style=chart_style, theme=theme)

    def to_pdf_report(self, output_path=None, chart_style="north", theme="gold"):
        """
        Generate a design-faithful A4 PDF (Chromium print of the HTML report).
        """
        from ..reports.generator import ReportGenerator
        gen = ReportGenerator()
        if output_path is None:
            import os
            name_clean = self.birth_data.get("name", "Kundali").replace(" ", "_")
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
            output_path = os.path.join(output_dir, f"{name_clean}_A4_Report.pdf")
        return gen.save_pdf(self, output_path, chart_style=chart_style, theme=theme)

    def to_synthesis_json(self, output_path=None):
        """Write the natal fact pack used for synthesis (every engine layer)."""
        from ..reports.synthesis import save_synthesis_json, build_synthesis_pack
        if output_path is None:
            return build_synthesis_pack(self)
        return save_synthesis_json(self, output_path)

    def to_advanced_json(self, output_path=None, from_date=None):
        """Write the full raw-calculation sidecar (KP chains + dated calendars)."""
        import os
        from ..reports.synthesis import save_advanced_json, build_advanced_pack
        if output_path is None:
            name_clean = (self.birth_data.get("name") or "Kundali").replace(" ", "_")
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
            output_path = os.path.join(output_dir, f"{name_clean}_A4_Report_advanced.json")
        return save_advanced_json(self, output_path, from_date=from_date)

    # ═══════════════════════════════════════════
    # RASHI CHART
    # ═══════════════════════════════════════════

    def _build_rashi_chart(self):
        """
        Build the complete D1 rashi chart.
        For each planet: house (rashi), lordship, dignity, house lord.
        """
        chart = {}

        for planet in PLANETS_9:
            pos = self.positions.get(planet)
            if not pos:
                continue

            sign = pos["sign"]
            sign_idx = pos["sign_index"]

            # House number (1-12) in rashi chart
            house_rashi = sign_to_house(sign_idx, self.lagna_index)

            # Lordship of this planet
            planet_lordships = []
            for h, lord in self.lordships.items():
                if lord == planet:
                    planet_lordships.append(h)

            # Dignity
            dignity = self._get_dignity(planet, sign, pos.get("degree_in_sign", 0))

            chart[planet] = {
                "sign": sign,
                "house_rashi": house_rashi,
                "longitude": pos["longitude"],
                "degree_in_sign": pos["degree_in_sign"],
                "dms": pos["dms"],
                "nakshatra": pos["nakshatra"],
                "pada": pos["pada"],
                "nakshatra_lord": pos["nakshatra_lord"],
                "navamsa": pos["navamsa"],
                "retrograde": pos["retrograde"],
                "dignity": dignity,
                "lordship": planet_lordships,
                "lordship_str": "+".join(f"{h}L" for h in sorted(planet_lordships)),
            }

        return chart

    def _get_dignity(self, planet, sign, degree_in_sign=0):
        """
        Determine planet dignity in a given sign.
        Returns: "Exalted", "Debilitated", "Moolatrikona", "Own Sign",
                 "Friendly", "Neutral", "Enemy"
        """
        # Exaltation check
        if planet in EXALTATION and EXALTATION[planet][0] == sign:
            return "Exalted"

        # Debilitation check
        if planet in DEBILITATION and DEBILITATION[planet][0] == sign:
            return "Debilitated"

        # Moolatrikona check (before own sign — MT is a subset of own)
        if planet in MOOLATRIKONA:
            mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
            if sign == mt_sign and mt_start <= degree_in_sign < mt_end:
                return "Moolatrikona"

        # Own sign check
        if planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
            return "Own Sign"

        # Friendship check
        sign_lord = SIGN_LORDS[sign]
        if planet == sign_lord:
            return "Own Sign"

        if planet in NATURAL_FRIENDS and sign_lord in NATURAL_FRIENDS[planet]:
            return "Friendly"

        if planet in NATURAL_ENEMIES and sign_lord in NATURAL_ENEMIES[planet]:
            return "Enemy"

        return "Neutral"

    # ═══════════════════════════════════════════
    # CHALIT (BHAVA) CHART
    # ═══════════════════════════════════════════

    def _build_chalit_chart(self):
        """
        Build Chalit (Bhava) chart.

        Two equal-house conventions, both from this native's Ascendant:

        * **Cusp / KP-equal** (`house_chalit_cusp`): each house STARTS at the
          lagna degree in successive signs. Planets earlier than that degree
          fall in the previous bhava.
        * **Madhya / Sripati-equal** (`house_chalit_madhya`): lagna is the
          *midpoint*; house starts 15° before ASC. Planets past that border
          go forward.

        Reported `house_chalit` uses a cusp-shift if present, else a madhya-shift.
        """
        asc_long = self.positions["Lagna"]["longitude"]
        chalit = {}

        for planet in PLANETS_9:
            pos = self.positions.get(planet)
            if not pos:
                continue

            p_long = pos["longitude"]
            offset = (p_long - asc_long + 360) % 360

            # Equal houses starting at this native's ASC degree
            house_cusp = int(offset / 30) + 1
            if house_cusp > 12:
                house_cusp = 12

            # Equal houses with ASC as bhava madhya (ASC − 15°)
            adjusted = (offset + 15) % 360
            house_madhya = int(adjusted / 30) + 1
            if house_madhya > 12:
                house_madhya = 12

            rashi_house = self.rashi_chart[planet]["house_rashi"]
            shifted_cusp = house_cusp != rashi_house
            shifted_madhya = house_madhya != rashi_house
            if shifted_cusp:
                house_chalit = house_cusp
            elif shifted_madhya:
                house_chalit = house_madhya
            else:
                house_chalit = rashi_house

            past_cusp = offset - (house_cusp - 1) * 30
            past_madhya = adjusted - (house_madhya - 1) * 30
            shifted = house_chalit != rashi_house

            chalit[planet] = {
                "house_chalit": house_chalit,
                "house_chalit_cusp": house_cusp,
                "house_chalit_madhya": house_madhya,
                "house_rashi": rashi_house,
                "shifted": shifted,
                "shift_description": (
                    f"{rashi_house}H to {house_chalit}H" if shifted else "No shift"
                ),
                "past_boundary_deg": round(
                    past_cusp if shifted_cusp else past_madhya, 2
                ) if shifted else None,
            }

        return chalit

    # ═══════════════════════════════════════════
    # ASPECTS (Graha Drishti)
    # ═══════════════════════════════════════════

    def _compute_aspects(self):
        """
        Compute all Parashari aspects (graha drishti).
        Every planet aspects the 7th house from it.
        Mars, Jupiter, Saturn, Rahu, Ketu have special aspects.
        
        Returns: dict of planet -> list of houses aspected
        """
        aspects = {}

        for planet in PLANETS_9:
            if planet not in self.rashi_chart:
                continue

            house = self.rashi_chart[planet]["house_rashi"]
            aspected_houses = []

            aspected_houses.append(house_counted_from(house, 7))
            if planet in SPECIAL_ASPECTS:
                for offset in SPECIAL_ASPECTS[planet]:
                    aspected_houses.append(house_counted_from(house, offset))

            aspects[planet] = sorted(set(aspected_houses))

        return aspects

    def get_planets_in_house(self, house_num, chart_type="rashi"):
        """Return list of planets in a given house (1-12)."""
        result = []
        for planet in PLANETS_9:
            if chart_type == "rashi":
                if self.rashi_chart.get(planet, {}).get("house_rashi") == house_num:
                    result.append(planet)
            elif chart_type == "chalit":
                if self.chalit_chart.get(planet, {}).get("house_chalit") == house_num:
                    result.append(planet)
        return result

    def get_house_lord(self, house_num):
        """Return the lord of a given house."""
        return self.lordships.get(house_num)

    def get_aspects_to_house(self, house_num):
        """Return list of planets aspecting a given house."""
        aspectors = []
        for planet, houses in self.aspects.items():
            if house_num in houses:
                aspectors.append(planet)
        return aspectors

    def get_aspects_to_planet(self, target_planet):
        """Return list of planets aspecting a given planet."""
        if target_planet not in self.rashi_chart:
            return []
        target_house = self.rashi_chart[target_planet]["house_rashi"]
        return [p for p in self.get_aspects_to_house(target_house) if p != target_planet]

    def get_conjunctions(self, planet):
        """Return planets conjunct with the given planet (same rashi house)."""
        if planet not in self.rashi_chart:
            return []
        house = self.rashi_chart[planet]["house_rashi"]
        return [p for p in self.get_planets_in_house(house) if p != planet]

    # ═══════════════════════════════════════════
    # HOUSE MAP (for display / reports)
    # ═══════════════════════════════════════════

    def get_house_map(self, chart_type="rashi"):
        """
        Return a 12-house map: for each house, list of planets and sign.
        
        Returns:
            dict[1..12] -> {sign, lord, planets: [planet_names]}
        """
        house_map = {}
        for h in range(1, 13):
            sign = house_to_sign(h, self.lagna_index)
            planets = self.get_planets_in_house(h, chart_type)
            house_map[h] = {
                "sign": sign,
                "lord": SIGN_LORDS[sign],
                "planets": planets,
            }
        return house_map

    # ═══════════════════════════════════════════
    # SUMMARY / DISPLAY
    # ═══════════════════════════════════════════

    def summary(self):
        """Return a text summary of the chart."""
        lines = []
        lines.append(f"═══ Birth Chart: {self.birth_data['name']} ═══")
        lines.append(f"Date: {self.birth_data['date']}  Time: {self.birth_data['time']}  TZ: {self.birth_data['tz']}")
        lines.append(f"Lat: {self.birth_data['lat']}  Lon: {self.birth_data['lon']}")
        lines.append(f"Lagna: {self.lagna_sign}  Ayanamsha: {self.birth_data['ayanamsha']}")
        lines.append(f"Ayanamsha value: {self.positions.get('_ayanamsha', 'N/A')}°")
        lines.append("")

        lines.append("Planet      Sign         House  Deg        Nakshatra          Pada  R  Dignity")
        lines.append("─" * 95)

        for planet in ["Lagna"] + list(PLANETS_9):
            pos = self.positions.get(planet, {})
            if not pos or planet.startswith("_"):
                continue

            if planet == "Lagna":
                house = 1
                dignity = ""
                retro = ""
                lordship = ""
            else:
                rc = self.rashi_chart.get(planet, {})
                house = rc.get("house_rashi", "?")
                dignity = rc.get("dignity", "")
                retro = "R" if pos.get("retrograde") else ""
                lordship = rc.get("lordship_str", "")

            lines.append(
                f"{planet:<11} {pos.get('sign', '?'):<12} {str(house):>5}  "
                f"{pos.get('dms', '?'):<10} {pos.get('nakshatra', '?'):<18} P{pos.get('pada', '?'):<3} "
                f"{retro:<2} {dignity}"
            )

        lines.append("")
        lines.append("House Map (Rashi):")
        house_map = self.get_house_map("rashi")
        for h in range(1, 13):
            info = house_map[h]
            planets_str = ", ".join(info["planets"]) if info["planets"] else "—"
            lines.append(f"  H{h:>2} {info['sign']:<13} Lord: {info['lord']:<8} Planets: {planets_str}")

        return "\n".join(lines)

    def __repr__(self):
        return f"BirthChart({self.birth_data['name']}, {self.birth_data['date']}, Lagna={self.lagna_sign})"
