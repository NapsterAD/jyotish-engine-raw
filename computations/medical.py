"""
medical.py — Medical Astrology & Ayurvedic Constitution Engine (rules.md §31).
Algorithmic data mapping for physiological and constitutional assessment:
- Planet-Organ & Bodily System Vulnerability Mapping
- Sign-Kalapurusha Anatomical Affliction Tracing
- Health Trigger Detection (6L/8L/12L placements, Lagna/Moon afflictions)
- Ayurvedic Tridosha Balance Scoring (Vata, Pitta, Kapha)
"""

from typing import Dict, Any, List
from ..core.constants import SIGNS, SIGN_INDEX, NAKSHATRAS, PLANETS_7, PLANETS_9
from ..core.mapping import house_to_sign

PLANET_SYSTEM_MAP = {
    "Sun": {"organs": ["Heart", "Bones", "Spine", "Eyesight", "Stomach"], "dosha": "Pitta", "disease": "Cardiac strain, bone density, eye tension, vitality crises"},
    "Moon": {"organs": ["Mind/Psychology", "Blood Plasma", "Lymph", "Stomach Lining", "Fluid balance"], "dosha": "Kapha/Vata", "disease": "Anxiety, mood fluctuations, lymphatic congestion, insomnia"},
    "Mars": {"organs": ["Muscles", "Bone Marrow", "Blood Red Cells", "Head", "Genitals"], "dosha": "Pitta", "disease": "Inflammation, muscular tears, surgeries, blood pressure spikes, burns"},
    "Mercury": {"organs": ["Nervous System", "Lungs/Bronchi", "Skin/Epidermis", "Speech/Vocal cords", "Thyroid"], "dosha": "Tridosha", "disease": "Nervous exhaustion, allergies, respiratory hypersensitivity, skin flareups"},
    "Jupiter": {"organs": ["Liver", "Pancreas/Insulin", "Adipose/Fat", "Ears", "Arteries"], "dosha": "Kapha", "disease": "Metabolic imbalances, lipid/glucose surges, liver congestion, ear issues"},
    "Venus": {"organs": ["Kidneys", "Renal System", "Reproductive Organs", "Skin Tone", "Throat"], "dosha": "Kapha/Vata", "disease": "Renal filtration strain, hormonal shifts, urinary tract sensitivity, throat fatigue"},
    "Saturn": {"organs": ["Skeletal Joints", "Teeth", "Legs/Knees", "Chronic Systems", "Neuromuscular"], "dosha": "Vata", "disease": "Joint stiffness, chronic fatigue, circulation sluggishness, dental strain"},
    "Rahu": {"organs": ["Immune/Autoimmune", "Central Nervous System", "Poisons/Toxins", "Unidentified"], "dosha": "Vata", "disease": "Hypersensitivities, sudden infections, phantom pain, toxicity sensitivity"},
    "Ketu": {"organs": ["Skin Wounds", "Microbiome", "Occult/Spine", "Surgeries"], "dosha": "Pitta", "disease": "Sudden fevers, viral encounters, diagnostic ambiguity, localized lesions"},
}

SIGN_ANATOMY_MAP = {
    "Aries": "Head, Brain, Cranium, Facial Structure",
    "Taurus": "Throat, Vocal Cords, Neck, Thyroid, Tonsils",
    "Gemini": "Lungs, Bronchi, Shoulders, Arms, Nervous Reflexes",
    "Cancer": "Chest, Breast, Gastric Cavity, Rib Cage, Stomach",
    "Leo": "Heart, Upper Spine, Cardiac Muscle, Vital Heat",
    "Virgo": "Intestines, Abdominal Nerves, Digestive Enzymes, Spleen",
    "Libra": "Kidneys, Lumbar Region, Skin, Osmotic Equilibrium",
    "Scorpio": "Reproductive Organs, Pelvic Cavity, Excretory System",
    "Sagittarius": "Thighs, Hips, Femur, Sciatic Nerve, Liver Reserve",
    "Capricorn": "Knees, Skeletal Bones, Patella, Structural Joints",
    "Aquarius": "Calves, Ankles, Blood Circulation, Shin Bones",
    "Pisces": "Feet, Toes, Lymphatic Vessels, Immune Plasma",
}


def calc_medical_profile(chart) -> Dict[str, Any]:
    """Compute Ayurvedic Dosha Constitution and Health Vulnerability Indicators."""
    positions = chart.positions or {}
    rashi = chart.rashi_chart or {}
    lordships = getattr(chart, "lordships", {}) or {}
    shadbala = getattr(chart, "shadbala", {}) or {}
    aspects = getattr(chart, "aspects", {}) or {}
    
    l6 = lordships.get(6)
    l8 = lordships.get(8)
    l12 = lordships.get(12)
    
    h_l6 = rashi.get(l6, {}).get("house_rashi", 6)
    h_l8 = rashi.get(l8, {}).get("house_rashi", 8)
    h_l12 = rashi.get(l12, {}).get("house_rashi", 12)
    
    # Check malefic aspects on house 1 (Lagna)
    malefics = ["Saturn", "Mars", "Sun", "Rahu", "Ketu"]
    malefic_aspects_on_lagna = [m for m in malefics if 1 in aspects.get(m, []) or rashi.get(m, {}).get("house_rashi") == 1]
    
    # Check afflictions to Moon
    moon_house = rashi.get("Moon", {}).get("house_rashi", 1)
    malefics_on_moon = [m for m in malefics if (rashi.get(m, {}).get("house_rashi") == moon_house) or (moon_house in aspects.get(m, []))]
    
    # Sun Shadbala check
    sun_rupas = shadbala.get("Sun", {}).get("rupas", 6.5)
    sun_sub_minimum = sun_rupas < 6.5
    
    # Health trigger detection (rules.md §31.3)
    health_flags = {
        "6L_in_dusthana": h_l6 in (6, 8, 12),
        "6L_in_lagna": h_l6 == 1,
        "8L_in_lagna": h_l8 == 1,
        "lagna_afflicted": len(malefic_aspects_on_lagna) >= 2,
        "moon_afflicted": len(malefics_on_moon) >= 2,
        "sun_weak": sun_sub_minimum,
        "saturn_on_lagna": rashi.get("Saturn", {}).get("house_rashi") == 1,
        "mars_in_6_or_8": rashi.get("Mars", {}).get("house_rashi") in (6, 8),
        "rahu_in_6": rashi.get("Rahu", {}).get("house_rashi") == 6,
    }
    
    # Ayurvedic Tridosha Scoring (rules.md §31.4)
    # Kendra & Trikona houses: 1, 4, 7, 10, 5, 9
    kendra_trikona = (1, 4, 7, 10, 5, 9)
    
    def in_kt(planet):
        return rashi.get(planet, {}).get("house_rashi") in kendra_trikona
        
    moon_pos = positions.get("Moon", {})
    moon_nak_name = moon_pos.get("nakshatra", "Purva Ashadha")
    # Nakshatra Nadi lookup from NAKSHATRAS
    moon_nadi = "Madhya"
    for n in NAKSHATRAS:
        if n["name"] == moon_nak_name:
            moon_nadi = n.get("nadi", "Madhya")
            break
            
    # Vata: Saturn, Rahu in KT + Moon in Aadi (Vata) Nadi
    vata_score = sum(1 for p in ("Saturn", "Rahu") if in_kt(p)) + (1 if "Aadi" in moon_nadi or "Vata" in moon_nadi else 0)
    # Pitta: Sun, Mars, Ketu in KT + Moon in Madhya (Pitta) Nadi
    pitta_score = sum(1 for p in ("Sun", "Mars", "Ketu") if in_kt(p)) + (1 if "Madhya" in moon_nadi or "Pitta" in moon_nadi else 0)
    # Kapha: Moon, Jupiter, Venus in KT + Moon in Antya (Kapha) Nadi
    kapha_score = sum(1 for p in ("Moon", "Jupiter", "Venus") if in_kt(p)) + (1 if "Antya" in moon_nadi or "Kapha" in moon_nadi else 0)
    
    total_dosha = max(vata_score + pitta_score + kapha_score, 1)
    
    scores = {"Vata": vata_score, "Pitta": pitta_score, "Kapha": kapha_score}
    dominant_dosha = max(scores, key=scores.get)
    
    # Anatomical areas of focus based on occupied / lorded dusthana houses
    vulnerable_signs = [house_to_sign(h, chart.lagna_index) for h in (6, 8, 12)]
    vulnerable_anatomy = {s: SIGN_ANATOMY_MAP.get(s, "") for s in vulnerable_signs}
    
    return {
        "dominant_dosha": dominant_dosha,
        "dosha_breakdown": {
            "Vata": {"score": vata_score, "pct": round(vata_score / total_dosha * 100, 1)},
            "Pitta": {"score": pitta_score, "pct": round(pitta_score / total_dosha * 100, 1)},
            "Kapha": {"score": kapha_score, "pct": round(kapha_score / total_dosha * 100, 1)},
        },
        "health_trigger_flags": health_flags,
        "dusthana_lords": {
            "6L": {"planet": l6, "house": h_l6},
            "8L": {"planet": l8, "house": h_l8},
            "12L": {"planet": l12, "house": h_l12},
        },
        "vulnerable_anatomical_zones": vulnerable_anatomy,
        "planet_systems": PLANET_SYSTEM_MAP
    }
