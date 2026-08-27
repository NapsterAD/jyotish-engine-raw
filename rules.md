# Jyotish Calculation Engine — Universal Formula Spec (`rules.md`)

This document is the **formula base of the engine**. Every algorithm, constant, and lookup table here is **chart-agnostic**: it takes civil inputs — date, time, timezone, latitude, longitude — and produces results for **that** native (or query moment). The same functions run for every birth; nothing in a formula is hard-wired to one person.

```python
from jyotish_engine.main import JyotishEngine
engine = JyotishEngine()   # True Chitrapaksha; Swiss .se1 if present on disk
chart  = engine.compute(date, time, tz, lat, lon, name="")
# date "YYYY-MM-DD", time "HH:MM:SS", tz "+05:30", lat/lon floats
```

**What is a formula vs an example.** Algorithms, orbs, year-lengths, BAV contribution lists, KP sub-arc proportions, Badhaka house-by-modality, Jaimini rashi-drishti, Tithi/Karana/Yoga floors, Sade-Sati ±1 sign — these are the spec. Numeric rows labelled *Worked example* (historically Aditya Prasad, 2000-10-06 07:02:21 IST, Katrasgarh) are **verification only**. Never substitute an example table for the algorithm. COMBINED / JHora dumps lock one chart; they are not this file.

Cross-check classical sources: *Brihat Parashara Hora Shastra*, *Jaimini Upadesha Sutras*, *Tajika Neelakanthi*, *Phaladeepika*, *Saravali*, *Prasna Marga*; software: Jagannatha Hora, Swiss Ephemeris.

---

## Table of Contents
1. [Software Libraries & Astronomical Architecture](#1-software-libraries--astronomical-architecture)
2. [Core Constants, Signs, Nakshatras & Dignities](#2-core-constants-signs-nakshatras--dignities)
3. [Divisional Charts (Vargas D1 to D60)](#3-divisional-charts-vargas-d1-to-d60)
4. [Dasha Calculation Systems (15 Systems: Vimshottari, Tribhagi, Yogini, Chara, Narayana, Mandook, Shashti-Hayani, Sudasa, Ashtottari, Kalachakra, Moola, Lagna Kendradi, Drigdasa, Shoola, Niryana Shoola)](#4-dasha-calculation-systems-15-systems)
5. [Ashtakavarga System (BAV, SAV, Shodhana & Pindas)](#5-ashtakavarga-system-bav-sav-shodhana--pindas)
6. [Shadbala & Planetary Strengths](#6-shadbala--planetary-strengths)
7. [Jaimini Astrology (Chara Karakas, Karakamsa & Arudha Padas)](#7-jaimini-astrology-chara-karakas-karakamsa--arudha-padas)
8. [Special Sensitive Points & Sahams](#8-special-sensitive-points--sahams)
9. [Yoga Detection Engine](#9-yoga-detection-engine)
10. [Transit Engine & Gochara with Vedha](#10-transit-engine--gochara-with-vedha)
11. [Tajika Varshaphala (Annual Horoscopy)](#11-tajika-varshaphala-annual-horoscopy)
12. [Kundali Matching (Ashtakoota Guna Milan)](#12-kundali-matching-ashtakoota-guna-milan)
13. [Kakshya Sub-division System](#13-kakshya-sub-division-system)
14. [Panchang Elements — Computation](#14-panchang-elements--computation)
15. [Pranapada (Vitality Point) — Computation Formula](#15-pranapada-vitality-point--computation-formula)
16. [Extended Sahams (Arabic Parts / Tajika)](#16-extended-sahams-arabic-parts--tajika)
17. [Manglik / Kuja Dosha — Complete Detection Algorithm](#17-manglik--kuja-dosha--complete-detection-algorithm)
18. [Bhavat Bhavam — Computation Rule](#18-bhavat-bhavam--computation-rule)
19. [Marriage Timing — Conditional Rules](#19-marriage-timing--conditional-rules)
20. [Longevity (Ayurdaya) — Classification Algorithm](#20-longevity-ayurdaya--classification-algorithm)
21. [Krishnamurti Paddhati (KP System) — Calculation Engine](#21-krishnamurti-paddhati-kp-system--calculation-engine)
22. [Nadi Astrology Rules (Bhrigu Nandi Nadi)](#22-nadi-astrology-rules-bhrigu-nandi-nadi)
23. [Lal Kitab Calculation Rules](#23-lal-kitab-calculation-rules)
24. [Navamsa, Pushkara Navamsa & Sensitive Points (CS Patel Standards)](#24-navamsa-pushkara-navamsa--sensitive-points-cs-patel-standards)
25. [Nakshatra-Level Predictive Algorithms & Activation Ages](#25-nakshatra-level-predictive-algorithms--activation-ages)
26. [Rahu-Ketu Axis & Eclipse Calculation Rules](#26-rahu-ketu-axis--eclipse-calculation-rules)
27. [Sudarshana Chakra Dasha — Triple-Lagna Progression](#27-sudarshana-chakra-dasha--triple-lagna-progression)
28. [Sarvatobhadra Chakra (SBC) — Transit Grid Engine](#28-sarvatobhadra-chakra-sbc--transit-grid-engine)
29. [Career & Profession Determination — Computation Algorithm](#29-career--profession-determination--computation-algorithm)
30. [Wealth & Dhana Determination — Computation Algorithm](#30-wealth--dhana-determination--computation-algorithm)
31. [Medical Astrology — Planet-Disease Mapping & Health Trigger Rules](#31-medical-astrology--planet-disease-mapping--health-trigger-rules)
32. [Muhurtha Essentials — Electional Computation Rules](#32-muhurtha-essentials--electional-computation-rules)
33. [Gandanta, Nakshatra Sandhi & Abhukta Moola — Computation Rules](#33-gandanta-nakshatra-sandhi--abhukta-moola--computation-rules)

---

## 1. Software Libraries & Astronomical Architecture

### 1.1 Installed Libraries
- **`pyswisseph` (`swisseph`)**: Python C-extension binding for the Swiss Ephemeris (Astro-Dienst Zurich).
  - High-precision planetary coordinates (Sun through Saturn, Rahu, Ketu).
  - Sidereal house cusps and Ascendant (`swe.houses_ex`).
  - Julian Day calculation (`swe.julday`, `swe.revjul`).
  - Ayanamsha computation (`swe.get_ayanamsa_ut`).
  - Sunrise, sunset, and solar/lunar phenomena (`swe.rise_trans`).
- **Standard Python 3.10+ Libraries**:
  - `math`: Trigonometric functions, arc conversions, square roots.
  - `datetime`, `timedelta`, `timezone`, `zoneinfo`: Local-to-UT time conversion, IANA zones.
  - `tzdata`: IANA timezone database (required on Windows so `America/New_York` resolves; `pip install tzdata`).
  - `re`: Regular expressions for parsing coordinates, degrees, and timezones.
  - `json`: Ground truth loading, data export.
  - `os`, `sys`: System paths and environment handling.

### 1.2 Ephemeris Modes & Offline Operation
- **100% Offline**: No network calls or API dependencies during runtime.
- **Swiss Ephemeris `.se1` Files**: High precision (when present in `data/ephe`, `C:\sweph\ephe`, or `~/sweph/ephe`).
- **Moshier Semi-Analytic Ephemeris**: Built-in Swiss Ephemeris fallback when `.se1` files are not on disk (valid 3000 BC to 3000 AD; within arc-seconds of JPL DE431).

### 1.3 Time & Coordinate Systems
- **Ayanamsha (engine default)**: `"lahiri"` maps to **True Chitrapaksha** (`swe.SIDM_TRUE_CITRA`, Spica at $180^\circ$). Official IAU Lahiri is `ayanamsha="lahiri_official"` (`swe.SIDM_LAHIRI`). Also: Raman, Krishnamurti / KP (`swe.SIDM_KRISHNAMURTI`), Yukteshwar. Pass `ayanamsha=` on `JyotishEngine(...)` for any native.
- **Sunrise / sunset**: Swiss `rise_trans` with **disc center + no refraction** (geometric sunrise). Used for day/night, special lagnas, Maandi/Gulika, Hora. Always computed at the native’s lat/lon and civil date. If the civil date has no rise or set (polar day/night), search adjacent days for the last/next real event (up to ±366 days) and flag `polar_estimated`. Do **not** invent noon±6h except as a last-resort placeholder when Swiss finds nothing in that window.
- **Coordinate Conversion** (any civil clock):
  $$\text{UT Hour} = \text{Hour} + \frac{\text{Minute}}{60} + \frac{\text{Second}}{3600} - \text{TZ Offset}$$
  $$\text{Julian Day} = \text{swe.julday}(\text{Year}, \text{Month}, \text{Day}, \text{UT Hour})$$
- **Rahu / Ketu Protocol**:
  - Rahu = Mean Node (`swe.MEAN_NODE`; `swe.TRUE_NODE` optional). Engine default is **mean**.
  - Ketu longitude $= (\lambda_{\text{Rahu}} + 180^\circ) \pmod{360^\circ}$.
  - Ketu latitude $= -\beta_{\text{Rahu}}$.
  - **Same mean motion**: $\mathrm{d}\lambda_{\text{Ketu}}/\mathrm{d}t = \mathrm{d}\lambda_{\text{Rahu}}/\mathrm{d}t$ (both $\approx -0.053^\circ/\text{day}$). Do **not** negate Rahu’s Swiss speed for Ketu — that would mark Ketu Direct.
  - `is_retrograde` is **True** for both mean nodes (rules.md §2.9). True node may station/direct briefly; the engine does not use that as default.
- **House Systems** (all from that native’s $\lambda_{\text{ASC}}$):
  - **Rashi**: whole-sign houses from Lagna (sign of Lagna = 1H).
  - **Chalit (two equal conventions, both stored)**:
    1. *Cusp / KP-equal*: house $H$ starts at $\lambda_{\text{ASC}} + 30^\circ(H-1)$ (same degree-in-sign as Lagna in each successive sign). A planet with $\lambda_P$ earlier than that cusp falls in the previous bhava.
    2. *Madhya / Sripati-equal*: Lagna is house-1 midpoint; cusp at $\text{ASC}-15^\circ$. A planet past that border falls in the next bhava.
    3. Reported `house_chalit` uses a cusp-shift if present, else a madhya-shift (hybrid of the two equal conventions).
  - **Placidus** (`b'P'`): KP house cusps (`get_house_cusps`) from Swiss `houses_ex` at the native’s lat/lon.
- **Special lagnas** (from Sun at sunrise; $t$ = hours after sunrise):
  - Bhava Lagna $= \lambda_{\text{Sun,rise}} + 15^\circ t$
  - Hora Lagna $= \lambda_{\text{Sun,rise}} + 30^\circ t$
  - Ghati Lagna $= \lambda_{\text{Sun,rise}} + 75^\circ t$
  - Vighati Lagna $= \lambda_{\text{Sun,rise}} + 4500^\circ t$
  - Sree Lagna $= \lambda_{\text{ASC}} + \frac{\lambda_{\text{Moon}} \bmod 13^\circ20'}{13^\circ20'} \times 360^\circ$
  - Varnada sign $= (S_{\text{ASC}} + S_{\text{HL}} + 1) \bmod 12$, degree $=$ Lagna degree-in-sign
  - Maandi / Gulika: Saturn’s 1/8 of daytime (weekday table in §8), longitude = ASC at that JD.

### 1.4 Engine knobs (any native)
Every civil chart is fully determined by these parameters. Defaults are engine-wide; override on `JyotishEngine(...)` / `compute(...)`. Do not mix knobs inside one chart.

| Knob | Default | Valid range | Affects |
|:---|:---|:---|:---|
| `date`, `time` | required | civil ISO | Lagna degree, all longitudes |
| `tz` | required | `±HH:MM`, `UTC`/`Z`/`GMT`, `IST`, IANA (`America/New_York`) | UT / JD; 1 h error ≈ 15° Lagna. **Unparseable tz raises** — never silently becomes IST. IANA on Windows needs `tzdata`. |
| `lat`, `lon` | required | degrees | houses, sunrise, special lagnas |
| `ayanamsha` | `"lahiri"` = True Chitrapaksha | `lahiri`, `lahiri_official`, `raman`, `krishnamurti`, `yukteshwar` | every sidereal λ |
| Node | **mean** Rahu (`MEAN_NODE`) | mean (default) / true optional | Rahu/Ketu sign & speed |
| Rashi houses | whole-sign from Lagna | always on | `house_rashi`, yogas, SAV-by-house |
| Chalit | dual equal (cusp + madhya) | stored both | `house_chalit` |
| KP cusps | Placidus `b'P'` | Swiss `houses_ex`; **Equal fallback** if `|lat|≥66°` (Placidus undefined) | CSL, ABCD |
| Vimshottari year | sidereal year days in `dashas.py` | not tropical 365.25 | MD/AD/PD dates |
| Sunrise | disc center, **no refraction** | Swiss `rise_trans`; polar → last/next real event, `polar_estimated` | day/night, hora, Gulika |
| Vargas D3 | Parashara 0/10/20 → S, S+4, S+8 | §3 | drekkana |
| Vargas D30 | engine floor (locked Mars=Gemini on Aditya) | §3 | trimsamsa |
| Chara karakas | 7-planet KN Rao + 8-planet with Rahu 30° rule | both stored | PK/PiK |

Lagna-dependent vs independent outputs: §2.12.

---

## 2. Core Constants, Signs, Nakshatras & Dignities

### 2.1 The 12 Signs (Rashis)
| Index | Sign | Lord | Element | Modality | Gender | Body Part |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | Aries (Mesha) | Mars | Fire | Movable (Chara) | Male / Odd | Head |
| 1 | Taurus (Vrishabha) | Venus | Earth | Fixed (Sthira) | Female / Even | Face/Throat |
| 2 | Gemini (Mithuna) | Mercury | Air | Dual (Dvisvabhava) | Male / Odd | Arms/Shoulders |
| 3 | Cancer (Karkata) | Moon | Water | Movable (Chara) | Female / Even | Chest/Heart |
| 4 | Leo (Simha) | Sun | Fire | Fixed (Sthira) | Male / Odd | Stomach |
| 5 | Virgo (Kanya) | Mercury | Earth | Dual (Dvisvabhava) | Female / Even | Intestines |
| 6 | Libra (Tula) | Venus | Air | Movable (Chara) | Male / Odd | Lower abdomen |
| 7 | Scorpio (Vrishchika) | Mars | Water | Fixed (Sthira) | Female / Even | Genitals |
| 8 | Sagittarius (Dhanu) | Jupiter | Fire | Dual (Dvisvabhava) | Male / Odd | Thighs |
| 9 | Capricorn (Makara) | Saturn | Earth | Movable (Chara) | Female / Even | Knees |
| 10 | Aquarius (Kumbha) | Saturn | Air | Fixed (Sthira) | Male / Odd | Calves/Ankles |
| 11 | Pisces (Meena) | Jupiter | Water | Dual (Dvisvabhava) | Female / Even | Feet |

### 2.2 The 27 Nakshatras
- Each Nakshatra spans $13^\circ 20' = \frac{360^\circ}{27} = 13.3333^\circ$.
- Each Pada (Quarter) spans $3^\circ 20' = \frac{13^\circ 20'}{4} = 3.3333^\circ$.

| # | Nakshatra | Span | Lord | Deity | Gana | Yoni | Nadi |
|:---:|:---|:---:|:---:|:---|:---:|:---:|:---:|
| 1 | Ashwini | 00°00' - 13°20' Aries | Ketu | Ashwini Kumaras | Deva | Horse | Aadi (Vata) |
| 2 | Bharani | 13°20' - 26°40' Aries | Venus | Yama | Manushya | Elephant | Madhya (Pitta) |
| 3 | Krittika | 26°40' Ari - 10°00' Tau | Sun | Agni | Rakshasa | Sheep | Antya (Kapha) |
| 4 | Rohini | 10°00' - 23°20' Taurus | Moon | Brahma | Manushya | Serpent | Antya (Kapha) |
| 5 | Mrigashira | 23°20' Tau - 06°40' Gem | Mars | Soma | Deva | Serpent | Madhya (Pitta) |
| 6 | Ardra | 06°40' - 20°00' Gemini | Rahu | Rudra | Manushya | Dog | Aadi (Vata) |
| 7 | Punarvasu | 20°00' Gem - 03°20' Can | Jupiter | Aditi | Deva | Cat | Aadi (Vata) |
| 8 | Pushya | 03°20' - 16°40' Cancer | Saturn | Brihaspati | Deva | Sheep | Madhya (Pitta) |
| 9 | Ashlesha | 16°40' - 30°00' Cancer | Mercury | Nagas | Rakshasa | Cat | Antya (Kapha) |
| 10 | Magha | 00°00' - 13°20' Leo | Ketu | Pitris | Rakshasa | Rat | Aadi (Vata) |
| 11 | Purva Phalguni | 13°20' - 26°40' Leo | Venus | Bhaga | Manushya | Rat | Madhya (Pitta) |
| 12 | Uttara Phalguni | 26°40' Leo - 10°00' Vir | Sun | Aryaman | Manushya | Cow | Antya (Kapha) |
| 13 | Hasta | 10°00' - 23°20' Virgo | Moon | Savitr | Deva | Buffalo | Antya (Kapha) |
| 14 | Chitra | 23°20' Vir - 06°40' Lib | Mars | Tvashtr | Rakshasa | Tiger | Madhya (Pitta) |
| 15 | Swati | 06°40' - 20°00' Libra | Rahu | Vayu | Deva | Buffalo | Aadi (Vata) |
| 16 | Vishakha | 20°00' Lib - 03°20' Sco | Jupiter | Indra-Agni | Rakshasa | Tiger | Aadi (Vata) |
| 17 | Anuradha | 03°20' - 16°40' Scorpio | Saturn | Mitra | Deva | Deer | Madhya (Pitta) |
| 18 | Jyeshtha | 16°40' - 30°00' Scorpio | Mercury | Indra | Rakshasa | Deer | Antya (Kapha) |
| 19 | Moola | 00°00' - 13°20' Sgr | Ketu | Nirrti | Rakshasa | Dog | Aadi (Vata) |
| 20 | Purva Ashadha | 13°20' - 26°40' Sgr | Venus | Apas | Manushya | Monkey | Madhya (Pitta) |
| 21 | Uttara Ashadha | 26°40' Sgr - 10°00' Cap | Sun | Vishvedevas | Manushya | Mongoose | Antya (Kapha) |
| 22 | Shravana | 10°00' - 23°20' Cap | Moon | Vishnu | Deva | Monkey | Antya (Kapha) |
| 23 | Dhanishtha | 23°20' Cap - 06°40' Aqu | Mars | Vasus | Rakshasa | Lion | Madhya (Pitta) |
| 24 | Shatabhisha | 06°40' - 20°00' Aquarius | Rahu | Varuna | Rakshasa | Horse | Aadi (Vata) |
| 25 | Purva Bhadrapada | 20°00' Aqu - 03°20' Psc | Jupiter | Aja Ekapada | Manushya | Lion | Aadi (Vata) |
| 26 | Uttara Bhadrapada | 03°20' - 16°40' Pisces | Saturn | Ahir Budhnya | Manushya | Cow | Madhya (Pitta) |
| 27 | Revati | 16°40' - 30°00' Pisces | Mercury | Pushan | Deva | Elephant | Antya (Kapha) |

### 2.3 Planetary Dignities Table
| Planet | Exaltation Sign (Deep Deg) | Debilitation Sign (Deep Deg) | Moolatrikona Range | Own Signs (Swakshetra) |
|:---|:---:|:---:|:---:|:---|
| **Sun** | Aries ($10^\circ$) | Libra ($10^\circ$) | Leo $0^\circ - 20^\circ$ | Leo |
| **Moon** | Taurus ($3^\circ$) | Scorpio ($3^\circ$) | Taurus $3^\circ - 30^\circ$ | Cancer |
| **Mars** | Capricorn ($28^\circ$) | Cancer ($28^\circ$) | Aries $0^\circ - 12^\circ$ | Aries, Scorpio |
| **Mercury** | Virgo ($15^\circ$) | Pisces ($15^\circ$) | Virgo $15^\circ - 20^\circ$ | Gemini, Virgo |
| **Jupiter** | Cancer ($5^\circ$) | Capricorn ($5^\circ$) | Sagittarius $0^\circ - 10^\circ$ | Sagittarius, Pisces |
| **Venus** | Pisces ($27^\circ$) | Virgo ($27^\circ$) | Libra $0^\circ - 15^\circ$ | Taurus, Libra |
| **Saturn** | Libra ($20^\circ$) | Aries ($20^\circ$) | Aquarius $0^\circ - 20^\circ$ | Capricorn, Aquarius |
| **Rahu** | Taurus ($20^\circ$) | Scorpio ($20^\circ$) | Gemini / Virgo | Aquarius |
| **Ketu** | Scorpio ($20^\circ$) | Taurus ($20^\circ$) | Sagittarius / Pisces | Scorpio |

### 2.4 Natural Planetary Relationships (Naisargika Maitri)
| Planet | Natural Friends (Mitra) | Natural Neutrals (Sama) | Natural Enemies (Satru) |
|:---|:---|:---|:---|
| **Sun** | Moon, Mars, Jupiter | Mercury | Venus, Saturn |
| **Moon** | Sun, Mercury | Mars, Jupiter, Venus, Saturn | *(None)* |
| **Mars** | Sun, Moon, Jupiter | Venus, Saturn | Mercury |
| **Mercury** | Sun, Venus | Mars, Jupiter, Saturn | Moon |
| **Jupiter** | Sun, Moon, Mars | Saturn | Mercury, Venus |
| **Venus** | Mercury, Saturn | Mars, Jupiter | Sun, Moon |
| **Saturn** | Mercury, Venus | Jupiter | Sun, Moon, Mars |

### 2.5 Parashari Graha Drishti (Aspects)
- **Universal Aspect**: Every planet aspects the $7^\text{th}$ house ($180^\circ$) from its position with 100% full sight.
- **Special Full Aspects**:
  - **Mars**: Aspects $4^\text{th}$ and $8^\text{th}$ houses from its position.
  - **Jupiter**: Aspects $5^\text{th}$ and $9^\text{th}$ houses from its position.
  - **Saturn**: Aspects $3^\text{rd}$ and $10^\text{th}$ houses from its position.
  - **Rahu / Ketu**: Aspect $5^\text{th}$ and $9^\text{th}$ houses (per classical Parashara school).

### 2.6 House Classifications & Purushartha Trikonas (The 4 Trines)

Every chart is divided into 4 fundamental **Purushartha Trikonas** (Triangular Life Aim Quadrants) and classical geometric groups:

```
                  [ 10th House (Karma/Artha) ]
                                |
[ 1st House (Dharma) ] ---- Kendra Axis ---- [ 7th House (Kama) ]
                                |
                   [ 4th House (Moksha) ]
```

#### 2.6.1 The 4 Purushartha House Trines (Trikonas)
| Trikona (Trine) | Houses | Element | Life Domain (Purushartha) | Inherent Nature & Strength |
|:---|:---:|:---:|:---|:---|
| **Dharma Trikona** | **1, 5, 9** | Fire (Agni) | Righteousness, Soul Purpose, Past Merit, Wisdom | **Lakshmi Sthanas**: Always auspicious. Lords are functional benefics. |
| **Artha Trikona** | **2, 6, 10** | Earth (Prithvi) | Wealth, Material Resources, Service/Work, Career | Professional & financial manifestation engine. |
| **Kama Trikona** | **3, 7, 11** | Air (Vayu) | Desires, Relationships, Enterprise, Networking, Gains | Ambition & fulfillment of worldly pursuits. |
| **Moksha Trikona** | **4, 8, 12** | Water (Jala) | Inner Peace, Occult Transformation, Detachment, Liberation | Subconscious, spiritual elevation & final emancipation. |

#### 2.6.2 The 4 Elemental Sign Trines (Rasi Trikonas)
| Element | Signs (0-Indexed) | Signs (Names) | Direction (Nadi) | Modality Breakdown |
|:---|:---:|:---|:---:|:---|
| **Agni (Fire)** | 0, 4, 8 | Aries, Leo, Sagittarius | **East** | Movable (Ar) $\rightarrow$ Fixed (Le) $\rightarrow$ Dual (Sg) |
| **Prithvi (Earth)** | 1, 5, 9 | Taurus, Virgo, Capricorn | **South** | Fixed (Ta) $\rightarrow$ Dual (Vi) $\rightarrow$ Movable (Cp) |
| **Vayu (Air)** | 2, 6, 10 | Gemini, Libra, Aquarius | **West** | Dual (Ge) $\rightarrow$ Movable (Li) $\rightarrow$ Fixed (Aq) |
| **Jala (Water)** | 3, 7, 11 | Cancer, Scorpio, Pisces | **North** | Movable (Cn) $\rightarrow$ Fixed (Sc) $\rightarrow$ Dual (Pi) |

#### 2.6.3 Earth Trine (*Prithvi Trikona* / *Artha Trikona*) — Deep Specification
The Earth Trine governs the **material manifestation engine** (tangible wealth, duty, physical security, executive execution):

1. **House Components (*Artha Bhavas*)**:
   - **2nd House (*Dhana Bhava*)**: Stored capital, liquid assets, food, speech, family lineage.
   - **6th House (*Shatru / Roga / Seva*)**: Problem-solving, daily work routine, overcoming obstacles, debts, competitive stamina.
   - **10th House (*Karma Bhava*)**: Career zenith, public authority, professional status, executive power.
2. **Sign Components (*Prithvi Rasis*)**:
   - **Taurus (Sign 2 — Fixed Earth / *Sthira*)**: Tangible resources, banking, agriculture, values. Karaka: Venus.
   - **Virgo (Sign 6 — Dual Earth / *Dvisvabhava*)**: Analytical processing, accounting, healing, precision craft. Karaka: Mercury.
   - **Capricorn (Sign 10 — Movable Earth / *Chara*)**: Structural ambition, governance, enterprise hierarchies. Karaka: Saturn.
3. **Nakshatra Trinal Symmetry in Earth Signs**:
   - Sun Nakshatras: Krittika (Tau), Uttara Phalguni (Vir), Uttara Ashadha (Cap).
   - Moon Nakshatras: Rohini (Tau), Hasta (Vir), Shravana (Cap).
   - Mars Nakshatras: Mrigashira (Tau), Chitra (Vir), Dhanishta (Cap).
4. **Pushkara Navamsas in Earth Signs**:
   - **3rd Navamsa** ($06^\circ 40' - 10^\circ 00'$): Pisces Navamsa (Jupiter)
   - **5th Navamsa** ($13^\circ 20' - 16^\circ 40'$): Taurus Navamsa (Venus)
5. **Nadi Direction**: **South** ($100\%$ mutual trinal conjunction).

#### 2.6.4 Water Trine (*Jala Trikona* / *Moksha Trikona*) — Deep Specification
The Water Trine governs the **subconscious & spiritual dissolution engine** (emotions, occult depth, psychic intuition, liberation):

1. **House Components (*Moksha Bhavas*)**:
   - **4th House (*Sukha Bhava*)**: Emotional roots, inner peace, mother, vehicles, shelter, psychological sanctuary.
   - **8th House (*Randhra / Ayu*)**: Occult research, unearned wealth, sudden transformations, longevity, deep subconscious alchemy.
   - **12th House (*Vyaya / Moksha*)**: Solitude, foreign lands, sleep/dreams, spiritual surrender, final emancipation.
2. **Sign Components (*Jala Rasis*)**:
   - **Cancer (Sign 4 — Movable Water / *Chara*)**: Flowing river/spring, memory, maternal nurturing, intuitive flow. Karaka: Moon.
   - **Scorpio (Sign 8 — Fixed Water / *Sthira*)**: Deep abyss/stagnant swamp, secrets, occult depth, poison vs. medicine. Karaka: Mars / Ketu.
   - **Pisces (Sign 12 — Dual Water / *Dvisvabhava*)**: Endless cosmic ocean (*Samudra*), dissolution of ego, universal compassion. Karaka: Jupiter.
3. **Nakshatra Trinal Symmetry & Gandanta Points**:
   - Jupiter Nakshatras: Punarvasu (Can), Vishakha (Sco), Purva Bhadrapada (Pis).
   - Saturn Nakshatras: Pushya (Can), Anuradha (Sco), Uttara Bhadrapada (Pis).
   - Mercury Nakshatras: Ashlesha (Can), Jyeshtha (Sco), Revati (Pis) — **All 3 terminate at a Nakshatra Gandanta** ($29^\circ 00' - 01^\circ 00'$).
4. **Pushkara Navamsas in Water Signs**:
   - **1st Navamsa** ($00^\circ 00' - 03^\circ 20'$): Cancer Navamsa (Moon)
   - **3rd Navamsa** ($06^\circ 40' - 10^\circ 00'$): Virgo Navamsa (Mercury)
5. **Nadi Direction**: **North** ($100\%$ mutual trinal conjunction).

#### 2.6.5 Geometric & Functional House Groupings
| Group Name | Houses | Classification Rule & Astrological Function |
|:---|:---:|:---|
| **Kendras (Quadrants / Vishnu Sthanas)** | **1, 4, 7, 10** | Pillars of the chart. $10\text{H} > 1\text{H} > 7\text{H} > 4\text{H}$ in strength. |
| **Trikonas (Trines / Lakshmi Sthanas)** | **1, 5, 9** | Auspicious merit houses. $9\text{H} > 5\text{H} > 1\text{H}$ in benefic capacity. |
| **Panapharas (Succedent Houses)** | **2, 5, 8, 11** | Fixed sustaining houses. Secondary strength ($50\%$). |
| **Apoklimas (Cadent Houses)** | **3, 6, 9, 12** | Flexible, mutable houses. Variable strength ($25\%$). |
| **Upachayas (Growth Houses)** | **3, 6, 10, 11** | Houses of continuous improvement with age and effort. Natural malefics give wealth here. |
| **Apachayas (Non-Growth Houses)** | **1, 2, 4, 7, 8** | Houses where karma is fixed and non-accumulative. |
| **Trishadayas (Material Effort / Friction)** | **3, 6, 11** | Malefic lordships. Produce worldly gains but disturb mental tranquility. |
| **Dusthanas / Trika (Affliction Houses)** | **6, 8, 12** | $8\text{H} > 12\text{H} > 6\text{H}$ in severity. Disease, longevity/crises, expenditure/loss. |
| **Marakas (Death-Inflicting Houses)** | **2, 7** | Primary terminal houses. Lords trigger health crises during dasha/antardasha. |

#### 2.6.6 Functional Nature Classification (Per Lagna)
1. **Trikona Lords (1, 5, 9)**: Always functional benefics for the native.
2. **Kendra Lords (1, 4, 7, 10)**: Subject to *Kendradhipati Dosha* if natural benefics; natural malefics lose evil nature.
3. **Dusthana Lords (6, 8, 12)**: Functional malefics (unless ruling 1st house or forming Viparita Raja Yoga).
4. **Trishadaya Lords (3, 6, 11)**: Functional malefics for spiritual and mental peace.
5. **Yogakaraka**: A single planet owning both a Kendra ($4, 7, 10$) and a Trikona ($5, 9$) simultaneously:
   - Taurus Lagna $\rightarrow$ Saturn ($9\text{L} + 10\text{L}$)
   - Cancer Lagna $\rightarrow$ Mars ($5\text{L} + 10\text{L}$)
   - Leo Lagna $\rightarrow$ Mars ($4\text{L} + 9\text{L}$)
   - Libra Lagna $\rightarrow$ Saturn ($4\text{L} + 5\text{L}$)
   - Capricorn Lagna $\rightarrow$ Venus ($5\text{L} + 10\text{L}$)
   - Aquarius Lagna $\rightarrow$ Venus ($4\text{L} + 9\text{L}$)

### 2.7 Combustion (Asta / Dagdha) — Detection Rules
A planet $P$ is **combust** if $|\\lambda_P - \\lambda_{\\text{Sun}}| \\le \\text{orb}(P, \\text{motion})$.

| Planet | Orb (Direct) | Orb (Retrograde) |
|:---|:---:|:---:|
| Moon | $12°$ | — (Moon does not retrograde) |
| Mars | $17°$ | $17°$ |
| Mercury | $14°$ | $12°$ |
| Jupiter | $11°$ | $11°$ |
| Venus | $10°$ | $8°$ |
| Saturn | $15°$ | $15°$ |

**Source:** Sanjay Rath (*Prashna*), BPHS Ch. 25, Saravali

**Computation Rules:**
1. `is_combust(P) = True` if $|\\lambda_P - \\lambda_{\\text{Sun}}| \\le \\text{orb}(P)$. Use the retrograde orb if `P.is_retrograde = True`.
2. **Rahu, Ketu**: Exempt — never combust (shadow points, no physical body).
3. **Sun**: Cannot be combust. Sun's "combustion" state = solar eclipse: `is_eclipsed(Sun) = True` if $|\\lambda_{\\text{Sun}} - \\lambda_{\\text{Rahu}}| \\le 15°$ (approximate eclipse window).
4. **Combustion severity gradation**:
   - $|\\Delta\\lambda| \\le 3°$ → `state = "FULLY_COMBUST"` (Asta — planet virtually invisible)
   - $3° < |\\Delta\\lambda| \\le 6°$ → `state = "SEVERELY_COMBUST"`
   - $6° < |\\Delta\\lambda| \\le \\text{orb}$ → `state = "MODERATELY_COMBUST"`
5. **Strength reduction**: Combust planet loses its **Sthanabala** contribution and cannot contribute positively to Shadbala. In Shadbala calculation, set `naisargika_bala_modifier = 0` for fully combust planet.
6. **Combustion flag in yoga detection**: If planet is combust AND is a Yogakaraka or Raj Yoga participant, flag the yoga as `yoga_status = "COMBUST_WEAKENED"` rather than cancelling it entirely.
7. **Moon combustion**: Moon within $12°$ of Sun = New Moon phase (`is_combust_moon = True`). Moon's **Paksha Bala** drops to minimum. Cross-reference: Paksha Bala formula in §6 Shadbala.

Engine (any native): `chart.combustion`. Angular separation is the shortest arc, $\min(|\Delta|, 360-|\Delta|)$.

### 2.8 Planetary War (Graha Yuddha) — Detection Algorithm
Two planets $P_1, P_2$ are in **Graha Yuddha** if:
$$|\\lambda_{P_1} - \\lambda_{P_2}| \\le 1° \\quad \\text{AND} \\quad P_1, P_2 \\in \\{\\text{Mars, Mercury, Jupiter, Venus, Saturn}\\}$$

**Winner Determination (Standard — Surya Siddhanta):**
```
winner = planet with HIGHER celestial latitude (|β|)
loser  = planet with LOWER  celestial latitude (|β|)
```
- Requires `swe_calc_ut()` with `SEFLG_TOPOCTR` to get geocentric latitude $\\beta$ for each planet.
- **Alternative rule (Phaladeepika):** Winner = planet with LESSER longitude (i.e., the one "ahead" in the zodiac).

**Strength Modification (engine):**
- Winner: $+60$ Shashtiamsas as **Kala Bala Yuddha** (§6.1).
- Loser: $-60$ Shashtiamsas in the same Kala slot.
- Phaladeepika also describes cutting the loser’s **total Shadbala by $1/3$**. The engine does **not** apply that second pass (it would double-penalize after $\pm 60$). Detection still uses $|\beta|$ then lesser longitude.

**Exclusions:** Sun (causes combustion instead), Moon, Rahu, Ketu are **never** participants in Graha Yuddha.

Engine (any native): `chart.yuddha`. Winner = higher $|\beta|$ when Swiss latitude is present; else Phaladeepika lesser-longitude.

### 2.9 Retrograde (Vakri) — Status Flags & Strength Modifications
A planet $P$ is **retrograde** if its daily motion is negative: $\\frac{d\\lambda_P}{dt} < 0$.

**Strength Rules (for Shadbala):**
1. Cheshta Bala for Mars–Saturn is **Seeghra Kendra / 3** (BPHS, 0–60). Retrograde is **not** forced to 60. Outer vakri grahas sit near opposition, so the kendra is already large. See §6.1.
2. `is_retrograde(P)` for **motion**: Mars, Mercury, Jupiter, Venus, Saturn from $\mathrm{d}\lambda/\mathrm{d}t < 0$. Sun and Moon never retrograde. **Rahu/Ketu (mean node) are always retrograde** — engine stores `retrograde=True` and the same negative $\mathrm{d}\lambda/\mathrm{d}t$ on both (§1.3). Nodes are not given Shadbala Cheshta.

**Conditional State Flags:**
| Condition | Flag |
|:---|:---|
| `P.is_retrograde AND P.is_exalted` | `state = "EXCEPTIONALLY_STRONG"` |
| `P.is_retrograde AND P.is_debilitated` | `state = "DEBILITATION_MITIGATED"` (counts as partial Neecha Bhanga — see §9.6) |
| `P.is_retrograde AND P.is_in_own_sign` | `state = "VERY_STRONG"` |
| `P.is_retrograde AND P.is_combust` | Combustion rules still apply; retrograde does NOT cancel combustion |
| `P.is_natural_benefic AND P.is_retrograde` | `benefic_strength_multiplier = 1.5` (amplified benefic capacity) |
| `P.is_natural_malefic AND P.is_retrograde` | `malefic_strength_multiplier = 1.5` (amplified malefic capacity) |

### 2.10 Partial Aspects (Spashta Drishti — Parashari)
Every planet aspects the 7th house with full strength. Mars, Jupiter, Saturn have special additional full aspects. All planets also cast **partial aspects** used in **Drik Bala** computation:

$$\\text{Drishti\\_Pinda}(P, H) = \\text{base\\_aspect}(\\Delta H) + \\text{special\\_aspect}(P, \\Delta H)$$

where $\\Delta H$ = house count from planet's sign to target sign (1-indexed, CW).

| $\\Delta H$ | Base Aspect | Mars Special | Jupiter Special | Saturn Special |
|:---:|:---:|:---:|:---:|:---:|
| 1 | — | — | — | — |
| 2 | 0 | 0 | 0 | 0 |
| 3 | 15 | 0 | 0 | **45** |
| 4 | 30 | **15** | 0 | 0 |
| 5 | 15 | 0 | **30** | 0 |
| 6 | 0 | 0 | 0 | 0 |
| 7 | **60** | 0 | 0 | 0 |
| 8 | 30 | **15** | 0 | 0 |
| 9 | 15 | 0 | **30** | 0 |
| 10 | 30 | 0 | 0 | **15** |
| 11 | 15 | 0 | 0 | 0 |
| 12 | 0 | 0 | 0 | 0 |

**Total aspect = base + special.** Full aspect ($60$) = $100\\%$. Half aspect ($30$) = $50\\%$. Quarter aspect ($15$) = $25\\%$.
**Source:** BPHS Ch. 26–27, Graha & Bhava Balas (BVR)

House-level yoga detection treats Mars 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th as **full** special aspects (`SPECIAL_ASPECTS`). Engine `calc_drik_bala` and Bhava Drishti Bala use the virupa table above (Spashta Drishti Pinda); benefic aspectors add, malefic aspectors subtract.

**In Graha Drik Bala (§6.1):** use the **degree** spashta table on $\lambda_Q \rightarrow \lambda_P$, then divide the signed sum by 4 (JHora). The whole-sign pinda table above is **Bhava Drishti Bala** only (§6.7).

### 2.11 Badhaka Lords (Badhakesh) — Determination Table
The **Badhaka Sthana** (obstructing house) depends on the Lagna sign's modality:

| Lagna Modality | Badhaka House | Formula |
|:---|:---:|:---|
| **Chara (Movable)**: Ar, Cn, Li, Cp | $11\\text{th}$ house | `badhaka_house = (lagna_idx + 10) % 12` |
| **Sthira (Fixed)**: Ta, Le, Sc, Aq | $9\\text{th}$ house | `badhaka_house = (lagna_idx + 8) % 12` |
| **Dvisvabhava (Dual)**: Ge, Vi, Sg, Pi | $7\\text{th}$ house | `badhaka_house = (lagna_idx + 6) % 12` |

**Badhakesh** = Lord of the Badhaka house. Use standard sign-lordship table from §2.

**Complete Badhakesh Lookup (all 12 Lagnas):**
| Lagna | Type | Badhaka House | Badhakesh |
|:---|:---|:---:|:---|
| Aries | Chara | 11th (Aquarius) | Saturn |
| Taurus | Sthira | 9th (Capricorn) | Saturn |
| Gemini | Dual | 7th (Sagittarius) | Jupiter |
| Cancer | Chara | 11th (Taurus) | Venus |
| Leo | Sthira | 9th (Aries) | Mars |
| Virgo | Dual | 7th (Pisces) | Jupiter |
| Libra | Chara | 11th (Leo) | Sun |
| Scorpio | Sthira | 9th (Cancer) | Moon |
| Sagittarius | Dual | 7th (Gemini) | Mercury |
| Capricorn | Chara | 11th (Scorpio) | Mars |
| Aquarius | Sthira | 9th (Libra) | Venus |
| Pisces | Dual | 7th (Virgo) | Mercury |

**Dual-role Conflict Flag:** If `Badhakesh == Yogakaraka` for a given Lagna, flag `planet.has_badhaka_yogakaraka_conflict = True`. Occurs when the same planet lords a kendra (4/7/10) and a trikona (5/9): Venus for Aquarius Lagna, Saturn for Taurus Lagna, Mars for Leo Lagna. Source: Viveka Chudamani §1.10.2.

Engine (any native): `chart.badhaka` from **this** Lagna’s modality.

### 2.12 Whole-sign house mapping (single source of truth)
Every whole-sign house number in the engine is

$$H(\text{sign}, \text{origin}) = (s_{\text{sign}} - s_{\text{origin}}) \bmod 12 + 1$$
$$s(H, \text{origin}) = (s_{\text{origin}} + H - 1) \bmod 12$$

with $s \in \{0,\ldots,11\}$, $H \in \{1,\ldots,12\}$. Origin is Lagna for rashi houses; Moon for Gochara; a varga lagna for D9/D10 houses. Inverse: $s(H(\text{sign}, L), L) = \text{sign}$.

**Engine:** `jyotish_engine.core.mapping` — `sign_to_house`, `house_to_sign`, `house_counted_from` (7th = count 7), `bhavat_bhavam`, `badhaka_house`. No other module may invent its own `(idx ± n) % 12` house loop.

7th from house $H$: `house_counted_from(H, 7)`. Bhavat-bhavam: `house_counted_from(H, H)`.

**Lagna-dependent** (shift if Lagna sign/degree changes): rashi `house_rashi`, `sav_by_house`, Dig Bala peak house, Bhava Bala, functional nature, yogas, Arudha A1–A12, Sahams using ASC, Badhaka, Bhavat Bhavam, Chalit/KP cusps, varga lagnas, Narayana/Sudasa/Drigdasa/Shoola start sign.

**Special-reference** (not Lagna): Vimshottari/Yogini/Ashtottari (Moon nakshatra); Chara Karakas (degree rank); Sade-Sati (Moon sign); Ghati (sunrise); Pranapada (Sun); Kalachakra savya (Moon pada).

**Lagna-independent:** planetary λ / nakshatra / pada, Sthana (except kendra sub), Naisargika, Cheshta, Ayana/Vara/Masa/Hora, combustion, yuddha, panchang, sunrise/sunset, BAV/SAV **sign-row** (Aries→Pisces). House *labels* on that SAV row rotate; the 12 numbers as a set do not.

**Invariant:** rotating Lagna through all 12 signs with planetary positions frozen must keep `sorted(sav_by_house.values()) == sorted(sav)`. Adjacent houses 12/1/2/3 are the wrap zone. Tests: `test_lagna_mapping.py`.

---

## 3. Divisional Charts (Vargas D1 to D60)

Let $\lambda$ be the sidereal longitude ($0^\circ \le \lambda < 360^\circ$), $S = \lfloor \lambda / 30 \rfloor$ (0-based sign index), and $D = \lambda \pmod{30}$ (degree in sign).

| Varga | Division | Span | Classical Calculation Rule | Significance |
|:---|:---:|:---:|:---|:---|
| **D1** (Rashi) | 1 | $30^\circ 00'$ | $\text{Sign} = S$ | Physical body, general life |
| **D2** (Hora) | 2 | $15^\circ 00'$ | **Odd Sign**: $0-15^\circ \rightarrow$ Leo (Sun), $15-30^\circ \rightarrow$ Cancer (Moon).<br>**Even Sign**: $0-15^\circ \rightarrow$ Cancer (Moon), $15-30^\circ \rightarrow$ Leo (Sun). | Wealth, treasury |
| **D3** (Drekkana) | 3 | $10^\circ 00'$ | $0-10^\circ \rightarrow S$, $10-20^\circ \rightarrow (S + 4) \pmod{12}$, $20-30^\circ \rightarrow (S + 8) \pmod{12}$. | Siblings, courage, vitality |
| **D4** (Chaturthamsha) | 4 | $7^\circ 30'$ | Part $k = \lfloor D / 7.5 \rfloor$. Sign = $(S + 3k) \pmod{12}$ (1st, 4th, 7th, 10th from $S$). | Fixed assets, property, home |
| **D5** (Panchamsha) | 5 | $6^\circ 00'$ | Standard cyclic: $(S \times 5 + \lfloor D / 6 \rfloor) \pmod{12}$. | Spiritual merit, fame |
| **D6** (Shashthamsha) | 6 | $5^\circ 00'$ | Standard cyclic: $(S \times 6 + \lfloor D / 5 \rfloor) \pmod{12}$. | Debts, diseases, litigation |
| **D7** (Saptamsha) | 7 | $4^\circ 17' 08.57''$ | Division $k = \lfloor D / (30/7) \rfloor$.<br>**Odd Sign**: $(S + k) \pmod{12}$.<br>**Even Sign**: $(S + 6 + k) \pmod{12}$ (starts from 7th). | Children, progeny, dynasty |
| **D8** (Ashtamsha) | 8 | $3^\circ 45'$ | Standard cyclic: $(S \times 8 + \lfloor D / 3.75 \rfloor) \pmod{12}$. | Hidden obstacles, longevity |
| **D9** (Navamsa) | 9 | $3^\circ 20'$ | Division $k = \lfloor D / (30/9) \rfloor$.<br>**Fire Signs** (Ari, Leo, Sgr) $\rightarrow$ Starts from Aries ($0 + k$).<br>**Earth Signs** (Tau, Vir, Cap) $\rightarrow$ Starts from Capricorn ($9 + k$).<br>**Air Signs** (Gem, Lib, Aqu) $\rightarrow$ Starts from Libra ($6 + k$).<br>**Water Signs** (Can, Sco, Psc) $\rightarrow$ Starts from Cancer ($3 + k$). | Dharma, marriage, soul destiny |
| **D10** (Dashamsha) | 10 | $3^\circ 00'$ | Division $k = \lfloor D / 3 \rfloor$. JHora / BPHS **modality** map (not odd/even): **Movable** start from $S$; **Fixed** from 9th $(S+8)$; **Dual** from 5th $(S+4)$. Then $(start + k) \bmod 12$. | Career, profession, status |
| **D11** (Rudramsha) | 11 | $2^\circ 43' 38.18''$ | Standard cyclic: $(S \times 11 + \lfloor D / (30/11) \rfloor) \pmod{12}$. | Sudden gains/losses, combat |
| **D12** (Dwadashamsha) | 12 | $2^\circ 30'$ | Division $k = \lfloor D / 2.5 \rfloor$. Sign = $(S + k) \pmod{12}$. | Parents, ancestry |
| **D16** (Shodashamsha) | 16 | $1^\circ 52' 30''$ | Division $k = \lfloor D / (30/16) \rfloor$.<br>**Movable Sign** $\rightarrow$ Starts from Aries ($0 + k$).<br>**Fixed Sign** $\rightarrow$ Starts from Leo ($4 + k$).<br>**Dual Sign** $\rightarrow$ Starts from Sagittarius ($8 + k$). | Vehicles, pleasures, accidents |
| **D20** (Vimsamsha) | 20 | $1^\circ 30'$ | Division $k = \lfloor D / 1.5 \rfloor$.<br>**Movable Sign** $\rightarrow$ Starts from Aries ($0 + k$).<br>**Fixed Sign** $\rightarrow$ Starts from Sagittarius ($8 + k$).<br>**Dual Sign** $\rightarrow$ Starts from Leo ($4 + k$). | Upasana, spiritual progress |
| **D24** (Siddhamsa) | 24 | $1^\circ 15'$ | Division $k = \lfloor D / 1.25 \rfloor$.<br>**Odd Sign**: Starts from Leo ($4 + k$).<br>**Even Sign**: Starts from Cancer ($3 + k$). | Learning, intellect, education |
| **D27** (Nakshatramsha) | 27 | $1^\circ 06' 40''$ | Division $k = \lfloor D / (30/27) \rfloor$.<br>**Fire** $\rightarrow$ Aries ($0+k$), **Earth** $\rightarrow$ Cancer ($3+k$),<br>**Air** $\rightarrow$ Libra ($6+k$), **Water** $\rightarrow$ Capricorn ($9+k$). | Inherent strengths, protection |
| **D30** (Trimsamsha) | 30 | Unequal | **Odd Signs**: $0-5^\circ$ Mars (Aries), $5-10^\circ$ Saturn (Aquarius), $10-18^\circ$ Jupiter (Sagittarius), $18-25^\circ$ Mercury (Gemini), $25-30^\circ$ Venus (Libra).<br>**Even Signs**: $0-5^\circ$ Venus (Taurus), $5-12^\circ$ Mercury (Virgo), $12-20^\circ$ Jupiter (Pisces), $20-25^\circ$ Saturn (Capricorn), $25-30^\circ$ Mars (Scorpio). | Evils, afflictions, character |
| **D40** (Khavedamsha) | 40 | $0^\circ 45'$ | Division $k = \lfloor D / 0.75 \rfloor$.<br>**Odd Sign**: Starts from Aries ($0 + k$).<br>**Even Sign**: Starts from Libra ($6 + k$). | Auspicious/inauspicious fruits |
| **D45** (Akshavedamsha) | 45 | $0^\circ 40'$ | Division $k = \lfloor D / (40/60) \rfloor$.<br>**Movable** $\rightarrow$ Aries, **Fixed** $\rightarrow$ Leo, **Dual** $\rightarrow$ Sagittarius. | Moral character, integrity |
| **D60** (Shashtiamsha) | 60 | $0^\circ 30'$ | Division $k = \lfloor D / 0.5 \rfloor$. Sign = $(S + k) \pmod{12}$. | Past life karma, all matters |

---

## 4. Dasha Calculation Systems (15 Systems: Vimshottari, Tribhagi, Yogini, Chara, Narayana, Mandook, Shashti-Hayani, Sudasa, Ashtottari, Kalachakra, Moola, Lagna Kendradi, Drigdasa, Shoola, Niryana Shoola)

### 4.1 Vimshottari Dasha (120-Year Cycle)
- **Planetary Sequence & Full Years**:
  - Ketu (7 yrs) $\rightarrow$ Venus (20 yrs) $\rightarrow$ Sun (6 yrs) $\rightarrow$ Moon (10 yrs) $\rightarrow$ Mars (7 yrs) $\rightarrow$ Rahu (18 yrs) $\rightarrow$ Jupiter (16 yrs) $\rightarrow$ Saturn (19 yrs) $\rightarrow$ Mercury (17 yrs).
  - Total = $7 + 20 + 6 + 10 + 7 + 18 + 16 + 19 + 17 = 120\text{ years}$.
- **Balance of Mahadasha at Birth**:
  $$\text{Nakshatra Fraction Elapsed} = \frac{\lambda_\text{Moon} \pmod{13^\circ 20'}}{13^\circ 20'}$$
  $$\text{Fraction Remaining } f = 1 - \text{Nakshatra Fraction Elapsed}$$
  $$\text{Birth Dasha Balance (Years)} = f \times \text{Full Years of Nakshatra Lord}$$
- **Year length**: $1$ dasha-year $= 365.256364$ days (JHora sidereal year).
- **Sub-Period Duration Formula (Multi-Level)**:
  $$\text{Duration (Years)} = \text{Parent Duration (Years)} \times \frac{\text{Lord's Vimshottari Years}}{120}$$
  - Level 1: Mahadasha (MD)
  - Level 2: Antardasha (AD) = $\text{MD Years} \times \frac{\text{AD Lord Years}}{120}$
  - Level 3: Pratyantardasha (PD) = $\text{AD Years} \times \frac{\text{PD Lord Years}}{120}$
  - Level 4: Sookshmadasha (SD) = $\text{PD Years} \times \frac{\text{SD Lord Years}}{120}$
  - Level 5: Pranadasha (PAD) = $\text{SD Years} \times \frac{\text{PAD Lord Years}}{120}$

### 4.2 Yogini Dasha (36-Year Cycle)
- **Sequence & Duration**:
  1. Mangala (Moon) — 1 year
  2. Pingala (Sun) — 2 years
  3. Dhanya (Jupiter) — 3 years
  4. Bhramari (Mars) — 4 years
  5. Bhadrika (Mercury) — 5 years
  6. Ulka (Saturn) — 6 years
  7. Siddha (Venus) — 7 years
  8. Sankata (Rahu) — 8 years
  - Total = $1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 = 36\text{ years}$.
- **Starting Yogini Formula**:
  $$\text{Yogini Index (0-based)} = (\text{Nakshatra Number [1-27]} + 2) \pmod 8$$
- **Sub-Period Calculation**:
  $$\text{Sub-Period (Years)} = \frac{\text{Major Yogini Years} \times \text{Sub Yogini Years}}{36}$$

### 4.3 Chara Dasha (Jaimini) — Calculation Algorithm
Chara Dasha assigns sign-based periods. The starting sign = **Lagna sign** (always).

**Period Duration Calculation:**
1. Find the **lord of the sign** being evaluated.
2. Count houses from the sign to its lord's position:
   - For **Odd signs** (Ar, Ge, Le, Li, Sg, Aq): Count forward (CW in zodiac order).
   - For **Even signs** (Ta, Cn, Vi, Sc, Cp, Pi): Count backward (CCW).
3. `raw_count = house_count - 1` (0-based index).
4. **Exception**: If lord is in its own sign, `raw_count = 12` (full cycle; some authorities use 12, KN Rao uses 12).
5. **Rahu/Ketu co-lord exception (Scorpio, Aquarius)**:
   - Scorpio: If Mars is in Scorpio, use Ketu as lord instead. Count from Scorpio to Ketu.
   - Aquarius: If Saturn is in Aquarius, use Rahu as lord instead. Count from Aquarius to Rahu.
6. `dasha_years = raw_count` (each unit = 1 year).
7. **Sub-period (Antardasha)**: Divide each sign's dasha equally among 12 signs, starting from the dasha sign itself:
   $$\text{Antardasha}(i) = \frac{\text{dasha\_years}}{12} \quad \text{years each, for } i = 0..11$$
8. **Sequence of signs**: After Lagna sign, the next dasha sign follows the same counting rule (forward for odd Lagna, backward for even Lagna).

Engine (any native): `chart.dasha_systems["chara"]`.

**Source:** KN Rao — *Predicting Through Jaimini's Chara Dasha*, Sanjay Rath

### 4.4 Narayana Dasha — Calculation Algorithm
Narayana Dasha also uses sign-based periods but starts from the **strongest Kendra sign** from Lagna.

**Starting Sign Selection:**
1. Among the 4 Kendra signs from Lagna (houses 1, 4, 7, 10), select the strongest using:
   - Most planets in the sign → stronger.
   - If tied: Exalted planet present → stronger.
   - If still tied: Use the sign whose lord has higher Shadbala.
   - If still tied: Use the Lagna sign itself.
2. **Exception (Sanjay Rath method)**: Always start from Lagna sign for D-1. For D-9, start from the Navamsa Lagna sign.

**Period Duration**: Same counting method as Chara Dasha (§4.3), including the odd/even forward/backward rule.

**Sequence**: After the starting sign, subsequent signs follow the forward/backward sequence determined by the starting sign's odd/even nature.

**Source:** Sanjay Rath — *Narayana Dasha*, BPHS Jaimini section

### 4.5 Mandook Dasha (Jaimini Frog-Jump Dasha) — Calculation Algorithm
Mandook Dasha is a sign-based jump dasha primarily applied to the Rudramsa (D-11) and Rasi (D-1) for timing conflicts, acute crises, and health transformations.

**Starting Sign Selection:**
- Evaluate Lagna (House 1) vs 7th House: Start from whichever sign is stronger (higher number of planets, presence of exalted planets, or aspect of Jupiter/Mercury).

**Sequence Progression (The Mandook / Frog Jump):**
The sequence jumps across quadrants (Kendras), then Panapharas, then Apoklimas:
- **For Odd Starting Sign (Direct Jumping)**:
  1. Kendras: $1\text{st} \rightarrow 4\text{th} \rightarrow 7\text{th} \rightarrow 10\text{th}$
  2. Panapharas: $2\text{nd} \rightarrow 5\text{th} \rightarrow 8\text{th} \rightarrow 11\text{th}$
  3. Apoklimas: $3\text{rd} \rightarrow 6\text{th} \rightarrow 9\text{th} \rightarrow 12\text{th}$
- **For Even Starting Sign (Reverse Jumping)**:
  1. Kendras: $1\text{st} \rightarrow 10\text{th} \rightarrow 7\text{th} \rightarrow 4\text{th}$
  2. Panapharas: $12\text{th} \rightarrow 9\text{th} \rightarrow 6\text{th} \rightarrow 3\text{rd}$
  3. Apoklimas: $11\text{th} \rightarrow 8\text{th} \rightarrow 5\text{th} \rightarrow 2\text{nd}$

**Period Duration:**
- Same counting rules as Chara Dasha (§4.3): Count from dasha sign to its lord (forward for odd signs, backward for even signs), subtract 1. Lord in own sign = 12 years.

### 4.6 Shashti-Hayani Dasha (60-Year Cycle) — Calculation Algorithm
A special conditional nakshatra dasha from *BPHS Ch. 46*.
**Activation Condition:** Chart must have Sun placed in the **1st House (Lagna)** in any sign (`house_of(Sun, Lagna) == 1`).

**Total Cycle:** 60 Years across 8 planetary lords.

**Nakshatra Grouping & Lordship Table:**
| Group # | Nakshatras | Lord | Duration (Years) |
|:---:|:---|:---:|:---:|
| 1 | Ashwini (1), Bharani (2), Krittika (3) | **Jupiter** | 10 |
| 2 | Rohini (4), Mrigashira (5), Ardra (6) | **Sun** | 10 |
| 3 | Punarvasu (7), Pushya (8), Ashlesha (9) | **Mars** | 10 |
| 4 | Magha (10), Purva Phalguni (11), Uttara Phalguni (12) | **Moon** | 6 |
| 5 | Hasta (13), Chitra (14), Swati (15) | **Mercury** | 6 |
| 6 | Vishakha (16), Anuradha (17), Jyeshtha (18) | **Venus** | 6 |
| 7 | Mula (19), Purva Ashadha (20), Uttara Ashadha (21), Abhijit (28) | **Saturn** | 6 |
| 8 | Shravana (22), Dhanishta (23), Shatabhisha (24), Purva Bhadrapada (25), Uttara Bhadrapada (26), Revati (27) | **Rahu** | 6 |

**Balance of Dasha at Birth:**
Let $N$ be natal Moon's Nakshatra number ($1-27$), $G$ be its Group, $L$ be the Group Lord with total years $Y_G$:
$$\text{Elapsed Fraction in Group} = \frac{(\text{Nakshatra index in group} - 1) \times 13^\circ 20' + (\lambda_{\text{Moon}} \pmod{13^\circ 20'})}{\text{Total Arc of Group}}$$
$$\text{Balance Years} = Y_G \times (1 - \text{Elapsed Fraction})$$

### 4.7 Sudasa (Lakshmi Sthana Dasha) — Calculation Algorithm
Sudasa (also known as Sri Lagna Dasha) is a Jaimini rasi dasha specifically designed for calculating financial fortune, status elevation, and Lakshmi blessings.

**Starting Point — Sri Lagna (SL) Longitude:**
$$\lambda_{\text{SL}} = \left[ \lambda_{\text{ASC}} + \left( \frac{\lambda_{\text{Moon}} \pmod{13^\circ 20'}}{13^\circ 20'} \times 360^\circ \right) \right] \pmod{360^\circ}$$
- Starting Dasha Sign = Sign containing $\lambda_{\text{SL}}$ ($\lfloor \lambda_{\text{SL}} / 30^\circ \rfloor$).

**Sequence of Signs:**
- If Sri Lagna sign is an **Odd sign**: Direct zodiacal order ($1 \rightarrow 2 \rightarrow 3 \dots \rightarrow 12$).
- If Sri Lagna sign is an **Even sign**: Reverse zodiacal order ($12 \rightarrow 11 \rightarrow 10 \dots \rightarrow 1$).

**Duration of Each Sign Period:**
- Calculated using standard Jaimini counting from the Dasha sign to its lord's sign (Odd sign: forward $- 1$; Even sign: backward $- 1$; Own sign: 12 years).

### 4.8 Vimshottari — Tribhagi Variation (40-Year Sub-Cycle)
In the Tribhagi variant, the standard 120-year Vimshottari cycle is compressed by a factor of $\frac{1}{3}$ into a **40-year cycle** that repeats 3 times over 120 years.

**Planetary Dasha Durations in Tribhagi:**
$$\text{Tribhagi Duration}(\text{Planet}) = \frac{\text{Standard Vimshottari Years}}{3}$$

| Planet | Standard Years | Tribhagi Years | Tribhagi Duration (Y-M-D) |
|:---|:---:|:---:|:---|
| **Sun** | 6 | **2.0000** | 2 Years, 0 Months, 0 Days |
| **Moon** | 10 | **3.3333** | 3 Years, 4 Months, 0 Days |
| **Mars** | 7 | **2.3333** | 2 Years, 4 Months, 0 Days |
| **Rahu** | 18 | **6.0000** | 6 Years, 0 Months, 0 Days |
| **Jupiter** | 16 | **5.3333** | 5 Years, 4 Months, 0 Days |
| **Saturn** | 19 | **6.3333** | 6 Years, 4 Months, 0 Days |
| **Mercury** | 17 | **5.6667** | 5 Years, 8 Months, 0 Days |
| **Ketu** | 7 | **2.3333** | 2 Years, 4 Months, 0 Days |
| **Venus** | 20 | **6.6667** | 6 Years, 8 Months, 0 Days |
| **Total Cycle** | **120** | **40.0000** | **40 Years** (Repeats $3\times$) |

**Balance of Dasha at Birth:**
$$\text{Tribhagi Balance (Years)} = (1 - \text{Nakshatra Fraction Elapsed}) \times \text{Tribhagi Duration}(\text{Nakshatra Lord})$$

---

### 4.9 Ashtottari Dasha (108-Year Cycle) — Calculation Engine
From *BPHS Ch. 46*. A non-luminary nakshatra dasha system consisting of **8 planetary lords** (Ketu is excluded).

**Applicability Condition:**
- Rahu placed in a Kendra ($1, 4, 7, 10$) or Trikona ($5, 9$) from the Lagna Lord, OR birth during Krishna Paksha in daytime / Shukla Paksha at night.

**Total Cycle:** 108 Years across 8 planets.

**Planetary Dasha Periods:**
| Planet | Dasha Duration (Years) | Fraction of 108 |
|:---|:---:|:---:|
| **Sun** | 6 | $6 / 108$ |
| **Moon** | 15 | $15 / 108$ |
| **Mars** | 8 | $8 / 108$ |
| **Mercury** | 17 | $17 / 108$ |
| **Saturn** | 10 | $10 / 108$ |
| **Jupiter** | 19 | $19 / 108$ |
| **Rahu** | 12 | $12 / 108$ |
| **Venus** | 21 | $21 / 108$ |
| **Total** | **108** | **1.0** |

**Nakshatra Assignment Table (28-Nakshatra Scheme Starting from Ardra):**
| Group # | Starting Nakshatra | Nakshatras Included | Count | Dasha Lord | Full Years |
|:---:|:---|:---|:---:|:---|:---:|
| 1 | Ardra (6) | Ardra, Punarvasu, Pushya, Ashlesha | 4 | **Sun** | 6 |
| 2 | Magha (10) | Magha, Purva Phalguni, Uttara Phalguni | 3 | **Moon** | 15 |
| 3 | Hasta (13) | Hasta, Chitra, Swati, Vishakha | 4 | **Mars** | 8 |
| 4 | Anuradha (17) | Anuradha, Jyeshtha, Mula | 3 | **Mercury** | 17 |
| 5 | Purva Ashadha (20) | P.Ashadha, U.Ashadha, Abhijit, Shravana | 4 | **Saturn** | 10 |
| 6 | Dhanishta (23) | Dhanishta, Shatabhisha, Purva Bhadrapada | 3 | **Jupiter** | 19 |
| 7 | Uttara Bhadrapada (26) | U.Bhadrapada, Revati, Ashwini, Bharani | 4 | **Rahu** | 12 |
| 8 | Krittika (3) | Krittika, Rohini, Mrigashira | 3 | **Venus** | 21 |

**Balance of Dasha Calculation:**
Let $N$ be natal Moon's nakshatra, $G$ be the group of $N$, $k$ be the number of nakshatras in $G$ ($3$ or $4$), and $Y_G$ be group duration:
$$\text{Group Total Arc} = k \times 13^\circ 20' = k \times 13.3333^\circ$$
$$\text{Elapsed Arc in Group} = (\text{Nakshatra index in group} - 1) \times 13^\circ 20' + (\lambda_{\text{Moon}} \pmod{13^\circ 20'})$$
$$\text{Balance Years} = Y_G \times \left(1 - \frac{\text{Elapsed Arc in Group}}{\text{Group Total Arc}}\right)$$

**Antardasha Sub-period Formula:**
$$\text{AD Duration (Years)} = \frac{\text{MD Years} \times \text{AD Lord Years}}{108}$$

---

### 4.10 Kalachakra Dasha — Calculation Engine
From *BPHS Ch. 47*. The most intricate nakshatra-rasi dasha system in Jyotish, based on Moon's Navamsa movement across the zodiacal wheel (*Kalachakra*).

#### 4.10.1 Savya (Direct) vs. Apasavya (Reverse) Groups
- **Savya** (nakshatra numbers $1$–$9$, $14$–$19$, $25$–$27$): Ashwini, Bharani, Krittika, Rohini, Mrigashira, Ardra; Punarvasu, Pushya, Ashlesha; Chitra, Swati, Vishakha; Anuradha, Jyeshtha, Mula; Purva Bhadrapada, Uttara Bhadrapada, Revati.
- **Apasavya** (numbers $10$–$13$, $20$–$24$): Magha, Purva Phalguni, Uttara Phalguni; Hasta; Purva Ashadha, Uttara Ashadha, Shravana; Dhanishta, Shatabhisha.
- **Abhijit** intercalary $276^\circ40' \le \lambda < 280^\circ53'20''$ (Capricorn $6^\circ40'$–$10^\circ53'20''$, same span as §25.1) is always **Apasavya**, even though Uttara Ashadha (21) is Apasavya and the overlapping 27-nakshatra index is 21.

#### 4.10.2 Deha and Jiva Signs
- **Deha (Body)**: The starting sign of the 9-Navamsa pada progression.
- **Jiva (Soul)**: The ending sign of the 9-Navamsa pada progression.
- *Rule*: Transits of natural malefics over Deha or Jiva sign trigger acute physical or psychological crises.

#### 4.10.3 Rasi Dasha Durations (Paramayus Years)
| Rasi (Sign) | Lord | Kalachakra Dasha Years |
|:---|:---|:---:|
| **Aries** | Mars | 7 |
| **Taurus** | Venus | 16 |
| **Gemini** | Mercury | 9 |
| **Cancer** | Moon | 21 |
| **Leo** | Sun | 5 |
| **Virgo** | Mercury | 9 |
| **Libra** | Venus | 16 |
| **Scorpio** | Mars | 7 |
| **Sagittarius** | Jupiter | 10 |
| **Capricorn** | Saturn | 4 |
| **Aquarius** | Saturn | 4 |
| **Pisces** | Jupiter | 10 |
| **Total Full Cycle** | — | **88 to 100 Years** (depends on Pada) |

#### 4.10.4 Special Gatis (Non-Linear Jumps)
1. **Manduki Gati (Frog Jump)**: Direct jump between non-adjacent signs (e.g., Cancer $\rightarrow$ Leo or Virgo $\rightarrow$ Cancer).
2. **Markati Gati (Monkey Jump)**: Retrograde leap backward to the preceding sign.
3. **Simhavalokana Gati (Lion's Backward Glance)**: Major jump across quad boundaries (e.g., Sagittarius $\rightarrow$ Aries, or Pisces $\rightarrow$ Scorpio).

---

### 4.11 Moola Dasa (Root Cause / D-60 Karma Dasha) — Calculation Engine
Used for timing the ripening of past-life karmic seeds recorded in the Shashtiamsha (D-60) and natal chart root dignities.

**Starting Planet Selection:**
- Compare **Lagna** vs. **Moon**: Select the stronger based on Shadbala and Kendra placements.
- Dasha begins with the strongest planet occupying a Kendra from the starting point.
- If no planets in Kendras: Proceed to planets in Panapharas ($2, 5, 8, 11$), then Apoklimas ($3, 6, 9, 12$).

**Planetary Dasha Sequence & Durations:**
- Sequence proceeds in descending order of Shadbala strength among the planets in each quadrant group.
- Basic durations follow standard Vimshottari years (Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17, Ketu 7, Venus 20) modified by dignity coefficients.

---

### 4.12 Lagna Kendradi Rasi Dasa — Calculation Engine
A fundamental Jaimini rasi dasha that measures status elevation, worldly accomplishments, and public life.

**Starting Point:**
- Dasha begins with the **Lagna Sign (Ascendant)**.

**Sequence of Sign Cycles (3 Quad Groups):**
1. **Group 1 (Kendras)**: Houses $1, 4, 7, 10$ from Lagna.
2. **Group 2 (Panapharas)**: Houses $2, 5, 8, 11$ from Lagna.
3. **Group 3 (Apoklimas)**: Houses $3, 6, 9, 12$ from Lagna.

- **Progression within Groups**:
  - If the starting sign of the group is an **Odd sign**: Direct counting ($1 \rightarrow 4 \rightarrow 7 \rightarrow 10$).
  - If the starting sign of the group is an **Even sign**: Reverse counting ($10 \rightarrow 7 \rightarrow 4 \rightarrow 1$).

**Duration of Each Sign Period:**
- Count from the dasha sign to its lord's sign (Odd: forward $- 1$; Even: backward $- 1$; Lord in own sign $= 12$ years).

---

### 4.13 Drigdasa (Drishti Dasa / Vision Dasha) — Calculation Engine
A spiritual, dharmic, and vision dasha from *Jaimini Upadesha Sutras*.

**Starting Sign:**
- Always begins with the **9th House from Lagna** (the Dharma/Vision sthana).

**Sign Progression Algorithm:**
For any sign $S$, Drigdasa runs through $S$ itself, followed by all signs that **aspect $S$ via Jaimini Rasi Drishti**:
1. First period: 9th House sign.
2. Next periods: Signs casting direct Jaimini aspect on the 9th house sign (in direct or reverse order depending on odd/even).
3. Next group: 10th House sign and the signs aspecting the 10th house.
4. Next group: 11th House sign and the signs aspecting the 11th house, continuing through all 12 houses.

**Duration per Sign:**
- Standard Jaimini counting from sign to its lord's position $- 1$ (Own sign $= 12$ years).

---

### 4.14 Shoola Dasa (Ayur / Longevity & Disease Dasha) — Calculation Engine
The primary Jaimini dasha for identifying periods of bodily vulnerability, severe illness, accidents, and death (*Ayur-daya*).

**Starting Sign Selection:**
- Compare **1st House (Lagna)** and **7th House**: Start from whichever sign is stronger (occupied by more planets, or aspected by Jupiter/Mercury).

**Sequence of Signs:**
- **Odd Starting Sign**: Direct zodiacal sequence ($1 \rightarrow 2 \rightarrow 3 \rightarrow 4 \dots \rightarrow 12$).
- **Even Starting Sign**: Reverse zodiacal sequence ($12 \rightarrow 11 \rightarrow 10 \rightarrow 9 \dots \rightarrow 1$).

**Fixed Duration:**
- **Exactly 9 Years per Sign** (Invariant across all 12 signs).
- Total cycle $= 12 \times 9 = \mathbf{108\text{ Years}}$.

**Critical Crisis Activation Triggers:**
- Dasha sign containing or aspecting the **Rudra planet** (stronger of 8L and 2L).
- Dasha sign containing the **Trishoola** or **Maandi**.
- Dasha sign in the 8th house from Lagna or AL.

---

### 4.15 Niryana Shoola Dasa — Calculation Engine
A specialized death-inflicting (*Niryana*) longevity dasha focusing strictly on terminal exits and major transformations.

**Starting Sign Selection (mandatory, not optional):**
Score houses **2, 7, and 8** from Lagna (occupants + exaltation bonus, same `_kendra_strength` as Shoola). Dasha **starts from the strongest of those three**. Ties keep the earlier house in the order $2 \rightarrow 7 \rightarrow 8$.

**Sequence of Signs:**
- Direct zodiacal order for Odd starting signs; reverse order for Even starting signs.

**Variable Duration per Sign Modality:**
| Sign Modality | Examples | Dasha Duration per Sign |
|:---|:---|:---:|
| **Movable Signs (*Chara*)** | Aries, Cancer, Libra, Capricorn | **7 Years** |
| **Fixed Signs (*Sthira*)** | Taurus, Leo, Scorpio, Aquarius | **8 Years** |
| **Dual Signs (*Dvisvabhava*)** | Gemini, Virgo, Sagittarius, Pisces | **9 Years** |
| **Full 12-Sign Cycle** | $4 \times 7 + 4 \times 8 + 4 \times 9$ | **96 Years** |

---

### 4.16 Dasha Lord Strength Evaluation Framework
For ALL dasha systems, the strength/weakness of the dasha lord determines result quality. Evaluate using this checklist:

| # | Condition | Flag Value |
|:---:|:---|:---|
| 1 | Dasha lord in own sign | `STRONG` |
| 2 | Dasha lord exalted | `VERY_STRONG` |
| 3 | Dasha lord in Moolatrikona | `STRONG` |
| 4 | Dasha lord in friendly sign | `MODERATE` |
| 5 | Dasha lord in neutral sign | `NEUTRAL` |
| 6 | Dasha lord in enemy sign | `WEAK` |
| 7 | Dasha lord debilitated | `VERY_WEAK` |
| 8 | Dasha lord combust (§2.7) | `WEAKENED` |
| 9 | Dasha lord retrograde (§2.9) | `MODIFIED_STRENGTH` (amplified good or bad) |
| 10 | Dasha lord in Kendra from Lagna | Positional boost: `+1` |
| 11 | Dasha lord in Trikona from Lagna | Positional boost: `+1` |
| 12 | Dasha lord in Dusthana (6/8/12) | Positional penalty: `-1` |
| 13 | Dasha lord lost in Graha Yuddha (§2.8) | `WEAKENED` |
| 14 | Dasha lord Vargottama (same sign in D1 and D9) | `STRONG` |
| 15 | Dasha lord receiving aspect from benefics | `SUPPORTED` |
| 16 | Dasha lord receiving aspect from malefics | `AFFLICTED` |

---

## 5. Ashtakavarga System (BAV, SAV, Shodhana & Pindas)

### 5.1 Bhinnashtakavarga (BAV) Contribution Matrix
Each beneficiary planet receives 1 bindu (dot) when the contributor is placed at specific house offsets (1-indexed) from the contributor's natal position:

1. **Sun (48 Total Bindus)**:
   - From Sun: 1, 2, 4, 7, 8, 9, 10, 11 (8)
   - From Moon: 3, 6, 10, 11 (4)
   - From Mars: 1, 2, 4, 7, 8, 9, 10, 11 (8)
   - From Mercury: 3, 5, 6, 9, 10, 11, 12 (7)
   - From Jupiter: 5, 6, 9, 11 (4)
   - From Venus: 6, 7, 12 (3)
   - From Saturn: 1, 2, 4, 7, 8, 9, 10, 11 (8)
   - From Lagna: 3, 4, 6, 10, 11, 12 (6)
2. **Moon (49 Total Bindus)** — JHora / PyJHora (engine; these four cells are what make SAV = 337):
   - From Sun: 3, 6, 7, 8, 10, 11 (6)
   - From Moon: 1, 3, 6, 7, **9**, 10, 11 (7)
   - From Mars: 2, 3, 5, 6, 10, 11 (6) *(no 9)*
   - From Mercury: 1, 3, 4, 5, 7, 8, 10, 11 (8)
   - From Jupiter: 1, **2**, 4, 7, 8, 10, 11 (7) *(+2, −12)*
   - From Venus: 3, 4, 5, 7, 9, 10, 11 (7)
   - From Saturn: 3, 5, 6, 11 (4)
   - From Lagna: 3, 6, 10, 11 (4)
3. **Mars (39 Total Bindus)**:
   - From Sun: 3, 5, 6, 10, 11 (5)
   - From Moon: 3, 6, 11 (3)
   - From Mars: 1, 2, 4, 7, 8, 10, 11 (7)
   - From Mercury: 3, 5, 6, 11 (4)
   - From Jupiter: 6, 10, 11, 12 (4)
   - From Venus: 6, 8, 11, 12 (4)
   - From Saturn: 1, 4, 7, 8, 9, 10, 11 (7)
   - From Lagna: 1, 3, 6, 10, 11 (5)
4. **Mercury (54 Total Bindus)**:
   - From Sun: 5, 6, 9, 11, 12 (5)
   - From Moon: 2, 4, 6, 8, 10, 11 (6)
   - From Mars: 1, 2, 4, 7, 8, 9, 10, 11 (8)
   - From Mercury: 1, 3, 5, 6, 9, 10, 11, 12 (8)
   - From Jupiter: 6, 8, 11, 12 (4)
   - From Venus: 1, 2, 3, 4, 5, 8, 9, 11 (8)
   - From Saturn: 1, 2, 4, 7, 8, 9, 10, 11 (8)
   - From Lagna: 1, 2, 4, 6, 8, 10, 11 (7)
5. **Jupiter (56 Total Bindus)**:
   - From Sun: 1, 2, 3, 4, 7, 8, 9, 10, 11 (9)
   - From Moon: 2, 5, 7, 9, 11 (5)
   - From Mars: 1, 2, 4, 7, 8, 10, 11 (7)
   - From Mercury: 1, 2, 4, 5, 6, 9, 10, 11 (8)
   - From Jupiter: 1, 2, 3, 4, 7, 8, 10, 11 (8)
   - From Venus: 2, 5, 6, 9, 10, 11 (6)
   - From Saturn: 3, 5, 6, 12 (4)
   - From Lagna: 1, 2, 4, 5, 6, 7, 9, 10, 11 (9)
6. **Venus (52 Total Bindus)**:
   - From Sun: 8, 11, 12 (3)
   - From Moon: 1, 2, 3, 4, 5, 8, 9, 11, 12 (9)
   - From Mars: 3, 4, 6, 9, 11, 12 (6) *(no 8 — JHora)*
   - From Mercury: 3, 5, 6, 9, 11 (5)
   - From Jupiter: 5, 8, 9, 10, 11 (5)
   - From Venus: 1, 2, 3, 4, 5, 8, 9, 10, 11 (9)
   - From Saturn: 3, 4, 5, 8, 9, 10, 11 (7)
   - From Lagna: 1, 2, 3, 4, 5, 8, 9, 11 (7)
7. **Saturn (39 Total Bindus)**:
   - From Sun: 1, 2, 4, 7, 8, 10, 11 (7) *(no 9 — JHora)*
   - From Moon: 3, 6, 11 (3)
   - From Mars: 3, 5, 6, 10, 11, 12 (6)
   - From Mercury: 6, 8, 9, 10, 11, 12 (6)
   - From Jupiter: 5, 6, 11, 12 (4)
   - From Venus: 6, 11, 12 (3)
   - From Saturn: 3, 5, 6, 11 (4)
   - From Lagna: 1, 3, 4, 6, 10, 11 (5)
8. **Lagna BAV (49 Total Bindus)** — JHora / PyJHora:
   - From Sun: 3, 4, 6, 10, 11, 12 (6)
   - From Moon: 3, 6, 10, 11, 12 (5)
   - From Mars: 1, 3, 6, 10, 11 (5)
   - From Mercury: 1, 2, 4, 6, 8, 10, 11 (7)
   - From Jupiter: 1, 2, 4, 5, 6, 7, 9, 10, 11 (9)
   - From Venus: 1, 2, 3, 4, 5, 8, 9 (7) *(no 11)*
   - From Saturn: 1, 3, 4, 6, 10, 11 (5)
   - From Lagna: 3, 6, 10, 11 (4)

### 5.2 Sarvashtakavarga (SAV)
$$\text{SAV}(\text{Sign } s) = \sum_{P \in \{\text{Sun}, \dots, \text{Saturn}\}} \text{BAV}_P(s)$$
- Standard Canonical Total: **337 points** (Lagna excluded from summation).
- Benchmark: $\ge 28$ points = Strong/Auspicious; $< 25$ points = Weak/Challenging.

### 5.3 Shodhya Pindas (Rashi & Graha Multipliers)
- **Rashi Gunakara (Sign Multipliers)**:
  - Aries: 7 | Taurus: 10 | Gemini: 8 | Cancer: 4 | Leo: 10 | Virgo: 5
  - Libra: 7 | Scorpio: 8 | Sagittarius: 9 | Capricorn: 5 | Aquarius: 11 | Pisces: 12
- **Graha Gunakara (Planet Multipliers)**:
  - Sun: 5 | Moon: 5 | Mars: 8 | Mercury: 5 | Jupiter: 10 | Venus: 7 | Saturn: 5
- **Shodhana (before pinda)**: Trikona — if all three signs of an elemental trikona have bindus, subtract the minimum from all three. Ekadhipatya — dual-lord pairs (Ar–Sc, Ta–Li, Ge–Vi, Sg–Pi, Cp–Aq). Skip a pair if either sign is already 0. Both occupied: no change. One occupied: empty sign is cut to the occupied remainder (or 0 if occupied ≥ empty). Both empty: equal → both 0; unequal → both set to the smaller.
- **Formulas** (on *reduced* bindus):
  $$\text{Rashi Pinda} = \sum_{s=0}^{11} \text{Reduced Bindus}(s) \times \text{Rashi Gunakara}(s)$$
  $$\text{Graha Pinda} = \sum_{s} \text{Reduced}(s) \times \sum_{P \text{ occupying } s} \text{Graha Gunakara}(P)$$
  $$\text{Shodhya Pinda} = \text{Rashi Pinda} + \text{Graha Pinda}$$
  Engine: `chart.ashtakavarga["sodhya"]`.

### 5.4 SAV Pattern Flags (not a separate formula)
Derived from the SAV row and this native’s Lagna. Stored on `chart.ashtakavarga["patterns"]`:
- **11H vs 10H** (KN Rao): whether house-11 bindus exceed house-10.
- **Above-average / weak houses**: house SAV vs mean; weak if $< \text{mean}-3$.
- **7H $< 25$**: marriage-timing delay flag.
- **6H $> 30$**: service / endurance flag.

These are labels on the SAV numbers in §5.2, not a second bindu system.

---

## 6. Shadbala & Planetary Strengths

Shadbala measures the 6-fold potency of the 7 classical planets in **Shashtiamsas** (60 Shashtiamsas = 1 Rupa).

### 6.1 The Six Balas — Mathematical Formulation Engine

$$\text{Total Shadbala}(P) = \text{Sthana Bala} + \text{Dig Bala} + \text{Kala Bala} + \text{Cheshta Bala} + \text{Naisargika Bala} + \text{Drik Bala}$$

#### 1. Sthana Bala (Positional Strength — 5 Sub-components)
$$\text{Sthana Bala}(P) = \text{Uchcha Bala} + \text{Saptavargaja Bala} + \text{Ojha-Yugmarashi Bala} + \text{Kendradi Bala} + \text{Drekkana Bala}$$

- **Uchcha Bala (Exaltation Strength)**:
  Let $\lambda_{\text{deb}}$ be the deep debilitation longitude of planet $P$ (§2.3). Compute shortest angular distance $\Delta\lambda = |\lambda_P - \lambda_{\text{deb}}| \pmod{360^\circ}$; if $\Delta\lambda > 180^\circ$, set $\Delta\lambda = 360^\circ - \Delta\lambda$:
  $$\text{Uchcha Bala} = \frac{\Delta\lambda}{3} \quad (0 \le \text{Uchcha Bala} \le 60\text{ Shashtiamsas})$$
- **Saptavargaja Bala (7-Divisional Dignity Strength)**:
  Evaluated across D-1 (Rasi), D-2 (Hora), D-3 (Drekkana), D-7 (Saptamsa), D-9 (Navamsa), D-12 (Dwadasamsa), D-30 (Trimsamsa):
  | Dignity in Varga | Shashtiamsas Awarded |
  |:---|:---:|
  | Moolatrikona | 45.000 |
  | Swakshetra (Own Sign) | 30.000 |
  | Adhi-Mitra (Great Friend's Sign) | 20.000 |
  | Mitra (Friend's Sign) | 15.000 |
  | Sama (Neutral Sign) | 7.500 |
  | Satru (Enemy's Sign) | 3.750 |
  | Adhi-Satru (Bitter Enemy's Sign) | 1.875 |
  $$\text{Saptavargaja Bala} = \sum_{v=1}^{7} \text{Dignity Score}(P, \text{Varga}_v)$$
- **Ojha-Yugmarashi Bala (Odd/Even Sign Strength)**:
  - Male planets (Sun, Mars, Jupiter) + Mercury + Saturn in Odd signs ($1, 3, 5, 7, 9, 11$): Award $+15$ in D-1, $+15$ in D-9 (Max 30).
  - Female planets (Moon, Venus) in Even signs ($2, 4, 6, 8, 10, 12$): Award $+15$ in D-1, $+15$ in D-9 (Max 30).
- **Kendradi Bala (Quadrant/Succedent/Cadent Placement)**:
  - In Kendra ($1, 4, 7, 10$): **60 Shashtiamsas**
  - In Panaphara ($2, 5, 8, 11$): **30 Shashtiamsas**
  - In Apoklima ($3, 6, 9, 12$): **15 Shashtiamsas**
- **Drekkana Bala (Decanate Gender Strength)**:
  - 1st Drekkana ($0^\circ - 10^\circ$): Male planets (Sun, Mars, Jupiter) get **15 Shashtiamsas**.
  - 2nd Drekkana ($10^\circ - 20^\circ$): Neutral planets (Mercury, Saturn) get **15 Shashtiamsas**.
  - 3rd Drekkana ($20^\circ - 30^\circ$): Female planets (Moon, Venus) get **15 Shashtiamsas**.

#### 2. Dig Bala (Directional Strength)
Each planet achieves $60$ Shashtiamsas at its directional peak and $0$ at the opposite house:
- **Peak Longitudes ($\lambda_{\text{DigPeak}}$)**:
  - 1st House Cusp (East): Jupiter, Mercury
  - 4th House Cusp (North): Moon, Venus
  - 7th House Cusp (West): Saturn
  - 10th House Cusp (South): Sun, Mars
- **Zero Longitude ($\lambda_{\text{DigZero}}$)** $= (\lambda_{\text{DigPeak}} + 180^\circ) \pmod{360^\circ}$.
- **Formula**:
  Let $\Delta\lambda = |\lambda_P - \lambda_{\text{DigZero}}| \pmod{360^\circ}$; if $\Delta\lambda > 180^\circ$, set $\Delta\lambda = 360^\circ - \Delta\lambda$:
  $$\text{Dig Bala} = \frac{\Delta\lambda}{3} \quad (0 \le \text{Dig Bala} \le 60\text{ Shashtiamsas})$$

#### 3. Kala Bala (Temporal Strength — 6 Sub-components)
$$\text{Kala Bala}(P) = \text{Natonnatha} + \text{Paksha} + \text{Tribhaga} + \text{Abda-Masa-Vara-Hora} + \text{Ayana} + \text{Yuddha}$$

- **Natonnatha Bala (Diurnal / Nocturnal Strength)**:
  - Day Birth: Sun, Jupiter, Venus $= 60$; Moon, Mars, Saturn $= 0$; Mercury $= 60$ always.
  - Night Birth: Moon, Mars, Saturn $= 60$; Sun, Jupiter, Venus $= 0$; Mercury $= 60$ always.
- **Paksha Bala (Lunar Phase Fortnight Strength)**:
  Let elongation $E = |\lambda_{\text{Moon}} - \lambda_{\text{Sun}}| \pmod{360^\circ}$; if $E > 180^\circ$, set $E = 360^\circ - E$:
  - For Benefics (Jupiter, Venus, Waxing Moon, unafflicted Mercury): $\text{Paksha Bala} = \frac{E}{3}$ (Max 60 at Full Moon).
  - For Malefics (Sun, Mars, Saturn, Waning Moon, afflicted Mercury): $\text{Paksha Bala} = 60 - \frac{E}{3}$ (Max 60 at New Moon).
  - *Moon's Paksha Bala is multiplied by 2* ($\text{Paksha Bala}(\text{Moon}) = 2 \times \frac{E}{3}$). JHora leaves this **uncapped in Kala Bala** (can exceed 60 near Full Moon). Engine matches that. Cheshta used in Ishta–Kashta is the **undoubled** $E/3$ clamped to 60 (§6.3) so Moon Kashta is not forced to 0.
- **Tribhaga Bala (Three Segments of Day & Night)**:
  - Day Part 1 (Sunrise to 1/3 Day): **Mercury** gets 60.
  - Day Part 2 (1/3 Day to 2/3 Day): **Sun** gets 60.
  - Day Part 3 (2/3 Day to Sunset): **Saturn** gets 60.
  - Night Part 1 (Sunset to 1/3 Night): **Moon** gets 60.
  - Night Part 2 (1/3 Night to 2/3 Night): **Venus** gets 60.
  - Night Part 3 (2/3 Night to Sunrise): **Mars** gets 60.
  - **Jupiter** gets 60 at all times.
- **Abda, Masa, Vara, Hora Balas (Ruler Strengths)**:
  - Year Lord (*Varsha Lord*): **15 Shashtiamsas**
  - Month Lord (*Masa Lord*): **30 Shashtiamsas**
  - Day Lord (*Vara Lord*): **45 Shashtiamsas**
  - Hour Lord (*Hora Lord* — computed per §14.6): **60 Shashtiamsas**
- **Ayana Bala (Declination Strength)**:
  Based on celestial declination $\delta$. Sun, Mars, Jupiter, Venus gain strength in Northern declination; Moon, Saturn in Southern declination. Max = 60.
- **Yuddha Bala (Planetary War Adjustment)**:
  Winner receives **$+60$ Shashtiamsas**; loser loses **$-60$ Shashtiamsas** (per §2.8).

#### 4. Cheshta Bala (Motional Strength)
- **Sun**: Cheshta = Ayana Bala. **Moon**: Cheshta = Paksha Bala (clamped to 60 in this slot; Kala Paksha itself may exceed 60).
- **Mars, Mercury, Jupiter, Venus, Saturn** (BPHS Chesta Kendra, JHora-compatible mean longitudes from the 1900 Ujjain epoch):
  - Mean longitude $\bar\lambda_P$ from epoch mean + mean daily motion + year correction, shifted by $(76^\circ - \lambda_{\text{place}})/15/24$ days.
  - Outer (Mars, Jupiter, Saturn): Seeghrochcha $= \bar\lambda_{\text{Sun}}$, average $= (\lambda_P + \bar\lambda_P)/2$.
  - Inner (Mercury, Venus): Seeghrochcha $= \bar\lambda_P$, average $= (\lambda_P + \bar\lambda_{\text{Sun}})/2$.
  - Chesta Kendra = shortest arc $|\text{Seeghrochcha} - \text{average}|$ reduced to $0^\circ\!-\!180^\circ$.
  - $\text{Cheshta Bala} = \min(60, \text{Kendra}/3)$.
- Retrograde is **not** assigned a flat 60. Vakra outer grahas already have a large kendra; forcing 60 inflated Saturn vs JHora.

#### 5. Naisargika Bala (Natural Inherent Strength — Invariant)
| Planet | Shashtiamsas | Rupas |
|:---|:---:|:---:|
| **Sun** | **60.00** | 1.000 |
| **Moon** | **51.43** | 0.857 |
| **Venus** | **42.86** | 0.714 |
| **Jupiter** | **34.29** | 0.571 |
| **Mercury** | **25.71** | 0.429 |
| **Mars** | **17.14** | 0.286 |
| **Saturn** | **8.57** | 0.143 |

#### 6. Drik Bala (Aspectual Strength)
Graha Drik Bala uses **degree-based spashta dṛṣṭi** (BPHS ch.26 / JHora), not whole-sign house counts:
Let $\alpha = (\lambda_P - \lambda_Q) \bmod 360^\circ$. Convert $\alpha$ to virupas $V_Q$ by the piecewise 0–60 table (7th aspect peaks at $180^\circ$; Mars 4th/8th, Jupiter 5th/9th, Saturn 3rd/10th add in their peak bands). Then
$$\text{Drik Bala}(P) = \frac{1}{4}\sum_{Q \neq P} s(Q)\, V_Q(\alpha)$$
where $s(Q)=+1$ if $Q$ is a natural benefic for the paksha (Jupiter, Venus, Mercury, waxing Moon) and $-1$ if malefic (Sun, Mars, Saturn, waning Moon). The factor $1/4$ is required — omitting it parks Drik at the 60 virupa cap and inflates total rupas (Sun in the Aditya lock). Whole-sign pinda from §2.10 is used only for **Bhava Drishti Bala** (§6.7).

### 6.2 Minimum Required Shadbala Thresholds
| Planet | Minimum Rupas | Minimum Shashtiamsas |
|:---|:---:|:---:|
| **Sun** | 6.5 | 390 |
| **Moon** | 6.0 | 360 |
| **Mars** | 5.0 | 300 |
| **Mercury** | 7.0 | 420 |
| **Jupiter** | 6.5 | 390 |
| **Venus** | 5.5 | 330 |
| **Saturn** | 5.0 | 300 |

### 6.3 Ishta Phala & Kashta Phala
$$\text{Ishta Phala} = \sqrt{\text{Uchcha Bala} \times \text{Cheshta Bala}}$$
$$\text{Kashta Phala} = \sqrt{(60 - \text{Uchcha Bala}) \times (60 - \text{Cheshta Bala})}$$

Cheshta here is the Shadbala Cheshta of §6.1 **except for the Moon**. Kala Paksha for the Moon is doubled ($2E/3$) and capped at 60 in Kala Bala; using that cap here would force Moon Kashta $= 0$ near Full Moon. For Ishta–Kashta, Moon Cheshta $= \min(60, E/3)$ (undoubled elongation). Vakri grahas (Mars–Saturn) use $\max(\text{Cheshta}, 45)$ in this pair only. Engine: `chart.ishta_kashta`.

### 6.4 Baladi Avasthas (Age-based states)
Names and fruit **percentages** are the table in §6.6.1 (Bala 25%, Kumara 50%, Yuva 100%, **Vriddha 15%**, **Mrita 5%**). Odd signs use $0^\circ\!\rightarrow\!30^\circ$; even signs reverse. Engine stores the **name** (`chart.avasthas`); it does not multiply Shadbala by these percentages.

### 6.5 Vimsopaka Bala (20-Divisional Strength)
Vimsopaka Bala measures a planet's dignity across multiple divisional charts simultaneously.

**Shodasha Varga Scheme (16 Vargas used most commonly):**

| # | Varga | Division | Weightage (out of 20) |
|:---:|:---|:---:|:---:|
| 1 | D-1 (Rasi) | 1 | 3.5 |
| 2 | D-2 (Hora) | 2 | 1.5 |
| 3 | D-3 (Drekkana) | 3 | 1.5 |
| 4 | D-4 (Chaturthamsa) | 4 | 1.5 |
| 5 | D-7 (Saptamsa) | 7 | 1.5 |
| 6 | D-9 (Navamsa) | 9 | 3.0 |
| 7 | D-10 (Dasamsa) | 10 | 1.5 |
| 8 | D-12 (Dwadasamsa) | 12 | 1.5 |
| 9 | D-16 (Shodasamsa) | 16 | 1.0 |
| 10 | D-20 (Vimsamsa) | 20 | 1.0 |
| 11 | D-24 (Chaturvimsamsa) | 24 | 1.0 |
| 12 | D-27 (Bhamsa) | 27 | 0.5 |
| 13 | D-30 (Trimsamsa) | 30 | 0.5 |
| 14 | D-40 (Khavedamsa) | 40 | 0.5 |
| 15 | D-45 (Akshavedamsa) | 45 | 0.5 |
| 16 | D-60 (Shashtiamsa) | 60 | 0.5 |

The sixteen weightages as tabulated sum to **21**. Engine normalizes by $\sum w_i$ so the published 0–20 ceiling is kept:

**Calculation:**
1. For each Varga, determine planet's dignity in that chart:
   - Own sign = 20, Exalted = 20, Moolatrikona = 15, Friendly = 10, Neutral = 5, Enemy = 2, Debilitated = 0
2. $$\text{Vimsopaka Bala}(P) = \sum_{i=1}^{16} \text{dignity\_score}(P, \text{Varga}_i) \times \frac{\text{weight}_i}{\sum w}$$
3. Maximum possible = 20.00. Minimum = 0.00.

**Source:** BPHS Ch. 16–17, BVR Bhava & Graha Balas

### 6.6 Avasthas (Planetary States) — Complete Computation Rules

#### 6.6.1 Baladi Avastha (Age-Based — expanded with Even Sign reversal)
For **Odd signs** (Ar, Ge, Le, Li, Sg, Aq): Slabs proceed $0°→30°$.
For **Even signs** (Ta, Cn, Vi, Sc, Cp, Pi): Slabs are **reversed** ($30°→0°$).

| Slab (Odd Sign) | Slab (Even Sign) | Avastha | Strength % |
|:---:|:---:|:---|:---:|
| $0°–6°$ | $24°–30°$ | **Bala** (Infant) | 25% |
| $6°–12°$ | $18°–24°$ | **Kumara** (Adolescent) | 50% |
| $12°–18°$ | $12°–18°$ | **Yuva** (Youth — PRIME) | 100% |
| $18°–24°$ | $6°–12°$ | **Vriddha** (Old) | 15% |
| $24°–30°$ | $0°–6°$ | **Mrita** (Dead) | 5% |

**Source:** BPHS Ch. 45, Phaladeepika, Viveka Chudamani §1.10.9

#### 6.6.2 Jagradadi Avastha (Waking States)
Determination based on planet's sign relationship:

| Planet's Relationship to Sign | Avastha | Strength Multiplier |
|:---|:---|:---:|
| Own sign or Exalted | **Jaagrita** (Awake) | $1.0$ |
| Friendly sign | **Swapna** (Dreaming) | $0.5$ |
| Enemy sign or Debilitated | **Sushupta** (Sleeping) | $0.25$ |

$$\text{Avastha\_Modified\_Strength}(P) = \text{Base\_Strength}(P) \times \text{Multiplier}$$

#### 6.6.3 Deeptadi Avastha (Illumination States — 9 states)

| # | Avastha | Condition |
|:---:|:---|:---|
| 1 | **Deepta** (Blazing) | Planet exalted |
| 2 | **Swastha** (Comfortable) | Planet in own sign |
| 3 | **Mudita** (Delighted) | Planet in friend's sign |
| 4 | **Shanta** (Peaceful) | D1 **Neutral** *and* D9 dignity in Own / Exalt / MT / Friend. First matching row wins (combust and yuddha-loser override). |
| 5 | **Dina** (Weak/Sad) | Planet in neutral sign |
| 6 | **Vikala** (Distressed) | Planet combust |
| 7 | **Khala** (Wicked) | Planet in enemy sign |
| 8 | **Kopa** (Angry) | Planet defeated in Graha Yuddha |
| 9 | **Bheeta** (Frightened) | Planet debilitated |

### 6.7 Bhava Bala (House Strength) — Calculation Formula
Bhava Bala measures the strength of each house (bhava) in the chart.

$$\text{Bhava Bala} = \text{Bhavadhipati Bala} + \text{Bhava Dig Bala} + \text{Bhava Drishti Bala}$$

1. **Bhavadhipati Bala** = Shadbala of the house lord (total Shadbala value of the planet that lords the house).
2. **Bhava Dig Bala** (Directional strength of houses):
   - Houses 1, 4, 7, 10 (Kendras) get highest Dig Bala.
   - Compute: Bhava mid-point longitude → use the same Dig Bala formula as planets but applied to bhava sphutas.
3. **Bhava Drishti Bala** = Sum of aspects (Drishti Pinda values from §2.10) received by the bhava mid-point from all planets.
   - Benefic aspects add strength, malefic aspects subtract.

$$\text{Bhava Drishti Bala}(H) = \sum_{P} \text{Drishti\_Pinda}(P, H) \times \text{benefic\_sign}(P)$$

**Source:** BPHS Ch. 36–37, BVR Bhava & Graha Balas

---

## 7. Jaimini Astrology (Chara Karakas, Karakamsa & Arudha Padas)

### 7.1 Chara Karakas (Variable Significators)
- Determined by ranking planets by degree-in-sign ($\lambda \pmod{30}$) in descending order:
1. **7-Planet Scheme (Classical / KN Rao standard)**:
   - **AK** (Atmakaraka — Soul): Rank 1 (Highest degree)
   - **AmK** (Amatyakaraka — Career/Mind): Rank 2
   - **BK** (Bhatrikaraka — Guru/Father/Siblings): Rank 3
   - **MK** (Matrikaraka — Mother/Home): Rank 4
   - **PK** (Putrakaraka — Children/Intellect): Rank 5
   - **GK** (Gnatikaraka — Obstacles/Enemies): Rank 6
   - **DK** (Darakaraka — Spouse/Partner): Rank 7 (Lowest degree)
2. **8-Planet Scheme (Rath / Jaimini / JHora)**:
   - Includes Rahu using retrograde span: $\text{Rahu Effective Deg} = 30^\circ - (\lambda_\text{Rahu} \pmod{30})$. Ketu excluded.
   - Rank order (highest degree → lowest): **AK, AmK, BK, MK, PK, PiK, GK, DK**.
   - PK keeps the 7-planet rank-5 slot; **PiK is inserted as rank 6**. Assign from **this native’s** sorted degrees; do not reuse another chart’s karaka list.

### 7.2 Karakamsa & Jaimini Drishti
- **Karakamsa**: The Navamsa (D9) sign occupied by the Atmakaraka (AK).
- **Jaimini Rashi Drishti (Sign Aspects)** — from the **sign**, not the planet:
  - **Cardinal/Movable** (Aries, Cancer, Libra, Capricorn) aspect all **Fixed** signs except the adjacent one (the 2nd from it).
  - **Fixed** (Taurus, Leo, Scorpio, Aquarius) aspect all **Cardinal** signs except the adjacent one (the 12th from it).
  - **Dual** (Gemini, Virgo, Sagittarius, Pisces) aspect all **other Dual** signs (4th, 7th, 10th).
  - A planet in sign $S$ aspects every planet/house whose sign is in that aspect set.

Engine (any native): `chart.jaimini_drishti`.

### 7.3 Arudha Pada Calculation & 1/7 Exception Rule
For any house $H$ ($0 \le H \le 11$):
1. Find the sign lord $L$ of house $H$.
2. Calculate the distance $n$ from $H$ to $L$: $n = (S_L - H) \pmod{12}$. If $n = 0$, set $n = 12$.
3. Standard Arudha Sign: $A = (S_L + n) \pmod{12}$.
4. **Parashara 1/7 Exception Rule**:
   - If $A = H$ (1st from house) OR $A = (H + 6) \pmod{12}$ (7th from house):
   $$\text{Final Arudha} = (H + 9) \pmod{12} \quad (\text{10th from house } H)$$
5. **Key Padas**:
   - **AL (A1)**: Arudha Lagna (Public image, status).
   - **A7**: Dara Pada (Physical partnership, business transactions).
   - **UL (A12)**: Upapada Lagna (Marriage partner, legal union, marital stability). Dual school: BPHS/KN Rao = arudha of 12th (count from 12L); Rath/JHora may count from the 12th sign itself.
6. **Graha Arudhas**: For each planet $P$, compute the arudha of the **sign $P$ occupies** (same formula + 1/7 exception). Engine: `calc_graha_arudhas`.

---

## 8. Special Sensitive Points & Sahams

1. **Yogi Point, Yogi, Avayogi & SahaYogi**:
   $$\text{Yogi Point} = (\lambda_\text{Sun} + \lambda_\text{Moon} + 93^\circ 20') \pmod{360^\circ}$$
   - **Yogi Planet**: Nakshatra lord of the Yogi Point.
   - **SahaYogi Point** $= (\lambda_\text{Sun} + \lambda_\text{Moon} + 186^\circ 40') \pmod{360^\circ}$; **SahaYogi** = nakshatra lord of that point (JHora / COMBINED). *Not* the sign lord of the Yogi Point.
   - **Avayogi Point** $= (\lambda_\text{Sun} + \lambda_\text{Moon} + 280^\circ) \pmod{360^\circ}$ $=$ Yogi Point $+ 186^\circ 40'$; **Avayogi** = nakshatra lord of that point.
2. **Bhrigu Bindu (BB)**:
   - Midpoint of Rahu and Moon on the shorter arc:
   $$\text{BB} = \frac{\lambda_\text{Rahu} + \lambda_\text{Moon}}{2}$$
   - If $|\lambda_\text{Rahu} - \lambda_\text{Moon}| > 180^\circ$, adjust by adding $180^\circ \pmod{360^\circ}$.
3. **Vivaha Saham (Marriage Sensitive Point)**:
   - **Tajika Formula**:
     - Day Birth: $(\lambda_\text{ASC} + \lambda_\text{Moon} - \lambda_\text{Venus}) \pmod{360^\circ}$
     - Night Birth: $(\lambda_\text{ASC} + \lambda_\text{Venus} - \lambda_\text{Moon}) \pmod{360^\circ}$
   - **Parashara Formula**: $(\lambda_\text{ASC} + \lambda_\text{Venus} - \lambda_\text{Jupiter}) \pmod{360^\circ}$
4. **Part of Fortune (Pars Fortunae)**:
   - Day Birth: $(\lambda_\text{ASC} + \lambda_\text{Moon} - \lambda_\text{Sun}) \pmod{360^\circ}$
   - Night Birth: $(\lambda_\text{ASC} + \lambda_\text{Sun} - \lambda_\text{Moon}) \pmod{360^\circ}$
5. **Maandi & Gulika**:
   - Day duration = Sunset JD - Sunrise JD. Divided into 8 equal segments.
   - Saturn's segment gives Maandi/Gulika rising time (Sunday = 7th segment, Monday = 6th, Tuesday = 5th, Wednesday = 4th, Thursday = 3rd, Friday = 2nd, Saturday = 1st segment).
6. **Indu Lagna (wealth sphuta)**:
   Kalas: Sun 30, Moon 16, Mars 6, Mercury 8, Jupiter 10, Venus 12, Saturn 1.
   Sum kalas of 9th-lord from Lagna and 9th-lord from Moon; remainder $r = (k_1+k_2) \bmod 12$ (use 12 if $r=0$). Indu sign = $r$-th from Moon’s sign; longitude = that sign + Moon’s degree-in-sign.
7. **Tithi Lagna**: $\lambda_{\text{ASC}} + (\lambda_{\text{Moon}} - \lambda_{\text{Sun}}) \pmod{360^\circ}$.
8. **Viparita Lagna**: $\lambda_{\text{ASC}} + 180^\circ$ (equal 7th cusp).
9. **Mrityu sphutas**: Placidus 8th-cusp longitude, plus Gulika if computed (item 5 / §1.3).

Engine (any native): `chart.special_points`, `chart.extra_points`.

---

## 9. Yoga Detection Engine

### 9.1 Pancha Mahapurusha Yogas
Formed when a non-luminary planet is in **Own Sign or Exaltation** AND situated in a **Kendra (Houses 1, 4, 7, 10)**:
- **Mars** $\rightarrow$ **Ruchaka Yoga** (Courage, land ownership, leadership)
- **Mercury** $\rightarrow$ **Bhadra Yoga** (Intellect, commerce, communication mastery)
- **Jupiter** $\rightarrow$ **Hamsa Yoga** (Wisdom, spiritual dignity, universal respect)
- **Venus** $\rightarrow$ **Malavya Yoga** (Luxury, artistic genius, wealth, sensual refinement)
- **Saturn** $\rightarrow$ **Sasa Yoga** (Authority over masses, discipline, enduring power)

### 9.2 Viparita Raja Yogas (VRY)
Formed when Dusthana lords ($6\text{L}, 8\text{L}, 12\text{L}$) reside exclusively in Dusthana houses ($6, 8, 12$):
- **Harsha Yoga**: 6th lord in 6th, 8th, or 12th house (Immunity from enemies, robust health).
- **Sarala Yoga**: 8th lord in 6th, 8th, or 12th house (Fearlessness, hidden wealth, longevity).
- **Vimala Yoga**: 12th lord in 6th, 8th, or 12th house (Frugality, spiritual bliss, independence).

### 9.3 Classical Raj & Dhana Yogas
- **Raj Yogas**: Conjunction, mutual aspect, or Parivartana (exchange) between a Kendra lord ($1, 4, 7, 10$) and a Trikona lord ($1, 5, 9$).
- **Dhana Yogas**: Interconnections between wealth lords ($1\text{L}, 2\text{L}, 5\text{L}, 9\text{L}, 11\text{L}$).
- **Gaja Kesari Yoga**: Jupiter in a Kendra from Moon ($1, 4, 7, 10$ houses from Moon).
- **Kalatramooladdhana Yoga**: 7th lord situated in 2nd or 11th house (Wealth through spouse/partnership).

### 9.4 Doshas & Inauspicious Yogas
- **Kemadruma Yoga**: No planets (excluding Sun, Rahu, Ketu) in 2nd or 12th from Moon.
  - *Cancellation*: Planets in Kendra from Lagna or Moon in a Kendra.
- **Manglik / Kuja Dosha**: Mars placed in houses 1, 2, 4, 7, 8, or 12 from Lagna.
- **Kaal Sarp Yoga**: All 7 classical planets hemmed between the Rahu-Ketu nodal axis.
- **Sakata Yoga**: Moon placed in 6th, 8th, or 12th from Jupiter.
- **Ubhayachari / Vasi / Vesi**: Planets in 2nd and/or 12th from Sun.

### 9.5 Neecha Bhanga Raja Yoga (Cancellation of Debilitation) — Detection Conditions
A debilitated planet $P_{\text{deb}}$ receives **Neecha Bhanga** (cancellation of debilitation) if **ANY ONE** of these conditions is met:

| # | Condition | Formula / Check |
|:---:|:---|:---|
| 1 | Lord of $P_{\text{deb}}$'s debilitation sign is in Kendra from Lagna or Moon | `sign_lord(deb_sign) in kendra_from(lagna) OR kendra_from(moon)` |
| 2 | Lord of $P_{\text{deb}}$'s exaltation sign is in Kendra from Lagna or Moon | `sign_lord(exalt_sign) in kendra_from(lagna) OR kendra_from(moon)` |
| 3 | $P_{\text{deb}}$ is aspected by its debilitation sign lord | `has_aspect(sign_lord(deb_sign), P_deb)` |
| 4 | $P_{\text{deb}}$ is conjunct its exaltation sign lord | `same_sign(sign_lord(exalt_sign), P_deb)` |
| 5 | $P_{\text{deb}}$ is aspected by another planet exalted in the same sign | `exists Q: Q.is_exalted AND Q.sign == P_deb.sign AND has_aspect(Q, P_deb)` |
| 6 | The planet exalted in $P_{\text{deb}}$'s debilitation sign is in Kendra from Lagna or Moon | `planet_exalted_in(deb_sign) in kendra_from(lagna)` |
| 7 | $P_{\text{deb}}$ is retrograde (§2.9 — contested, but widely applied) | `P_deb.is_retrograde == True` |
| 8 | Two planets in mutual exchange such that one is debilitated and the other is exalted in that sign | Parivartana condition — see §9.6 |

**Strength of Neecha Bhanga**: More conditions met simultaneously = stronger cancellation. Single condition = partial cancellation. The yoga is strongest when the cancelling planet itself is strong (exalted/own sign/Kendra).

**Reduction**: If $P_{\text{deb}}$ with Neecha Bhanga is also in Dusthana (6/8/12 from Lagna), the cancellation is weakened. Source: Phaladeepika Ch. 7 Shloka 27, Viveka Chudamani §2.5.2.

### 9.6 Parivartana Yoga (Mutual Sign Exchange) — Detection & Classification
Two planets $P_A$ and $P_B$ form **Parivartana Yoga** if:
$$P_A \text{ is in sign owned by } P_B \quad \text{AND} \quad P_B \text{ is in sign owned by } P_A$$
i.e., `sign_lord(P_A.sign) == P_B AND sign_lord(P_B.sign) == P_A`.

**Classification by House Involvement:**

| Type | Condition | Classification |
|:---|:---|:---|
| **Maha Yoga** | Both houses are Kendras (1,4,7,10) or Trikonas (1,5,9) | `MAHA_PARIVARTANA` — Highly beneficial |
| **Kahala Yoga** | One house is Kendra/Trikona, other is 2nd, 3rd, or 11th | `KAHALA_PARIVARTANA` — Moderately beneficial |
| **Dainya Yoga** | One or both houses are Dusthana (6, 8, 12) | `DAINYA_PARIVARTANA` — Inauspicious |

**Special Rule — Viparita Parivartana**: If both exchanging lords are Dusthana lords (6L and 8L, or 8L and 12L, or 6L and 12L), this becomes a form of **Viparita Raja Yoga** rather than Dainya. Flag as `VIPARITA_PARIVARTANA`.

**Source:** BPHS Ch. 28, Laghu Parashari, Phaladeepika

### 9.7 Extended Yoga Catalogue — Detection Conditions
Each yoga below lists its EXACT formation conditions for computation:

#### A. Solar Yogas
| Yoga | Condition | Detection Formula |
|:---|:---|:---|
| **Budhaditya** | Sun and Mercury conjunct in same sign | `same_sign(Sun, Mercury) AND (Mercury NOT combust OR Mercury in own/exalted sign)` |
| **Vasi** | Planet(s) other than Moon in 12th from Sun | `exists P (P != Moon, Rahu, Ketu): house_from(P, Sun) == 12` |
| **Vesi** | Planet(s) other than Moon in 2nd from Sun | `exists P (P != Moon, Rahu, Ketu): house_from(P, Sun) == 2` |
| **Ubhayachari** | Planets in BOTH 2nd and 12th from Sun | `Vasi AND Vesi both True` |

#### B. Lunar Yogas
| Yoga | Condition | Detection Formula |
|:---|:---|:---|
| **Sunapha** | Planet(s) (excl Sun, Rahu, Ketu) in 2nd from Moon | `exists P (P != Sun, Ra, Ke): house_from(P, Moon) == 2` |
| **Anapha** | Planet(s) (excl Sun, Rahu, Ketu) in 12th from Moon | `exists P (P != Sun, Ra, Ke): house_from(P, Moon) == 12` |
| **Durudhara** | Planets in BOTH 2nd and 12th from Moon | `Sunapha AND Anapha both True` |
| **Kemadruma** | NO planets (excl Sun, Ra, Ke) in 2nd or 12th from Moon | `NOT Sunapha AND NOT Anapha` |
| **Kemadruma Cancellation** | Planet in Kendra from Lagna OR Moon in Kendra | `planet_in_kendra_from(Lagna) OR Moon in kendra` |
| **Gaja Kesari** | Jupiter in Kendra (1/4/7/10) from Moon | `house_from(Jupiter, Moon) in {1, 4, 7, 10}` |
| **Shakata** | Moon in 6th, 8th, or 12th from Jupiter | `house_from(Moon, Jupiter) in {6, 8, 12}` |
| **Shakata Cancellation** | Moon in Kendra from Lagna | `house_from(Moon, Lagna) in {1, 4, 7, 10}` |
| **Chandra-Mangal** | Moon and Mars conjunct in same sign | `same_sign(Moon, Mars)` |

#### C. Pancha Mahapurusha Yogas (already in §9.1 — additional cancellation rules)
| Bhanga (Cancellation) Condition | Check |
|:---|:---|
| Yoga planet is combust (§2.7) | `P.is_combust == True` → `PMP_status = WEAKENED` |
| Yoga planet is defeated in Graha Yuddha (§2.8) | `P.yuddha_loser == True` → `PMP_status = WEAKENED` |
| Yoga planet is aspected by a malefic lord of 6/8/12 | `has_aspect(dusthana_lord, P) AND dusthana_lord.is_natural_malefic` |
| Yoga planet is in Rashi Sandhi ($29°–1°$ boundary) | `P.degree_in_sign > 29.0 OR P.degree_in_sign < 1.0` |

#### D. Wealth & Raja Yogas
| Yoga | Condition | Detection Formula |
|:---|:---|:---|
| **Amala Yoga** | Natural benefic (Ju/Ve/Me/Moon) in 10th from Lagna or Moon | `exists P (P is natural_benefic): house_from(P, Lagna) == 10 OR house_from(P, Moon) == 10` |
| **Lakshmi Yoga** | 9th *or* 5th lord in own/exalt/MT **and** in a Kendra; Lagna lord powerful (own/exalt/MT or Kendra) | `(lord(9) OR lord(5)) dignity in {OWN, EXALTED, MT} AND house in {1,4,7,10} AND (lord(1) strong)`. 1L+9L conjunct in Lagna without 9L own/exalt is **Raja/Dhana**, not Lakshmi. |
| **Adhi Yoga** | Benefics in 6th, 7th, 8th from Moon | `count(benefics in houses 6,7,8 from Moon) >= 2` |
| **Dhana Yoga** | Lords of 1/2/5/9/11 in mutual connection (conjunction/aspect/exchange) | `mutual_connection(lord(2), lord(11)) OR mutual_connection(lord(5), lord(9))` etc. |
| **Raj Yoga** | Kendra lord + Trikona lord in conjunction/mutual aspect/exchange | `connection(kendra_lord, trikona_lord)` where kendra = {1,4,7,10} lords, trikona = {1,5,9} lords |

#### E. Inauspicious & Dosha Yogas
| Yoga | Condition | Detection Formula |
|:---|:---|:---|
| **Guru-Chandal** | Jupiter conjunct Rahu | `same_sign(Jupiter, Rahu)` |
| **Graha Malika** | 3+ planets in consecutive signs (chain) | `count_consecutive_occupied_signs() >= 3` |
| **Kaal Sarp** | All 7 planets (Su-Sa) on one side of Rahu-Ketu axis | See existing §9.4 |
| **Pitra Dosha** | Sun conjunct Rahu OR 9th lord conjunct Rahu OR Rahu in 9th | `same_sign(Sun, Rahu) OR same_sign(lord(9), Rahu) OR house(Rahu) == 9` |
| **Kendradhipati Dosha** | Natural benefic owns a Kendra (4/7/10) | `Jupiter/Venus/Mercury/Moon owns house 4 OR 7 OR 10` → flag as functional neutral |

---

## 10. Transit Engine & Gochara with Vedha

### 10.1 Double Transit (Parashara Timing Anchor)
The primary predictive rule for life events: Event materialization requires simultaneous activation of the target house by **Jupiter** (grace/expansion) and **Saturn** (manifestation/karma) via occupation or aspect.

### 10.2 Gochara & Vedha (Transits from Moon)
| Transiting Planet | Favorable Houses from Moon | Vedha (Obstruction) Houses |
|:---|:---|:---|
| **Sun** | 3, 6, 10, 11 | 9, 12, 4, 5 (respectively) |
| **Moon** | 1, 3, 6, 7, 10, 11 | 5, 9, 12, 2, 4, 8 |
| **Mars** | 3, 6, 11 | 12, 9, 5 |
| **Mercury** | 2, 4, 6, 8, 10, 11 | 5, 3, 9, 1, 8, 12 |
| **Jupiter** | 2, 5, 7, 9, 11 | 12, 4, 3, 10, 8 |
| **Venus** | 1, 2, 3, 4, 5, 8, 9, 11, 12 | 8, 7, 1, 10, 9, 5, 11, 6, 3 |
| **Saturn** | 3, 6, 11 | 12, 9, 5 |
| **Rahu / Ketu** | 3, 6, 11 | 12, 9, 5 |

*Vedha Rule*: If a planet transits a favorable house, but another planet (except Sun-Saturn / Moon-Mercury father-son pairs) transits its corresponding Vedha house, the favorable result is obstructed.

### 10.3 Sade-Sati Detection (7.5 Year Saturn Transit)
Sade-Sati occurs when **transiting Saturn** is within $\pm 1$ sign of the natal Moon sign.

**Algorithm:**
```
moon_sign_idx = floor(natal_moon_longitude / 30)   # 0-based
sat_transit_sign = floor(transit_saturn_longitude / 30)   # 0-based

phase_12th = (moon_sign_idx - 1) % 12   # sign before Moon
phase_1st  = moon_sign_idx               # Moon's sign
phase_2nd  = (moon_sign_idx + 1) % 12   # sign after Moon

if sat_transit_sign == phase_12th:
    sade_sati = True, phase = "RISING" (1st phase, ~2.5 years)
elif sat_transit_sign == phase_1st:
    sade_sati = True, phase = "PEAK" (2nd phase, ~2.5 years)
elif sat_transit_sign == phase_2nd:
    sade_sati = True, phase = "SETTING" (3rd phase, ~2.5 years)
else:
    sade_sati = False
```

**Ashtama Shani** (Saturn in 8th from Moon):
```
ashtama_shani = (sat_transit_sign == (moon_sign_idx + 7) % 12)
```

**Dhaiyya / Kantaka Shani** (Saturn in 4th from Moon):
```
kantaka_shani = (sat_transit_sign == (moon_sign_idx + 3) % 12)
```

Signs and longitudes are **this native’s natal Moon** vs **transiting Saturn** on the query date. Engine: `chart.sade_sati_for(date)`.

### 10.4 Bhrigu Bindu Transit Activation
The **Bhrigu Bindu (BB)** is a sensitive point. When a transiting planet (especially Jupiter or Saturn) conjuncts or aspects the BB degree, events related to the BB-axis activate.

**BB Calculation (already in §8):**
$$\text{BB} = \frac{\lambda_{\text{Rahu}} + \lambda_{\text{Moon}}}{2}$$
Adjust: If $|\lambda_{\text{Rahu}} - \lambda_{\text{Moon}}| > 180°$, add $180°$ before dividing and take $\pmod{360°}$.

**Transit Activation Check** (snapshot, `check_bb_transit`):
```
orb(P) = 5° if P in {Jupiter, Saturn} else 2°
for each transiting planet P:
    delta = shortest_arc(λ_P, λ_BB)
    if delta <= orb(P): BB is activated by P
```
Dated BB **windows** in `chart.time_pack` use a tighter $1^\circ$ scan (Moon daily, Ju/Sa/Sun every 3 days) so consecutive hits collapse to intervals. Engine: `chart.transits_for(date)["bb_transit"]`.

### 10.5 Sign Ingress (exact sign-change JD)
For one body $P$ on $[t_0, t_1]$:
1. Sidereal $\lambda, \dot\lambda$ from a **single-body** Swiss call (`sidereal_lon_speed`; Ketu = Rahu $+180^\circ$ with the **same** $\dot\lambda$).
2. Adaptive step toward the next $30^\circ$ boundary: $\Delta t \approx 0.85 \times \text{dist}/|\dot\lambda|$, capped.
3. On sign change, 24-iteration JD bisection to $\lt 0.02\,\text{d}$.
Ketu mean motion is retrograde (§1.3). Engine: `find_sign_ingress` / `chart.sign_ingresses` / `chart.raw_layers["ingress_2025_2043"]`.

---

## 11. Tajika Varshaphala (Annual Horoscopy)

### 11.1 Solar Return (Varsha Pravesh) Precision Algorithm
Finds the exact Julian Day $JD$ where:
$$\lambda_\text{Sun}(JD) = \lambda_\text{Sun}(\text{Birth } JD) \pmod{360^\circ}$$
Refined using Newton-Raphson iteration:
$$JD_{n+1} = JD_n + \frac{(\lambda_\text{target} - \lambda_\text{current})}{\text{Daily Sun Speed}}$$

### 11.2 Muntha (Progressed Annual Sign)
$$\text{Muntha Sign Index} = (\text{Birth Lagna Index} + \text{Age in Completed Years}) \pmod{12}$$
- Auspicious in Houses 1, 4, 5, 7, 9, 10, 11; Inauspicious in Dusthanas (6, 8, 12).

### 11.3 Degree-Based Tajika Aspects & Orbs (Deeksha)
| Aspect | Exact Angle | Allowable Orb (Pratyaksha Deeksha) | Nature |
|:---|:---:|:---:|:---|
| **Conjunction** (Yuti) | $0^\circ$ | $\pm 8^\circ$ | Variable (depends on planets) |
| **Sextile** (Pratyaksha Mitra) | $60^\circ$ | $\pm 5^\circ$ | Semi-friendly |
| **Square** (Pratyaksha Satru) | $90^\circ$ | $\pm 7^\circ$ | Openly inimical / challenging |
| **Trine** (Gupt Mitra) | $120^\circ$ | $\pm 7^\circ$ | Harmonious / very friendly |
| **Opposition** (Pratyaksha Satru) | $180^\circ$ | $\pm 8^\circ$ | Direct conflict / separation |

### 11.4 Tajika Yogas
1. **Itthasala (Muthasila)**: Faster planet is behind the slower planet, within aspect orb, moving toward exact aspect (Applying). Event materializes.
2. **Ishrafa (Musaripha)**: Faster planet has passed the slower planet by more than $1^\circ$ (Separating). Event denied or already past.
3. **Nakta Yoga**: Two significators have no direct aspect, but a faster intermediary planet separates from one and applies to the other (Translation of light).
4. **Yamaya Yoga**: Faster planet applies to slower, but a third planet obstructs by perfecting an aspect first (Prohibition).

---

## 12. Kundali Matching (Ashtakoota Guna Milan)

Total: **36 Gunas (Points)** based on Moon nakshatras and Moon signs of groom and bride:

| # | Koota | Max Points | Measurement Basis | Rules & Scoring |
|:---:|:---|:---:|:---|:---|
| 1 | **Varna** | 1 | Spiritual ego / caste | Boy Varna $\ge$ Girl Varna $\rightarrow$ 1 pt; else 0 pt.<br>(Brahmin=1, Kshatriya=2, Vaishya=3, Shudra=4). |
| 2 | **Vashya** | 2 | Mutual attraction | Same category $\rightarrow$ 2 pts; Compatible pair $\rightarrow$ 1 pt; Incompatible $\rightarrow$ 0 pts. |
| 3 | **Tara** | 3 | Destiny / longevity | Count Boy $\rightarrow$ Girl and Girl $\rightarrow$ Boy $\pmod 9$. Remainder $\notin \{3, 5, 7\}$ (Vipat, Pratyak, Naidhana). Both good $\rightarrow$ 3 pts; One good $\rightarrow$ 1.5 pts; Both bad $\rightarrow$ 0 pts. |
| 4 | **Yoni** | 4 | Biological / sexual compatibility | Same animal $\rightarrow$ 4 pts; Friendly $\rightarrow$ 3 pts; Neutral $\rightarrow$ 2 pts; Enemy $\rightarrow$ 1 pt; Sworn enemy $\rightarrow$ 0 pts. |
| 5 | **Graha Maitri** | 5 | Psychological harmony | Moon sign lords mutual friends $\rightarrow$ 5 pts; Friend+Neutral $\rightarrow$ 4 pts; Both neutral $\rightarrow$ 3 pts; Friend+Enemy $\rightarrow$ 1 pt; Both enemies $\rightarrow$ 0 pts. |
| 6 | **Gana** | 6 | Temperament | Deva, Manushya, Rakshasa.<br>Same Gana $\rightarrow$ 6 pts; Deva+Manushya $\rightarrow$ 6 pts; Manushya+Rakshasa $\rightarrow$ 1 pt; Deva+Rakshasa $\rightarrow$ 0 pts. |
| 7 | **Bhakoot** | 7 | Health, family welfare | Distance between Moon signs. Dosha if $2/12$ (Dhan-Vyay) or $6/8$ (Rog-Mrityu) $\rightarrow$ 0 pts; else 7 pts.<br>*Cancelled* if sign lords are identical or mutual friends. |
| 8 | **Nadi** | 8 | Genetic / dosha constitution | Aadi (Vata), Madhya (Pitta), Antya (Kapha).<br>Different Nadi $\rightarrow$ 8 pts; Same Nadi $\rightarrow$ 0 pts (Nadi Dosha).<br>*Cancelled* if same nakshatra with different padas or same sign. |

- **Score Evaluation**:
  - $\ge 28$ Gunas: Excellent / Outstanding match.
  - $21 - 27$ Gunas: Good / Highly recommended.
  - $18 - 20$ Gunas: Average / Acceptable.
  - $< 18$ Gunas: Inauspicious / Not recommended.

---

## 13. Kakshya Sub-division System

### 13.1 Kakshya Division Architecture
Every sign ($30^\circ$) is divided into 8 equal segments called **Kakshyas**, each spanning:
$$\text{Kakshya Span} = \frac{30^\circ}{8} = 3^\circ 45' = 3.75^\circ$$

The 8 Kakshya lords follow an invariant Parashari order from slowest to fastest planet + Lagna:
1. **Kakshya 1** ($00^\circ 00' - 03^\circ 45'$): **Saturn**
2. **Kakshya 2** ($03^\circ 45' - 07^\circ 30'$): **Jupiter**
3. **Kakshya 3** ($07^\circ 30' - 11^\circ 15'$): **Mars**
4. **Kakshya 4** ($11^\circ 15' - 15^\circ 00'$): **Sun**
5. **Kakshya 5** ($15^\circ 00' - 18^\circ 45'$): **Venus**
6. **Kakshya 6** ($18^\circ 45' - 22^\circ 30'$): **Mercury**
7. **Kakshya 7** ($22^\circ 30' - 26^\circ 15'$): **Moon**
8. **Kakshya 8** ($26^\circ 15' - 30^\circ 00'$): **Lagna**

### 13.2 Transit Kakshya Activation Principle
When a transiting planet passes through a sign, its transit fruit in a given $3^\circ 45'$ arc is conditioned by whether the **Kakshya Lord** of that segment contributed a benefic bindu ($1$) to that transiting planet's natal BAV in that sign:
- If BAV Contribution = $1$: Transit yields positive, unhindered results during that sub-arc.
- If BAV Contribution = $0$: Transit yields friction, delays, or negative results.

---

## 14. Panchang Elements — Computation

The five limbs of the Panchang:

### 14.1 Tithi (Lunar Day)
$$\text{Tithi Number (1-30)} = \left\lfloor \frac{\lambda_{\text{Moon}} - \lambda_{\text{Sun}}}{12°} \right\rfloor + 1$$
Tithi 1–15 = Shukla Paksha (waxing). Tithi 16–30 = Krishna Paksha (waning).
Each Tithi = $12°$ of elongation between Moon and Sun.

**Tithi Lord Assignment:**
| Tithis | Lord |
|:---|:---|
| 1, 6, 11 (Nanda) | Venus |
| 2, 7, 12 (Bhadra) | Mercury |
| 3, 8, 13 (Jaya) | Mars |
| 4, 9, 14 (Rikta) | Saturn |
| 5, 10, 15 (Purna) | Jupiter |

### 14.2 Karana (Half Tithi)
$$\text{Karana Number (1-60)} = \left\lfloor \frac{\lambda_{\text{Moon}} - \lambda_{\text{Sun}}}{6°} \right\rfloor + 1$$
There are 11 Karanas (7 repeating: Bava, Balava, Kaulava, Taitila, Garija, Vanija, Vishti + 4 fixed).

### 14.3 Yoga (of the Day — Nithya Yoga)
$$\text{Yoga Number (1-27)} = \left\lfloor \frac{\lambda_{\text{Moon}} + \lambda_{\text{Sun}}}{13°20'} \right\rfloor + 1 = \left\lfloor \frac{\lambda_{\text{Moon}} + \lambda_{\text{Sun}}}{13.333°} \right\rfloor + 1$$
27 Yogas from Vishkambha (1) to Vaidhriti (27).

### 14.4 Vara (Weekday)
Sunday = 0, Monday = 1, ..., Saturday = 6.
`vara = weekday(julian_day_number)` — standard astronomical calculation.
**Vara Lord**: Su, Mo, Ma, Me, Ju, Ve, Sa (in order Sun–Sat).

### 14.5 Nakshatra (from Moon)
Already covered in §2 constants. For Panchang:
$$\text{Nakshatra Number (1-27)} = \left\lfloor \frac{\lambda_{\text{Moon}}}{13°20'} \right\rfloor + 1$$

### 14.6 Hora (Planetary Hour) Lord — Calculation Engine
The day (from local sunrise to next local sunrise) is divided into **24 planetary Horas** (12 day Horas + 12 night Horas).

#### A. Dynamic Proportional Hora Lengths
Let $T_{\text{rise}}$ be sunrise on the day of birth, $T_{\text{set}}$ be sunset, and $T_{\text{next\_rise}}$ be the subsequent sunrise:
$$\text{Day Hora Duration } (D_{\text{day}}) = \frac{T_{\text{set}} - T_{\text{rise}}}{12}$$
$$\text{Night Hora Duration } (D_{\text{night}}) = \frac{T_{\text{next\_rise}} - T_{\text{set}}}{12}$$

For local birth time $t$:
- If $T_{\text{rise}} \le t < T_{\text{set}}$ (Day Birth):
  $$\text{Hora Index } k = \left\lfloor \frac{t - T_{\text{rise}}}{D_{\text{day}}} \right\rfloor \quad (k \in \{0, 1, \dots, 11\})$$
- If $t \ge T_{\text{set}}$ (Night Birth, before midnight or after):
  $$\text{Hora Index } k = 12 + \left\lfloor \frac{t - T_{\text{set}}}{D_{\text{night}}} \right\rfloor \quad (k \in \{12, 13, \dots, 23\})$$
- If $t < T_{\text{rise}}$: The birth belongs to the **astrological previous weekday**; compute relative to previous day's sunset.

#### B. Chaldean Order & Hourly Lord Progression
Planetary sequence follows the classical descending Chaldean order (by orbital distance/speed):
$$\text{Chaldean Sequence: } \text{Saturn (0)} \rightarrow \text{Jupiter (1)} \rightarrow \text{Mars (2)} \rightarrow \text{Sun (3)} \rightarrow \text{Venus (4)} \rightarrow \text{Mercury (5)} \rightarrow \text{Moon (6)}$$

**Starting Lord of 1st Hora ($k=0$) = Lord of the Day (Vara Lord):**
| Weekday (from Sunrise) | Vara Lord | Chaldean Base Index ($B_{\text{vara}}$) |
|:---|:---|:---:|
| **Sunday** | Sun | **3** |
| **Monday** | Moon | **6** |
| **Tuesday** | Mars | **2** |
| **Wednesday** | Mercury | **5** |
| **Thursday** | Jupiter | **1** |
| **Friday** | Venus | **4** |
| **Saturday** | Saturn | **0** |

**Hora Lord Formula for Hora $k$:**
$$\text{Hora Lord Index} = (B_{\text{vara}} + k) \pmod 7$$
Lookup in Chaldean sequence: $\{0:\text{Saturn}, 1:\text{Jupiter}, 2:\text{Mars}, 3:\text{Sun}, 4:\text{Venus}, 5:\text{Mercury}, 6:\text{Moon}\}$.

All five limbs use **this native’s** $\lambda_{\text{Sun}}$, $\lambda_{\text{Moon}}$, weekday from local sunrise, and rise/set at the birth lat/lon. Engine: `chart.panchang`.

---

## 15. Pranapada (Vitality Point) — Computation Formula

Pranapada is the ascendant degree at the exact moment of the first breath.

**Simplified Calculation (BPHS method):**
1. Calculate the Ishta Ghati (elapsed ghatis from sunrise to birth).
2. $$\text{Pranapada Longitude} = \lambda_{\text{Lagna}} + (\text{Ishta Ghati} \times 0.24°)$$
3. Reduce $\pmod{360°}$ to get the Pranapada sign and degree.

**Alternative Parashari Formula:**
- For Sun in Movable sign: $\text{PP} = (\text{Birth Time fraction of day} \times 360° \times 2) + \lambda_{\text{Sun}} \pmod{360°}$
- For Sun in Fixed sign: Add $240°$ to the above.
- For Sun in Dual sign: Add $120°$ to the above.

**Source:** BPHS Ch. 3

---

## 16. Extended Sahams (Arabic Parts / Tajika)

All Sahams follow the generic formula:
$$\text{Saham} = (\lambda_{\text{ASC}} + \lambda_A - \lambda_B) \pmod{360°}$$

**Day/Night reversal**: For most Sahams, swap $A$ and $B$ for night births (Sun below horizon).

| # | Saham Name | $A$ (Day) | $B$ (Day) | Signification |
|:---:|:---|:---|:---|:---|
| 1 | Punya (Fortune) | Moon | Sun | General fortune |
| 2 | Vidya (Education) | Sun | Moon | Learning ability |
| 3 | Vivaha (Marriage) | Venus | Moon (Tajika) | Marriage timing |
| 4 | Putra (Children) | Jupiter | Moon | Children |
| 5 | Pitri (Father) | Saturn | Sun | Father's welfare |
| 6 | Matri (Mother) | Moon | Venus | Mother's welfare |
| 7 | Bhratri (Siblings) | Jupiter | Saturn | Siblings |
| 8 | Roga (Disease) | Saturn | Mars | Health issues |
| 9 | Mrityu (Death) | Moon | 8th cusp | Longevity |
| 10 | Karma (Action) | Mars | Mercury | Career |
| 11 | Paradesa (Foreign) | Saturn | 9L | Foreign travel |
| 12 | Bandhu (Relatives) | Mercury | Moon | Extended family |
| 13 | Jalapatna (Water Risk) | 15° Cancer | Saturn | Water danger |
| 14 | Mangal (Auspicious) | Jupiter | Mars | General auspiciousness |
| 15 | Sastra (Weapons) | Saturn | Mars | Injury from weapons |
| 16 | Gaurava (Honour) | Jupiter | Sun | Reputation |

**Source:** Tajika Neelakanthi, MS Mehta, Varshaphala texts

---

## 17. Manglik / Kuja Dosha — Complete Detection Algorithm

**Formation Condition:** Mars placed in houses **1, 2, 4, 7, 8, or 12** from:
- Lagna (primary check)
- Moon (secondary check)
- Venus (tertiary check — used by some South Indian authorities)

```
is_manglik_from(reference) =
    house_of(Mars, reference) in {1, 2, 4, 7, 8, 12}

manglik_score = sum([
    is_manglik_from(Lagna) * 2,   # Weight 2 for Lagna
    is_manglik_from(Moon) * 1,    # Weight 1 for Moon
    is_manglik_from(Venus) * 1    # Weight 1 for Venus (optional)
])
```

**Cancellation Conditions (Dosha Bhanga):**
| # | Condition | Check |
|:---:|:---|:---|
| 1 | Mars in own sign (Aries/Scorpio) | `Mars.sign in {Aries, Scorpio}` |
| 2 | Mars in exaltation (Capricorn) | `Mars.sign == Capricorn` |
| 3 | Mars conjunct or aspected by Jupiter | `same_sign(Mars, Jupiter) OR has_full_aspect(Jupiter, Mars)` |
| 4 | Mars conjunct or aspected by benefic Moon (Shukla Paksha, waxing) | `same_sign(Mars, Moon) AND Moon.paksha == SHUKLA` |
| 5 | Mars in Leo or Aquarius | `Mars.sign in {Leo, Aquarius}` |
| 6 | 7th lord in Kendra or Trikona | `lord(7) in houses {1,4,5,7,9,10}` |
| 7 | Venus in 7th house | `house(Venus) == 7` |
| 8 | Saturn in 1st, 4th, 7th, 8th, or 12th (Mars-like Dosha from both partners cancels mutually) | Comparative chart check |

**Source:** BPHS, Phaladeepika, KP Reader 4, marriage matching texts

---

## 18. Bhavat Bhavam — Computation Rule

The **Bhavat Bhavam** (house from house) principle states that for any house $H$, the supplementary house is:
$$\text{BhB}(H) = (2H - 1) \pmod{12} + 1$$

Or equivalently: Count $H$ houses from house $H$.

| Primary House | Bhavat Bhavam House | Shared Signification |
|:---:|:---:|:---|
| 1st | 1st | Self (identity) |
| 2nd | 3rd | Resources / effort |
| 3rd | 5th | Initiative / creativity |
| 4th | 7th | Comfort / partnerships |
| 5th | 9th | Children / dharma |
| 6th | 11th | Enemies / gains |
| 7th | 1st | Partner / self-reflection |
| 8th | 3rd | Transformation / courage |
| 9th | 5th | Fortune / intellect |
| 10th | 7th | Career / public partnerships |
| 11th | 9th | Gains / dharmic merit |
| 12th | 11th | Losses / unfulfilled desires |

**Usage Rule**: When analyzing house $H$, also check the condition of house $\text{BhB}(H)$ and its lord for confirmation. Source: Viveka Chudamani §1.10.3.

---

## 19. Marriage Timing — Conditional Rules

Marriage event detection requires convergence of multiple conditions:

**Dasha Condition:**
- Dasha/Antardasha of ANY of: 7th lord, Venus, planets in 7th, Navamsa Lagna lord, UL lord, DK (Darakaraka).
- `dasha_lord in {lord(7), Venus, planets_in(7), navamsa_lagna_lord, UL_lord, darakaraka}`

**Transit Condition (Double Transit — §10.1):**
- Jupiter AND Saturn must simultaneously transit or aspect the 7th house OR 1st house OR Upapada (UL).
- `(Jupiter transits/aspects house_7 OR house_1 OR UL) AND (Saturn transits/aspects house_7 OR house_1 OR UL)`

**Navamsa Cross-Check:**
- 7th lord of D-9 should NOT be in Dusthana (6/8/12) in D-9 for smooth marriage.
- Venus and Jupiter should be reasonably strong in D-9.

**Jaimini Timing:**
- Chara Dasha sign should contain or aspect DK, 7th from UL, or A7 (Arudha of 7th house).

**Source:** KN Rao (*Timing of Marriage*), Trivedi (*Predicting Marriage*), BPHS, Jaimini Sutras

---

## 20. Longevity (Ayurdaya) — Classification Algorithm

**Three Pairs Method (BPHS / Phaladeepika):**
Classify using three independent pair checks, then take the majority verdict.

| Pair # | Elements Compared | Classification Rule |
|:---:|:---|:---|
| **Pair 1** | Lagna + 8th lord | Both in Chara → Alpaayu; Both in Sthira → Purnaayu; Both in Dvisvabhava → Madhyaayu; Mixed → use Pindayu formula |
| **Pair 2** | Lagna lord + Moon sign lord | Same classification rules as Pair 1 |
| **Pair 3** | Lagna + Hora Lagna | Same classification rules as Pair 1 |

**Longevity Ranges:**
| Classification | Age Range |
|:---|:---|
| **Alpaayu** (Short) | 0–32 years |
| **Madhyaayu** (Medium) | 33–66 years |
| **Purnaayu** (Full) | 67–100 years |

**Majority Verdict**: If 2 out of 3 pairs agree, that classification applies.

**Source:** BPHS Ch. 43–44, Phaladeepika Ch. 14, Jataka Parijata

---

## 21. Krishnamurti Paddhati (KP System) — Calculation Engine

KP event timing uses **cusp sub-lords**, not Parashari house lords. Every longitude (planet, lagna, or house cusp) is reduced to Sign lord / Star lord / Sub lord / SSL / SSSL by the same walk of Vimshottari proportions. Houses may be **Placidus** (unequal, from the native’s lat/lon) or **Equal-bhava** (same degree as that native’s Lagna in each sign). Compute **both**; do not copy another chart’s CSL table.

### 21.1 Astronomical Foundations
- **Ayanamsha (KP proper)**: KP Old or KP New / KP Straightline. Swiss: `swe.SIDM_KRISHNAMURTI`. Engine natal default is True Citra (`"lahiri"`); pass `ayanamsha="krishnamurti"` when KP-ayanamsha longitudes are required.
- **House System A — Placidus (KP standard)**: `swe.houses_ex(jd_ut, lat, lon, b'P', swe.FLG_SIDEREAL)` at **this** native’s coordinates. House $H_i$ runs from cusp $\lambda_{C_i}$ to $\lambda_{C_{i+1}}$. MC = 10th cusp.
- **House System B — Equal-bhava**: cusp of house $H$ =
  $$\lambda_{C_H} = \lambda_{\text{ASC}} + 30^\circ(H-1) \pmod{360^\circ}$$
  i.e. the **same degree-in-sign as this native’s Lagna** in each successive sign. Occupancy: house $= \lfloor((\lambda_P - \lambda_{\text{ASC}}) \bmod 360) / 30\rfloor + 1$.
- Whether the two systems share cusp *signs* (no interception) depends on latitude. Cusp **sub-lords** generally differ except where the two longitudes fall in the same Vimshottari sub.

### 21.2 Coordinates for Any Point $\lambda$ (Sign / Star / Sub / SSL / SSSL)
Apply to every planet, Lagna, and every house cusp. Let $\lambda \in [0, 360)$. Five walks: sign lord, star lord, sub-lord, sub-sub lord (SSL), sub-sub-sub lord (SSSL).

1. **Sign Lord (Rashi Lord)**:
   $$\text{Sign Index } S = \lfloor \lambda / 30^\circ \rfloor \quad (0=\text{Aries}\dots 11=\text{Pisces})$$
   Sign lord = standard lordship table (§2.1).

2. **Star Lord (Nakshatra / Constellation Lord)**:
   $$\text{Nakshatra Index } N = \lfloor \lambda / 13^\circ 20' \rfloor \quad (0\dots 26)$$
   Star lord = Vimshottari lord of that nakshatra. Cycle from Ashwini:  
   Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury (repeats).  
   Equivalent lord-index: $N \bmod 9$ on that cycle.

3. **Sub-Lord (Upa-Pati)**:
   Each nakshatra ($13^\circ 20' = 800'$) is split into 9 **unequal** subs in Vimshottari proportion, **starting from the star lord**:
   $$\text{Sub-Arc}(P) = 13^\circ 20' \times \frac{\text{Years}(P)}{120} = 800' \times \frac{\text{Years}(P)}{120}$$

   | Planet | Dasha Years | Arc Span | Deg-Min-Sec |
   |:---|:---:|:---:|:---|
   | Ketu | 7 | $46.6667'$ | $0^\circ 46' 40''$ |
   | Venus | 20 | $133.3333'$ | $2^\circ 13' 20''$ |
   | Sun | 6 | $40.0000'$ | $0^\circ 40' 00''$ |
   | Moon | 10 | $66.6667'$ | $1^\circ 06' 40''$ |
   | Mars | 7 | $46.6667'$ | $0^\circ 46' 40''$ |
   | Rahu | 18 | $120.0000'$ | $2^\circ 00' 00''$ |
   | Jupiter | 16 | $106.6667'$ | $1^\circ 46' 40''$ |
   | Saturn | 19 | $126.6667'$ | $2^\circ 06' 40''$ |
   | Mercury | 17 | $113.3333'$ | $1^\circ 53' 20''$ |
   | **Total** | **120** | **$800'$** | **$13^\circ 20'$** |

   Algorithm (`_get_kp_sublord` in `ephemeris.py`):
   ```
   degree_in_nak = λ mod 13°20'
   i = index of star_lord in Vimshottari order
   accumulated = 0
   for k in 0..8:
       sub = Vimshottari[(i + k) mod 9]
       span = 13°20' × Years(sub) / 120
       if accumulated + span > degree_in_nak: return sub
       accumulated += span
   ```

4. **Sub-Sub Lord (SSL)**:
   Inside the chosen sub-arc, repeat the same 9-way split **starting from the sub-lord**:
   $$\text{Sub-Sub Arc}(P_1, P_2) = \text{Sub-Arc}(P_1) \times \frac{\text{Years}(P_2)}{120}$$
   Walk $P_2$ through Vimshottari from $P_1$ until the remainder of `degree_in_nak − sub_start` falls in that sub-sub.

5. **Sub-Sub-Sub Lord (SSSL)** — fifth KP level, same `_walk_vimshottari` as SSL:
   Remainder inside the SSL arc; sequence **starts from the SSL**. This is a full lord, not a hint. Engine: `kp_sssl_lord(λ)` / `kp_chain(λ)["sssl_lord"]`.

### 21.3 Planet-wise KP chain (natal)
For Lagna and each of the 9 grahas of **this native**, store Sign / Star / Sub / SSL / SSSL from that body’s $\lambda$ (algorithm 21.2). Engine: `sign_lord`, `nakshatra_lord`, `sub_lord`, `sub_sub_lord` on every position dict; `kp_chain(λ)` adds `sssl_lord` and `kp_249`.

*Worked example (Aditya, verification only — do not reuse as a formula):* Lagna Venus/Rahu/Rahu · Sun Mercury/Moon/Mercury · Moon Jupiter/Venus/Mercury · Mars Sun/Venus/Rahu · Mercury Venus/Rahu/Ketu · Jupiter Venus/Moon/Saturn · Venus Venus/Jupiter/Jupiter · Saturn Venus/Sun/Mercury · Rahu Mercury/Jupiter/Ketu · Ketu Jupiter/Venus/Ketu.

### 21.4 House-cusp KP (CSL) — two systems
**Cusp Sub-Lord (CSL)** of house $H$ = sub-lord of $\lambda_{C_H}$ computed for **this** native. Event of house $H$ is timed by that CSL (and its star).

**Equal-bhava:** $\lambda_{C_H} = \lambda_{\text{ASC}} + 30^\circ(H-1)$. Star/sub/sub-sub = four-fold coords of that longitude. There is no fixed “odd houses Rahu / even houses Ketu” rule — that pattern appears only when Lagna sits in a particular sub (e.g. Swati-Rahu-Rahu near $7^\circ22'$ Libra).

**Placidus:** same four-fold algorithm on Swiss Placidus cusp longitudes. CSL of house $H$ matches equal-bhava **only** when both longitudes fall in the same Vimshottari sub. Always compute both systems; never assume 7H (or any house) has the same CSL as another chart.

### 21.5 Occupancy of a KP house
A planet **occupies** house $H$ if
$$\lambda_{C_H} \le \lambda_P < \lambda_{C_{H+1}}$$
(wrap at 360°). Use Placidus cusps for KP occupancy; use equal-bhava occupancy only when reading the equal table. Occupancy ≠ rashi house.

### 21.6 The 1 to 249 Sub-Division System
Walk the 27 nakshatras in order. Inside each nakshatra walk the 9 Vimshottari subs starting from that nakshatra’s star lord (same spans as §21.2). Number each piece sequentially from **KP-1**.

- 27 × 9 = 243 theoretical subs.
- A sub whose open-closed interval $(\lambda_{\text{start}}, \lambda_{\text{end}}]$ contains a $30^\circ$ sign boundary is **split into two numbered zones** (same star + same sub lord, two KP numbers). Exactly **six** subs split this way (the other sign junctions fall on a sub boundary or a nakshatra start). $243 + 6 = 249$.
- KP-1 = Aries $0^\circ$ / Ashwini-Ketu-Ketu. KP-249 = last piece of Revati-Mercury (Pisces).
- For any $\lambda$: find the unique zone with $\lambda_{\text{start}} \le \lambda < \lambda_{\text{end}}$ (wrap: $\lambda=0$ is KP-1; $\lambda=360$ is not used). Engine: `kp_249_index(λ)` / `chart.kp["planets"][P]["kp_249"]`.

### 21.7 Ruling Planets (RP) at a query moment
Evaluate at the judgment time and place (not only natal):
1. Lagna star lord  
2. Lagna sign lord  
3. Moon star lord  
4. Moon sign lord  
5. Day lord (Vara from local sunrise: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn for Sun–Sat)  
Optional 6th: Lagna sub-lord.  
**Node rule:** if Rahu or Ketu conjoins an RP, sits in an RP’s sign, or is the star/sub of an RP, the node **replaces** that RP.

### 21.8 Four-fold significators (ABCD) for house $H$
- **A (strongest)**: planets in the **nakshatra** of an occupant of $H$.  
- **B**: planets **occupying** $H$ (KP occupancy, §21.5).  
- **C**: planets in the **nakshatra of the sign-lord** of $H$.  
- **D (weakest)**: the **sign-lord** of $H$ itself.  
Rahu/Ketu act as **agents** of the lord of the sign they occupy and of any planet they conjoin.

### 21.9 Fruitful significators (event rule)
An event of house $H$ materializes when:
1. The **CSL of $H$** is a significator (A/B/C/D) of $H$ (and of supporting houses, e.g. 2+11 for money, 2+7+11 for marriage), **and**
2. That CSL is **not** a strong significator of denying houses (12th from $H$, or 6/8/12 as relevant), **and**
3. Vimshottari **MD–AD–PD lords** are among those significators (often the natal star/sub of the CSL).

Standard house sets: marriage $2,7,11$ (deny $1,6,10$); career $2,6,10$ (or $6,10,11$ service); foreign $3,9,12$.

### 21.10 Engine surface (any native)
| Calculation | Where |
|:---|:---|
| Placidus 12 cusps + nak + star + sub + sub-sub | `Ephemeris.get_house_cusps` |
| Sub / SSL / SSSL / 249 of any $\lambda$ | `kp_sub_lord` / `kp_sub_sub_lord` / `kp_sssl_lord` / `kp_249_index` / `kp_chain` |
| Planet Sign / Star / Sub / SSL / SSSL / KP-249 | position dict + `chart.kp["planets"]` |
| Equal-bhava 12-cusp table | `chart.kp["equal_cusps"]` |
| Occupancy Placidus + equal | `chart.kp["occupancy"]` |
| Ruling planets + node join | `chart.kp_ruling_planets()` |
| ABCD significators | `chart.kp_significators(H)` |
| Fruitful-significator filter | `chart.kp_fruitful(houses, deny)` |
| SSL tables, fold matrix, CRL, star chains | `chart.kp_advanced` |

**Source:** K.S. Krishnamurti *KP Reader* 1–6; Swiss `houses_ex` Placidus.

---

## 22. Nadi Astrology Rules (Bhrigu Nandi Nadi)

### 22.1 Directional / Trinal Conjunctions (1-5-9 System)
In Nadi astrology, signs sharing the same element/direction form a **$100\%$ mutual conjunction**:
- **East (Fire / Agni)**: Aries (1), Leo (5), Sagittarius (9)
- **South (Earth / Prithvi)**: Taurus (2), Virgo (6), Capricorn (10)
- **West (Air / Vayu)**: Gemini (3), Libra (7), Aquarius (11)
- **North (Water / Jala)**: Cancer (4), Scorpio (8), Pisces (12)

$$\text{Same\_Direction}(S_1, S_2) = (S_1 \pmod 4 == S_2 \pmod 4)$$

### 22.2 Positional Relationship Weights
From any planet $P$ in sign $S_P$:
- **Same Direction (1, 5, 9 from $S_P$)**: $100\%$ direct interaction.
- **7th Sign from $S_P$ (Direct Opposition)**: $100\%$ interaction.
- **2nd Sign from $S_P$ (Front / Immediate Future)**: $75\%$ progressive influence.
- **12th Sign from $S_P$ (Rear / Past Karma Backlog)**: $50\%$ modifying influence.
- **3rd and 11th Signs from $S_P$**: $25\%$ supportive influence.

### 22.3 Retrograde Planet Dual-Position Rule
If `P.is_retrograde == True`:
- $P$ acts with $50\%$ strength from its **posited sign** $S_P$.
- $P$ acts with $50\%$ strength from the **previous sign** $(S_P - 1) \pmod{12}$.

### 22.4 Primary Planetary Karakatwas in Nadi
| Planet | Nadi Role (Karakatwa) |
|:---|:---|
| **Jupiter** | **Jeeva Karaka** (The Native / Soul / Life Force / Prana) |
| **Saturn** | **Karma Karaka** (Profession / Destiny / Duty / Obstacles) |
| **Venus** | **Kalatra & Dhana Karaka** (Wife / Luxury / Wealth / Vehicle / Money) |
| **Mars** | **Bhratri & Pati Karaka** (Brother / Husband in female chart / Technical Skill) |
| **Mercury** | **Buddhi & Vidya Karaka** (Intelligence / Business / Land / Friends) |
| **Sun** | **Pitru & Atma Karaka** (Father / Government / Status / Vitality) |
| **Moon** | **Matru & Manas Karaka** (Mother / Mind / Travel / Liquid Cash / Losses) |
| **Rahu** | **Maya & Pitamaha** (Paternal Grandfather / Foreign / Expansion / Illusion) |
| **Ketu** | **Moksha & Matamaha** (Maternal Grandfather / Renunciation / Software / Liberation) |

---

## 23. Lal Kitab Calculation Rules

### 23.1 Fixed Permanent House Karakas (Pakka Ghar Table)
In Lal Kitab, houses have invariant natural lords regardless of Lagna:

| House | Permanent Lord (Pakka Ghar) | Exalted Planet | Debilitated Planet |
|:---:|:---:|:---:|:---:|
| **1st** | Mars / Sun | Sun | Saturn |
| **2nd** | Jupiter | Moon | — |
| **3rd** | Mars | Rahu | Ketu |
| **4th** | Moon | Jupiter | Mars |
| **5th** | Jupiter | Sun | — |
| **6th** | Mercury / Ketu | Mercury / Rahu | Venus / Ketu |
| **7th** | Venus / Mercury | Saturn | Sun |
| **8th** | Saturn / Mars | — | Moon |
| **9th** | Jupiter | Ketu | Rahu |
| **10th** | Saturn | Mars | Jupiter |
| **11th** | Jupiter | — | — |
| **12th** | Jupiter / Rahu | Venus / Ketu | Mercury / Rahu |

### 23.2 Masnui Grahas (Artificial / Compound Planets)
When individual planets combine, they generate the effect of another planet:
- **Artificial Sun**: Jupiter $+$ Ketu
- **Artificial Moon**: Jupiter $+$ Venus
- **Artificial Mars (Benefic / Nek)**: Sun $+$ Mercury
- **Artificial Mars (Malefic / Bad)**: Sun $+$ Saturn
- **Artificial Mercury**: Jupiter $+$ Rahu
- **Artificial Jupiter**: Sun $+$ Moon
- **Artificial Venus**: Rahu $+$ Ketu
- **Artificial Saturn**: Venus $+$ Mars
- **Artificial Rahu**: Mars $+$ Saturn
- **Artificial Ketu**: Venus $+$ Saturn

### 23.3 Soya Hua Ghar (Dormant House) & Soya Hua Graha
- **Dormant House**: A house is asleep (`is_sleeping_house = True`) if it contains no planets AND receives no direct aspect from any planet.
- **Awakening**: Activated when a transiting planet or dasha lord occupies its Pakka Ghar or friendly house.
- **Dormant Planet**: A planet is asleep if it occupies a house that does not aspect other houses.

### 23.4 Andha Teva (Blind Horoscope) Detection
- **Condition**: Saturn in the 7th house while Sun is in the 1st house, OR 10th house occupied by mutually inimical planets without any benefic aspect.
- **Result**: The chart is classified as `ANDHA_TEVA` (impaired directional guidance).

### 23.5 Pitru Rin (9 Ancestral Debts) Detection Table
| Rin (Debt) Type | Specific Chart Trigger Condition |
|:---|:---|
| **1. Pitru Rin (Father)** | Jupiter afflicted by Venus, Mercury, or Rahu in 2nd, 5th, 9th, or 12th house |
| **2. Matru Rin (Mother)** | Moon afflicted by Ketu in 2nd, 4th, or 8th house |
| **3. Stri Rin (Wife)** | Venus afflicted by Sun, Moon, or Rahu in 2nd or 7th house |
| **4. Bhratri Rin (Brother)** | Mars afflicted by Mercury or Ketu in 1st, 3rd, or 8th house |
| **5. Svajan Rin (Self)** | Sun afflicted by Venus, Saturn, or Rahu in 1st or 5th house |
| **6. Kanya Rin (Daughter)** | Mercury afflicted by Moon in 3rd or 6th house |
| **7. Nirmamta Rin (Cruelty)** | Saturn afflicted by Sun, Moon, or Mars in 8th, 10th, or 11th house |
| **8. Rahu Rin (Unborn)** | Rahu afflicted by Sun, Venus, or Mars in 12th house |
| **9. Ketu Rin (Divine)** | Ketu afflicted by Moon or Mars in 6th house |

---

## 24. Navamsa, Pushkara Navamsa & Sensitive Points (CS Patel Standards)

### 24.1 Pushkara Navamsa (24 Auspicious Navamsa Arcs)
Each $30^\circ$ sign contains exactly 2 Pushkara Navamsa zones ($3^\circ 20'$ each), totaling 24 in the zodiac. Planets placed in Pushkara Navamsa gain extraordinary nourish-ment and benefic manifestation capacity.

| Element | Signs | Pushkara Navamsas (Index & Degree Span) | Navamsa Sign & Lord |
|:---|:---|:---|:---|
| **Fire (Agni)** | Aries, Leo, Sagittarius | **7th Navamsa** ($20^\circ 00' - 23^\circ 20'$) | Libra (Venus) |
| | | **9th Navamsa** ($26^\circ 40' - 30^\circ 00'$) | Sagittarius (Jupiter) |
| **Earth (Prithvi)** | Taurus, Virgo, Capricorn | **3rd Navamsa** ($06^\circ 40' - 10^\circ 00'$) | Pisces (Jupiter) |
| | | **5th Navamsa** ($13^\circ 20' - 16^\circ 40'$) | Taurus (Venus) |
| **Air (Vayu)** | Gemini, Libra, Aquarius | **6th Navamsa** ($16^\circ 40' - 20^\circ 00'$) | Pisces (Jupiter) |
| | | **8th Navamsa** ($23^\circ 20' - 26^\circ 40'$) | Taurus (Venus) |
| **Water (Jala)** | Cancer, Scorpio, Pisces | **1st Navamsa** ($00^\circ 00' - 03^\circ 20'$) | Cancer (Moon) |
| | | **3rd Navamsa** ($06^\circ 40' - 10^\circ 00'$) | Virgo (Mercury) |

### 24.2 Pushkara Bhaga (Exact Single Degree Points)
The exact single-degree points of maximum auspiciousness in each sign:

| Sign | Pushkara Bhaga Degree | Exact Arc |
|:---|:---:|:---:|
| **Aries** | $21^\circ$ | $20^\circ 00' - 21^\circ 00'$ |
| **Taurus** | $14^\circ$ | $13^\circ 00' - 14^\circ 00'$ |
| **Gemini** | $18^\circ$ | $17^\circ 00' - 18^\circ 00'$ |
| **Cancer** | $08^\circ$ | $07^\circ 00' - 08^\circ 00'$ |
| **Leo** | $19^\circ$ | $18^\circ 00' - 19^\circ 00'$ |
| **Virgo** | $09^\circ$ | $08^\circ 00' - 09^\circ 00'$ |
| **Libra** | $24^\circ$ | $23^\circ 00' - 24^\circ 00'$ |
| **Scorpio** | $11^\circ$ | $10^\circ 00' - 11^\circ 00'$ |
| **Sagittarius** | $23^\circ$ | $22^\circ 00' - 23^\circ 00'$ |
| **Capricorn** | $14^\circ$ | $13^\circ 00' - 14^\circ 00'$ |
| **Aquarius** | $19^\circ$ | $18^\circ 00' - 19^\circ 00'$ |
| **Pisces** | $09^\circ$ | $08^\circ 00' - 09^\circ 00'$ |

### 24.3 64th Navamsa (Kha-Chatushtaya) Calculation
- **From Moon**:
  $$\lambda_{\text{64th\_Moon}} = (\lambda_{\text{Moon}} + 210^\circ) \pmod{360^\circ}$$
  Equivalent to the 8th house in D-9 (Navamsa) counted from Moon's Navamsa position.
- **From Lagna**:
  $$\lambda_{\text{64th\_Lagna}} = (\lambda_{\text{ASC}} + 210^\circ) \pmod{360^\circ}$$
- *Sensitive Transit Rule*: Transits of Saturn, Rahu, or Mars over the 64th Navamsa degree or its trines ($+120^\circ, +240^\circ$) trigger acute bodily or psychological crises.

### 24.4 22nd Drekkana (Khara Drekkana & Kharadhipati)
- The 22nd Drekkana from Lagna corresponds to the 8th house in the D-3 (Drekkana) chart.
- Longitude span: $\lambda_{\text{22nd\_Drekkana}} = (\lambda_{\text{ASC}} + 70^\circ) \pmod{360^\circ}$.
- **Kharadhipati**: The lord of the sign occupied by the 22nd Drekkana in D-3.

### 24.5 Vargottama Condition
$$\text{is\_vargottama}(P) = (\lfloor \lambda_P / 30^\circ \rfloor == \lfloor (\lambda_P \times 9) / 30^\circ \rfloor \pmod{12})$$
- A Vargottama planet receives $+1.0$ full dignity multiplier equivalent to residence in own sign.

---

## 25. Nakshatra-Level Predictive Algorithms & Activation Ages

### 25.1 28-Nakshatra Scheme with Abhijit
- **Abhijit Nakshatra Span**: $06^\circ 40' 00'' - 10^\circ 53' 20''$ of Capricorn (last $3^\circ 20'$ of Uttara Ashadha to first $0^\circ 53' 20''$ of Shravana).
- Total Span = $04^\circ 13' 20''$.
- Used in Sarvatobhadra Chakra, special transit calculations, and divine muhurtas.

### 25.2 Nava-Tara Calculation (9 Tara System from Janma Nakshatra)
Let $N_{\text{Janma}} \in \{1 \dots 27\}$ be natal Moon's Nakshatra, and $N \in \{1 \dots 27\}$ be target Nakshatra:
$$\text{Tara Index} = ((N - N_{\text{Janma}}) \pmod 9) + 1$$

| Index | Tara Name | Classification | Scoring Weight |
|:---:|:---|:---|:---:|
| 1 | **Janma** | Body / Self | Neutral ($0.0$) |
| 2 | **Sampat** | Wealth / Assets | Highly Auspicious ($+1.0$) |
| 3 | **Vipat** | Danger / Loss / Accident | Inauspicious ($-1.0$) |
| 4 | **Kshema** | Well-being / Protection | Auspicious ($+0.8$) |
| 5 | **Pratyak** | Obstacles / Confrontation | Inauspicious ($-0.8$) |
| 6 | **Sadhana** | Achievement / Realization | Highly Auspicious ($+1.0$) |
| 7 | **Naidhana (Vadh)** | Fatality / Severe Crisis | Severely Inauspicious ($-1.0$) |
| 8 | **Mitra** | Friendly / Support | Auspicious ($+0.8$) |
| 9 | **Parama Mitra** | Supreme Ally / Highest Gain | Highly Auspicious ($+1.0$) |

### 25.3 Special Sensitive Nakshatras (Parashari 27-Scheme)
Counted from Janma Nakshatra ($N_{\text{Janma}}$):
- **Janma**: 1st Nakshatra (Physical vitality)
- **Karma**: 10th Nakshatra (Career, public actions)
- **Samudayika**: 18th Nakshatra (Community, collective fortune)
- **Vainashika (Vinasha)**: 23rd Nakshatra (Destruction, vulnerability)
- **Manasa**: 25th Nakshatra (Mental health, inner peace)
- **Kula**: 24th Nakshatra (Family lineage, ancestry)
- **Jati**: 26th Nakshatra (Social group, community standing)
- **Desha**: 27th Nakshatra (Homeland, geographical security)
- **Abhisheka**: 28th (in 28-nakshatra scheme) / 27th (Coronation, ultimate authority)

### 25.4 Nakshatra Activation Ages (Classical & Lunar Astro System)
| # | Nakshatra | Primary Activation Age | Secondary Activation Age |
|:---:|:---|:---:|:---:|
| 1 | Ashwini | 20 | 28 |
| 2 | Bharani | 24 | 33 |
| 3 | Krittika | 21 | 30 |
| 4 | Rohini | 24 | 32 |
| 5 | Mrigashira | 28 | 35 |
| 6 | Ardra | 25 | 34 |
| 7 | Punarvasu | 24 | 32 |
| 8 | Pushya | 28 | 36 |
| 9 | Ashlesha | 30 | 39 |
| 10 | Magha | 25 | 34 |
| 11 | Purva Phalguni | 28 | 38 |
| 12 | Uttara Phalguni | 30 | 36 |
| 13 | Hasta | 25 | 35 |
| 14 | Chitra | 32 | 38 |
| 15 | Swati | 30 | 37 |
| 16 | Vishakha | 28 | 34 |
| 17 | Anuradha | 32 | 39 |
| 18 | Jyeshtha | 27 | 36 |
| 19 | Mula | 28 | 36 |
| 20 | Purva Ashadha | 28 | 35 |
| 21 | Uttara Ashadha | 31 | 38 |
| 22 | Shravana | 25 | 33 |
| 23 | Dhanishta | 24 | 32 |
| 24 | Shatabhisha | 28 | 36 |
| 25 | Purva Bhadrapada | 24 | 33 |
| 26 | Uttara Bhadrapada | 27 | 35 |
| 27 | Revati | 23 | 32 |

---

## 26. Rahu-Ketu Axis & Eclipse Calculation Rules

### 26.1 Calculation Modes
- **Mean Node (`swe.calc_ut(..., SE_MEAN_NODE)`)**: Constant retrograde rate ($\approx 19.34^\circ / \text{year} \approx -0.053^\circ/\text{day}$). Engine default. Ketu uses the **same** $\mathrm{d}\lambda/\mathrm{d}t$ (§1.3).
- **True Node (`swe.calc_ut(..., SE_TRUE_NODE)`)**: Instantaneous orbital-plane intersection (can station/direct). Optional; not the natal default.
- Sidereal frame: engine `"lahiri"` = **True Chitrapaksha** (`SIDM_TRUE_CITRA`) + mean node. Official IAU Lahiri is `ayanamsha="lahiri_official"`.

### 26.2 Complete 12 Kala Sarpa Yoga Types
Activated when all 7 classical planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) are positioned entirely on one side of the nodal axis ($180^\circ$ arc).

| Type # | Kala Sarpa Yoga Name | Rahu House | Ketu House | Signification Domain |
|:---:|:---|:---:|:---:|:---|
| 1 | **Ananta** | 1st House | 7th House | Self vs Relationship struggle |
| 2 | **Kulika** | 2nd House | 8th House | Family wealth & Health crisis |
| 3 | **Vasuki** | 3rd House | 9th House | Courage, Siblings & Luck |
| 4 | **Shankhapala** | 4th House | 10th House | Domestic peace vs Career pressure |
| 5 | **Padma** | 5th House | 11th House | Children, Intellect & Speculation |
| 6 | **Mahapadma** | 6th House | 12th House | Litigation, Health & Foreign stays |
| 7 | **Takshaka** | 7th House | 1st House | Partnership conflicts & Health |
| 8 | **Karkotaka** | 8th House | 2nd House | Sudden transformations & Inheritance |
| 9 | **Shankhachuda** | 9th House | 3rd House | Father, Religion & Destiny |
| 10 | **Ghataka** | 10th House | 4th House | Professional instability & Fame |
| 11 | **Vishadhara** | 11th House | 5th House | Elder siblings & Network gains |
| 12 | **Sheshanaga** | 12th House | 6th House | Secret enemies, Isolation & Expenses |

### 26.3 Kala Sarpa vs Kala Amrita Distinction
- **Kala Sarpa Yoga**: All 7 planets move in direct motion towards **Rahu** (Materialistic ambition, worldly struggles).
- **Kala Amrita Yoga**: All 7 planets move in direct motion towards **Ketu** (Spiritual liberation, detachment, inner knowledge).

### 26.4 Grahan (Eclipse) Yoga Detection Algorithm
$$\text{is\_grahan\_sun} = (|\lambda_{\text{Sun}} - \lambda_{\text{Rahu}}| \le 12^\circ) \lor (|\lambda_{\text{Sun}} - \lambda_{\text{Ketu}}| \le 12^\circ)$$
$$\text{is\_grahan\_moon} = (|\lambda_{\text{Moon}} - \lambda_{\text{Rahu}}| \le 12^\circ) \lor (|\lambda_{\text{Moon}} - \lambda_{\text{Ketu}}| \le 12^\circ)$$
- Eclipsed Sun/Moon loses Paksha/Dig Bala strength and causes functional affliction to its lorded houses.

### 26.5 Nodal Aspects (engine)
Parashari house aspects used by the engine match §2.5: Rahu and Ketu aspect the **5th and 9th** (same as Jupiter), plus the universal 7th. A South-Indian school adds a 12th aspect at 50%; that variant is **not** used. Yoga detection and `SPECIAL_ASPECTS` therefore list `[5, 9]` only.

---

## 27. Sudarshana Chakra Dasha — Triple-Lagna Progression

Sudarshana Chakra overlays three concurrent house progressions — one from Lagna, one from Sun, one from Moon — each advancing one house per year of life. An event predicted by a house $H$ is confirmed when the same house is activated from **all three** references simultaneously.

### 27.1 Year Assignment
For completed age $A$ (years after birth, 0-indexed):
$$\text{Active House from Lagna} = (A \pmod{12}) + 1$$
$$\text{Active House from Sun} = (A \pmod{12}) + 1 \quad \text{(counted from Sun's sign as house 1)}$$
$$\text{Active House from Moon} = (A \pmod{12}) + 1 \quad \text{(counted from Moon's sign as house 1)}$$

### 27.2 Triple-Layer Overlay Algorithm
```
for age in range(0, 120):
    lagna_house = (age % 12) + 1
    sun_sign_idx = floor(natal_sun_long / 30)
    sun_house_sign = (sun_sign_idx + (age % 12)) % 12
    moon_sign_idx = floor(natal_moon_long / 30)
    moon_house_sign = (moon_sign_idx + (age % 12)) % 12
    
    # Planets in activated sign from each reference
    lagna_planets = planets_in_sign(lagna_activated_sign)
    sun_planets = planets_in_sign(sun_house_sign)
    moon_planets = planets_in_sign(moon_house_sign)
    
    # Cross-reference: planet appearing in 2+ layers = strong year
    overlap = lagna_planets ∩ sun_planets ∩ moon_planets
```

### 27.3 Event Confirmation Rule
An event activates at age $A$ when:
1. The relevant house ($H$) is activated from Lagna at age $A$, **AND**
2. The same house (or its lord's sign) is activated from Sun or Moon at the same age, **AND**
3. The Vimshottari Dasha lord at age $A$ is a significator of house $H$.

**Source:** BPHS Ch. 65, BV Raman (*Hindu Predictive Astrology*)

---

## 28. Sarvatobhadra Chakra (SBC) — Transit Grid Engine

The SBC is a **45-cell symmetric grid** used for transit-based prediction. It maps nakshatras, vowels, weekdays, and tithis to a fixed $9 \times 9$ grid pattern. Transit vedha through the SBC determines favorable/unfavorable days.

### 28.1 Grid Layout (Fixed 45-Cell Pattern)
The $9 \times 9$ outer frame contains **28 Nakshatras** (including Abhijit), **7 Weekdays**, **16 Vowels**, and **14 Tithis** in fixed positions. The inner cells are empty. Layout:

| Row | Col 1 | Col 2 | Col 3 | Col 4 | Col 5 | Col 6 | Col 7 | Col 8 | Col 9 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Krittika | T3 | Wed | T4 | Rohini | T5 | Thu | T6 | Mrigashira |
| 2 | V-E | — | — | — | — | — | — | — | V-AI |
| 3 | Tue | — | — | — | — | — | — | — | Fri |
| 4 | T2 | — | — | — | — | — | — | — | T7 |
| 5 | Bharani | — | — | — | — | — | — | — | Ardra |
| 6 | T1 | — | — | — | — | — | — | — | T8 |
| 7 | Mon | — | — | — | — | — | — | — | Sat |
| 8 | V-AA | — | — | — | — | — | — | — | V-O |
| 9 | Ashwini | T14 | Sun | T13 | Revati | T12 | — | T11 | Shatabhisha |

*(Remaining nakshatras fill the sides in order: Punarvasu through Dhanishta clockwise)*

### 28.2 Vedha (Obstruction) Detection Rule
A transiting planet at nakshatra $N_T$ casts vedha (obstruction) on all cells that share a **diagonal line** through the SBC grid with $N_T$'s cell:
$$\text{vedha}(N_T) = \{\text{cells on the same diagonal as } N_T\text{'s cell in SBC}\}$$

### 28.3 Favorable / Unfavorable Day Computation
For a given date:
1. Find transiting Moon's nakshatra $\rightarrow$ locate in SBC.
2. Find the weekday $\rightarrow$ locate in SBC.
3. Find the tithi $\rightarrow$ locate in SBC.
4. Check if any natural malefic (transiting Mars, Saturn, Rahu) casts diagonal vedha on Moon's nakshatra cell, the weekday cell, or the birth nakshatra cell.
5. **If vedha from malefic on Janma Nakshatra**: Inauspicious day. **If vedha from benefic**: Auspicious day.

**Source:** BV Raman, Prasna Marga Ch. 15, BPHS

---

## 29. Career & Profession Determination — Computation Algorithm

Pure data extraction for career analysis. No interpretation — raw factor collection.

### 29.1 Primary Career Significators (Data Collection)
Collect the following raw data points:
```
career_data = {
    "10L":         lord(10),           # 10th lord planet
    "10L_sign":    sign_of(lord(10)),   # 10th lord's sign
    "10L_house":   house_of(lord(10)),  # 10th lord's house placement
    "10L_nak":     nakshatra_of(lord(10)),
    "10L_dignity": dignity(lord(10)),
    "10H_planets": planets_in_house(10),  # Planets in 10th house
    "10H_aspects": aspects_on_house(10),  # Planets aspecting 10th
    "D10_lagna":   D10_lagna_sign,
    "D10_10L":     lord_of_10th_in_D10,
    "D10_planets_10": planets_in_10th_D10,
    "AmK":         amatyakaraka_planet,  # Jaimini career karaka
    "AmK_sign":    sign_of(AmK),
    "AmK_house":   house_of(AmK),
    "saturn_house": house_of(Saturn),
    "saturn_sign":  sign_of(Saturn),
    "sun_house":    house_of(Sun),
    "MC_longitude": 10th_cusp_placidus,
    "MC_nak":       nakshatra_of(MC),
    "MC_sublord":   kp_sublord(MC),
}
```

### 29.2 Planet-Profession Mapping (Raw Lookup Table)
| Planet | Profession Domain (Karaka) |
|:---|:---|
| **Sun** | Government, authority, leadership, medicine, politics |
| **Moon** | Nursing, hospitality, liquids, dairy, travel, public dealing |
| **Mars** | Engineering, military, surgery, real estate, sports, fire |
| **Mercury** | Commerce, writing, accounting, IT, communication, astrology |
| **Jupiter** | Teaching, law, banking, advisory, priesthood, philosophy |
| **Venus** | Arts, entertainment, luxury goods, fashion, beauty, vehicles |
| **Saturn** | Mining, labor, agriculture, oil, iron, construction, judiciary |
| **Rahu** | Foreign trade, technology, aviation, diplomacy, unconventional |
| **Ketu** | Occult, software, spirituality, research, detailing, healing |

### 29.3 House-Profession Axis (Raw Data)
| 10L House | Career Direction Flag |
|:---:|:---|
| 1 | Self-employed, independent practice |
| 2 | Family business, finance, banking, speech-related |
| 3 | Communication, media, writing, sales, short travel |
| 4 | Real estate, farming, vehicles, homeland-based |
| 5 | Speculation, entertainment, education, advisory |
| 6 | Service, medical, legal, competition, debt recovery |
| 7 | Partnership, consultancy, foreign trade, spouse-related |
| 8 | Insurance, occult, research, inheritance, mining |
| 9 | Teaching, law, publishing, father's business, export |
| 10 | Government, own authority, peak career position |
| 11 | Large organizations, networking, gains-oriented |
| 12 | Foreign land, hospitals, ashrams, import, expenditure |

### 29.4 Government Job Detection Conditions
```
gov_indicators = [
    Sun in kendra or trikona,
    Sun aspects or conjoins 10L,
    10L connected to 1L or 9L,
    Saturn in 10H or aspects 10H (service / authority),
    D10 lagna = Leo or Capricorn or Aries,
    AmK = Sun or Jupiter,
]
gov_score = sum(1 for cond in gov_indicators if cond)
# gov_score >= 3: strong government career indication
```

**Source:** RG Rao (*Profession from Position of Planets*), KK Pathak (*Classical Predictive Techniques*), BPHS

---

## 30. Wealth & Dhana Determination — Computation Algorithm

Raw factor collection for wealth assessment. No interpretation.

### 30.1 Wealth Significator Data Collection
```
wealth_data = {
    "2L":         lord(2),
    "2L_house":   house_of(lord(2)),
    "2L_dignity": dignity(lord(2)),
    "11L":        lord(11),
    "11L_house":  house_of(lord(11)),
    "11L_dignity": dignity(lord(11)),
    "5L":         lord(5),
    "9L":         lord(9),
    "2H_planets": planets_in_house(2),
    "11H_planets": planets_in_house(11),
    "jupiter_house": house_of(Jupiter),
    "venus_house":   house_of(Venus),
    "indu_lagna":    indu_lagna_sign,   # §8.6
    "indu_lord":     lord_of_indu,
    "sree_lagna":    sree_lagna_sign,
    "2H_SAV":        SAV[house_2_sign],
    "11H_SAV":       SAV[house_11_sign],
    "dhana_yogas":   detected_dhana_yogas,  # from §9.3
}
```

### 30.2 Dhana Yoga Strength Scoring
$$\text{Dhana Score} = \sum_{\text{each Dhana Yoga present}} w_i$$
where:
| Yoga | Weight $w_i$ |
|:---|:---:|
| 2L-11L conjunction/mutual aspect | 3 |
| 5L-9L conjunction/mutual aspect | 3 |
| 1L-2L conjunction/mutual aspect | 2 |
| Lakshmi Yoga (§9.7D) | 4 |
| Jupiter in 2H or 11H or 5H or 9H | 2 |
| Venus in 2H or 4H or 7H | 1 |
| 11L in own sign or exalted | 2 |
| 2L in own sign or exalted | 2 |
| Indu Lagna lord in Kendra/Trikona | 2 |
| SAV of 11H ≥ 30 | 1 |

### 30.3 Wealth Timing (Data Extraction)
Wealth manifests during Dasha/AD of:
```
wealth_triggers = [lord(2), lord(11), lord(5), lord(9),
                   lord(1), "Jupiter", "Venus",
                   lord_of_indu_lagna]
# Cross-check with Double Transit (§10.1) on houses 2, 11
```

### 30.4 Ashtakavarga Wealth Indicators (Raw Flags)
```
av_wealth_flags = {
    "11H_gt_10H": SAV[11H_sign] > SAV[10H_sign],  # KN Rao rule
    "11H_gt_12H": SAV[11H_sign] > SAV[12H_sign],  # income > expense
    "2H_gt_avg":  SAV[2H_sign] > (337 / 12),       # above average
    "jupiter_BAV_11H": Jupiter_BAV[11H_sign],       # Jupiter bindu in 11H
}
```

**Source:** SS Chatterjee (*Fortune & Finance*), CS Patel (*Ashtakavarga*), BPHS, BV Raman (*300 Important Combinations*)

---

## 31. Medical Astrology — Planet-Disease Mapping & Health Trigger Rules

Raw data mapping for health analysis. Output = flags and data, no diagnosis.

### 31.1 Planet-Body System Mapping
| Planet | Body System / Organ | Dosha (Ayurveda) |
|:---|:---|:---:|
| **Sun** | Heart, eyes, bones, spine, stomach, right eye (M) / left eye (F) | Pitta |
| **Moon** | Mind, blood, lymph, breast, uterus, left eye (M) / right eye (F) | Kapha/Vata |
| **Mars** | Blood, muscles, marrow, head, genitals, accidents, surgeries | Pitta |
| **Mercury** | Nervous system, lungs, skin, speech, intestines, thyroid | Tridosha |
| **Jupiter** | Liver, fat, thighs, ears, diabetes, tumors | Kapha |
| **Venus** | Kidneys, reproductive system, face, throat, diabetes (co-) | Kapha/Vata |
| **Saturn** | Bones, joints, teeth, chronic diseases, paralysis, depression | Vata |
| **Rahu** | Poisons, mysterious diseases, phobias, epidemics, cancer | Vata |
| **Ketu** | Viruses, surgeries, skin, wounds, spiritual healing, epidemics | Pitta |

### 31.2 Sign-Body Part Mapping (Kalapurusha)
| Sign | Body Part | Disease Domain |
|:---:|:---|:---|
| Aries | Head, brain, face | Headaches, fevers, head injuries |
| Taurus | Throat, neck, thyroid | Throat infections, thyroid, tonsils |
| Gemini | Shoulders, arms, lungs | Asthma, bronchitis, arm fractures |
| Cancer | Chest, breast, stomach | Stomach ulcers, breast issues, fluid retention |
| Leo | Heart, spine, back | Heart disease, spinal disorders |
| Virgo | Intestines, nervous system | Digestive disorders, anxiety |
| Libra | Kidneys, lower back, skin | Kidney stones, skin diseases |
| Scorpio | Reproductive, excretory | STDs, piles, hernia |
| Sagittarius | Thighs, hips, liver | Liver disease, sciatica, hip injuries |
| Capricorn | Knees, bones, joints | Arthritis, fractures, joint pain |
| Aquarius | Calves, ankles, circulation | Varicose veins, circulatory issues |
| Pisces | Feet, lymph, immunity | Foot injuries, lymphatic disorders, allergies |

### 31.3 Health Trigger Detection (Raw Flags)
```
health_flags = {
    "6L_in_dusthana":   house_of(lord(6)) in {6, 8, 12},
    "6L_in_lagna":      house_of(lord(6)) == 1,
    "8L_in_lagna":      house_of(lord(8)) == 1,
    "lagna_afflicted":  malefic_aspects_on(1) >= 2,
    "moon_afflicted":   malefic_conjunct_or_aspect(Moon) >= 2,
    "sun_weak":         shadbala(Sun) < 390,  # below minimum
    "saturn_on_lagna":  house_of(Saturn) == 1,
    "mars_in_6_or_8":   house_of(Mars) in {6, 8},
    "rahu_in_6":        house_of(Rahu) == 6,
}
```

### 31.4 Dosha (Ayurvedic Constitution) from Chart
$$\text{Vata Score} = \text{count}(\text{Saturn, Rahu in Kendra/Trikona}) + \text{Moon in Vata Nadi nakshatra}$$
$$\text{Pitta Score} = \text{count}(\text{Sun, Mars, Ketu in Kendra/Trikona}) + \text{Moon in Pitta Nadi nakshatra}$$
$$\text{Kapha Score} = \text{count}(\text{Moon, Jupiter, Venus in Kendra/Trikona}) + \text{Moon in Kapha Nadi nakshatra}$$
Dominant dosha = $\arg\max(\text{Vata, Pitta, Kapha scores})$.

**Source:** KS Charak (*Essentials of Medical Astrology*, *Subtleties of Medical Astrology*), BPHS

---

## 32. Muhurtha Essentials — Electional Computation Rules

Minimum computation checks for electional astrology. Raw pass/fail flags.

### 32.1 Panchanga Shuddhi (5-Limb Purity Check)
For a proposed muhurtha datetime and location:
```
panchanga_check = {
    "tithi_ok":     tithi not in {4, 9, 14, 30, 8_krishna},  # Rikta tithis inauspicious
    "nakshatra_ok": nakshatra not in {Bharani, Krittika_1pada, Ashlesha,
                                       Jyeshtha, Moola_1pada, Revati_4pada},
    "yoga_ok":      yoga not in {Vyatipata(17), Vaidhriti(27),
                                  Vishkambha(1), Atiganda(6), Shoola(9),
                                  Gandha(10), Vajra(15), Vyaghata(13), Parigha(19)},
    "karana_ok":    karana != Vishti,  # Bhadra karana inauspicious
    "vara_ok":      True,  # weekday-specific rules per event type
}
panchanga_shuddhi = all(panchanga_check.values())
```

### 32.2 Chandrabala (Lunar Strength)
Moon's transit position relative to natal Moon at the muhurtha time:
$$\text{Chandrabala House} = ((\text{transit Moon sign} - \text{natal Moon sign}) \pmod{12}) + 1$$
- **Favorable**: Houses $1, 3, 6, 7, 10, 11$ from natal Moon.
- **Unfavorable**: Houses $2, 5, 8, 9, 12$ from natal Moon.
- **Exception**: $4^\text{th}$ house OK for fixed events (property, construction).

### 32.3 Tarabala (Star Strength)
$$\text{Tara Index} = ((\text{transit Moon nakshatra} - \text{Janma Nakshatra}) \pmod{9}) + 1$$
- **Inauspicious Taras**: $3$ (Vipat), $5$ (Pratyak), $7$ (Naidhana/Vadh) → avoid.
- Same Nava-Tara table as §25.2.

### 32.4 Lagna Shuddhi (Ascendant Purity)
For the muhurtha ascendant:
```
lagna_check = {
    "lagna_not_8th_from_natal":  muhurtha_lagna_sign != sign_8th_from_natal_lagna,
    "lagna_lord_not_combust":    not is_combust(lord_of_muhurtha_lagna),
    "lagna_not_afflicted":       no_malefic_in_muhurtha_lagna_without_benefic_aspect,
    "7th_from_lagna_not_malefic": no_malefic_in_7th_without_benefic_aspect,
}
```

### 32.5 Event-Specific Muhurtha Weekday Rules
| Event | Favorable Weekday(s) | Avoid |
|:---|:---|:---|
| Marriage | Mon, Wed, Thu, Fri | Tue, Sat, Sun |
| Business start | Wed, Thu, Fri | Tue, Sat |
| Travel | Mon, Wed, Fri | Tue, Sun |
| Surgery | Tue, Sat | Mon, Fri |
| Property | Thu, Fri | Tue |
| Education | Wed, Thu | Tue, Sat |

**Source:** BV Raman (*Muhurtha or Electional Astrology*), Prasna Marga

---

## 33. Gandanta, Nakshatra Sandhi & Abhukta Moola — Computation Rules

Precise degree ranges for the three types of junction sensitivity.

### 33.1 Gandanta Zones (Fire-Water Sign Junctions)
Gandanta = last $3^\circ 20'$ of a water sign merging into first $3^\circ 20'$ of a fire sign. There are exactly **3 Gandanta zones** in the zodiac:

| # | Water Sign End | Fire Sign Start | Degree Range | Nakshatra Boundary |
|:---:|:---|:---|:---|:---|
| 1 | Pisces $26^\circ 40' - 30^\circ 00'$ | Aries $0^\circ 00' - 3^\circ 20'$ | $356^\circ 40' - 3^\circ 20'$ | Revati (Pada 4) → Ashwini (Pada 1) |
| 2 | Cancer $26^\circ 40' - 30^\circ 00'$ | Leo $0^\circ 00' - 3^\circ 20'$ | $116^\circ 40' - 123^\circ 20'$ | Ashlesha (Pada 4) → Magha (Pada 1) |
| 3 | Scorpio $26^\circ 40' - 30^\circ 00'$ | Sagittarius $0^\circ 00' - 3^\circ 20'$ | $236^\circ 40' - 243^\circ 20'$ | Jyeshtha (Pada 4) → Moola (Pada 1) |

### 33.2 Gandanta Detection Algorithm
```
def is_gandanta(longitude):
    lam = longitude % 360.0
    deg_in_sign = lam % 30.0
    sign_idx = int(lam / 30.0)
    sign_element = SIGN_ELEMENT[SIGNS[sign_idx]]
    next_sign_element = SIGN_ELEMENT[SIGNS[(sign_idx + 1) % 12]]
    prev_sign_element = SIGN_ELEMENT[SIGNS[(sign_idx - 1) % 12]]
    
    # Last 3°20' of water sign
    if sign_element == "Water" and deg_in_sign >= 26.6667:
        return True, "END_OF_WATER", 30.0 - deg_in_sign  # proximity
    # First 3°20' of fire sign
    if sign_element == "Fire" and deg_in_sign <= 3.3333 and prev_sign_element == "Water":
        return True, "START_OF_FIRE", deg_in_sign
    return False, None, None
```

### 33.3 Gandanta Severity Gradation
| Proximity to Junction | Severity |
|:---|:---|
| $0^\circ 00' - 0^\circ 48'$ (first/last $0°48'$) | **SEVERE** — Abhukta Moola |
| $0^\circ 48' - 1^\circ 36'$ | **HIGH** |
| $1^\circ 36' - 3^\circ 20'$ | **MODERATE** |

### 33.4 Abhukta Moola Nakshatras
Nakshatras at the **exact** gandanta junction point whose first pada is considered most dangerous for birth:

| Nakshatra | Gandanta Zone | Abhukta Pada | Specific Risk |
|:---|:---|:---:|:---|
| **Ashwini** (Pada 1) | Pisces → Aries | $0^\circ 00' - 0^\circ 48'$ Aries | Risk to father |
| **Magha** (Pada 1) | Cancer → Leo | $0^\circ 00' - 0^\circ 48'$ Leo | Risk to mother |
| **Moola** (Pada 1) | Scorpio → Sagittarius | $0^\circ 00' - 0^\circ 48'$ Sagittarius | Risk to father / family |
| **Ashlesha** (Pada 4) | Cancer end | $29^\circ 12' - 30^\circ 00'$ Cancer | Risk to mother-in-law |
| **Jyeshtha** (Pada 4) | Scorpio end | $29^\circ 12' - 30^\circ 00'$ Scorpio | Risk to elder brother |
| **Revati** (Pada 4) | Pisces end | $29^\circ 12' - 30^\circ 00'$ Pisces | General risk |

### 33.5 Nakshatra Sandhi (General Nakshatra Junction)
Any planet at the boundary between two nakshatras (within $0^\circ 30'$ on either side) is in **Nakshatra Sandhi**:
$$\text{is\_nak\_sandhi}(\lambda) = (\lambda \pmod{13^\circ 20'}) \le 0^\circ 30' \quad \text{OR} \quad (\lambda \pmod{13^\circ 20'}) \ge 12^\circ 50'$$

### 33.6 Rashi Sandhi (Sign Junction)
A planet at the boundary between two signs:
$$\text{is\_rashi\_sandhi}(\lambda) = (\lambda \pmod{30^\circ}) \le 1^\circ 00' \quad \text{OR} \quad (\lambda \pmod{30^\circ}) \ge 29^\circ 00'$$
Planets in Rashi Sandhi lose positional strength and cannot deliver full results of either sign. This affects Pancha Mahapurusha Yoga detection (§9.1) and dignity assignment.

**Source:** Sanjay Rath (*Brhat Nakshatra*), BPHS Ch. 93, Prasna Marga
