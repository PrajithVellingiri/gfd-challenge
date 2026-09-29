#!/usr/bin/env python3
"""
Health Indicators Pipeline (NFHS-5 District Factsheets)
Normalizes district-level public health, maternal/child nutrition, and sanitation indicators.
Outputs to data/processed/health_indicators_normalized.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from district_normalizer import district_normalizer

RAW_DIR = Path(__file__).parent.parent / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"

# Sourced from National Family Health Survey (NFHS-5) 2019-2021 District Factsheets
# (International Institute for Population Sciences / MoHFW, Government of India)
NFHS_5_INDICATORS_RAW = [
    # Karnataka
    {"district": "Bengaluru Urban", "state": "Karnataka", "vaccination": 86.8, "inst_births": 99.4, "stunting": 24.1, "anemia_women": 45.2, "sanitation": 96.5, "water": 98.2, "insurance": 28.5},
    {"district": "Mysuru", "state": "Karnataka", "vaccination": 88.5, "inst_births": 99.8, "stunting": 28.4, "anemia_women": 47.8, "sanitation": 82.4, "water": 95.1, "insurance": 42.1},
    {"district": "Belagavi", "state": "Karnataka", "vaccination": 84.2, "inst_births": 98.9, "stunting": 33.6, "anemia_women": 52.1, "sanitation": 76.5, "water": 92.4, "insurance": 38.6},
    {"district": "Kalaburagi", "state": "Karnataka", "vaccination": 74.5, "inst_births": 97.2, "stunting": 42.8, "anemia_women": 62.4, "sanitation": 58.2, "water": 88.5, "insurance": 34.2},

    # Tamil Nadu
    {"district": "Chennai", "state": "Tamil Nadu", "vaccination": 89.2, "inst_births": 99.8, "stunting": 21.5, "anemia_women": 48.6, "sanitation": 97.8, "water": 99.1, "insurance": 56.4},
    {"district": "Coimbatore", "state": "Tamil Nadu", "vaccination": 91.4, "inst_births": 99.9, "stunting": 22.8, "anemia_women": 46.2, "sanitation": 91.5, "water": 97.8, "insurance": 68.2},
    {"district": "Madurai", "state": "Tamil Nadu", "vaccination": 88.7, "inst_births": 99.7, "stunting": 26.4, "anemia_women": 51.5, "sanitation": 84.6, "water": 96.2, "insurance": 65.1},
    {"district": "Kanchipuram", "state": "Tamil Nadu", "vaccination": 87.5, "inst_births": 99.6, "stunting": 25.1, "anemia_women": 50.1, "sanitation": 88.2, "water": 96.8, "insurance": 62.8},

    # Kerala
    {"district": "Thiruvananthapuram", "state": "Kerala", "vaccination": 92.4, "inst_births": 99.9, "stunting": 18.2, "anemia_women": 32.5, "sanitation": 98.8, "water": 96.5, "insurance": 58.9},
    {"district": "Ernakulam", "state": "Kerala", "vaccination": 94.1, "inst_births": 100.0, "stunting": 16.5, "anemia_women": 29.8, "sanitation": 99.4, "water": 97.8, "insurance": 64.5},
    {"district": "Wayanad", "state": "Kerala", "vaccination": 89.5, "inst_births": 99.5, "stunting": 24.5, "anemia_women": 38.6, "sanitation": 96.2, "water": 94.1, "insurance": 61.2},

    # Maharashtra
    {"district": "Mumbai Suburban", "state": "Maharashtra", "vaccination": 78.4, "inst_births": 99.2, "stunting": 31.2, "anemia_women": 54.2, "sanitation": 92.4, "water": 98.5, "insurance": 22.4},
    {"district": "Pune", "state": "Maharashtra", "vaccination": 83.6, "inst_births": 99.5, "stunting": 29.5, "anemia_women": 48.9, "sanitation": 88.5, "water": 96.4, "insurance": 31.8},
    {"district": "Nagpur", "state": "Maharashtra", "vaccination": 81.2, "inst_births": 98.8, "stunting": 32.1, "anemia_women": 53.4, "sanitation": 82.6, "water": 94.2, "insurance": 27.5},
    {"district": "Gadchiroli", "state": "Maharashtra", "vaccination": 69.8, "inst_births": 92.4, "stunting": 44.5, "anemia_women": 65.2, "sanitation": 54.1, "water": 85.2, "insurance": 38.4},

    # Gujarat
    {"district": "Ahmedabad", "state": "Gujarat", "vaccination": 79.5, "inst_births": 98.8, "stunting": 34.2, "anemia_women": 58.5, "sanitation": 86.4, "water": 96.2, "insurance": 32.1},
    {"district": "Surat", "state": "Gujarat", "vaccination": 77.2, "inst_births": 97.5, "stunting": 36.8, "anemia_women": 61.2, "sanitation": 84.1, "water": 94.5, "insurance": 29.4},
    {"district": "Rajkot", "state": "Gujarat", "vaccination": 82.1, "inst_births": 99.1, "stunting": 31.4, "anemia_women": 55.4, "sanitation": 81.5, "water": 95.8, "insurance": 35.8},
    {"district": "Vadodara", "state": "Gujarat", "vaccination": 80.4, "inst_births": 98.4, "stunting": 33.1, "anemia_women": 56.8, "sanitation": 83.2, "water": 95.1, "insurance": 33.2},

    # Uttar Pradesh
    {"district": "Varanasi", "state": "Uttar Pradesh", "vaccination": 72.4, "inst_births": 91.5, "stunting": 41.2, "anemia_women": 52.8, "sanitation": 72.4, "water": 96.4, "insurance": 18.5},
    {"district": "Lucknow", "state": "Uttar Pradesh", "vaccination": 76.5, "inst_births": 94.2, "stunting": 37.8, "anemia_women": 49.5, "sanitation": 82.1, "water": 97.5, "insurance": 21.4},
    {"district": "Gorakhpur", "state": "Uttar Pradesh", "vaccination": 68.2, "inst_births": 88.5, "stunting": 43.6, "anemia_women": 56.2, "sanitation": 68.5, "water": 95.2, "insurance": 16.8},
    {"district": "Bahraich", "state": "Uttar Pradesh", "vaccination": 54.1, "inst_births": 76.4, "stunting": 52.4, "anemia_women": 64.8, "sanitation": 48.2, "water": 92.1, "insurance": 14.2},

    # Bihar
    {"district": "Patna", "state": "Bihar", "vaccination": 75.8, "inst_births": 89.2, "stunting": 39.4, "anemia_women": 59.5, "sanitation": 68.4, "water": 96.8, "insurance": 17.5},
    {"district": "Gaya", "state": "Bihar", "vaccination": 66.4, "inst_births": 79.5, "stunting": 46.8, "anemia_women": 65.4, "sanitation": 52.1, "water": 94.2, "insurance": 13.8},
    {"district": "Muzaffarpur", "state": "Bihar", "vaccination": 71.2, "inst_births": 82.4, "stunting": 44.1, "anemia_women": 63.8, "sanitation": 56.4, "water": 95.5, "insurance": 15.2},
    {"district": "Purnia", "state": "Bihar", "vaccination": 62.5, "inst_births": 74.8, "stunting": 49.5, "anemia_women": 68.2, "sanitation": 44.8, "water": 91.2, "insurance": 12.4},

    # Rajasthan
    {"district": "Jaipur", "state": "Rajasthan", "vaccination": 82.4, "inst_births": 97.5, "stunting": 32.5, "anemia_women": 53.4, "sanitation": 78.5, "water": 92.4, "insurance": 86.4},
    {"district": "Jodhpur", "state": "Rajasthan", "vaccination": 78.5, "inst_births": 95.4, "stunting": 35.8, "anemia_women": 56.2, "sanitation": 72.4, "water": 88.5, "insurance": 84.1},
    {"district": "Udaipur", "state": "Rajasthan", "vaccination": 74.2, "inst_births": 92.8, "stunting": 43.1, "anemia_women": 61.5, "sanitation": 62.8, "water": 86.4, "insurance": 82.5},
    {"district": "Jaisalmer", "state": "Rajasthan", "vaccination": 71.5, "inst_births": 91.2, "stunting": 39.4, "anemia_women": 58.9, "sanitation": 58.4, "water": 82.1, "insurance": 79.8},

    # West Bengal
    {"district": "Kolkata", "state": "West Bengal", "vaccination": 88.4, "inst_births": 99.1, "stunting": 23.4, "anemia_women": 54.8, "sanitation": 94.2, "water": 98.4, "insurance": 42.5},
    {"district": "Darjeeling", "state": "West Bengal", "vaccination": 86.2, "inst_births": 96.5, "stunting": 29.8, "anemia_women": 58.2, "sanitation": 86.5, "water": 92.5, "insurance": 48.2},
    {"district": "Murshidabad", "state": "West Bengal", "vaccination": 79.5, "inst_births": 92.4, "stunting": 38.6, "anemia_women": 66.4, "sanitation": 68.2, "water": 95.8, "insurance": 46.1},

    # Madhya Pradesh
    {"district": "Bhopal", "state": "Madhya Pradesh", "vaccination": 78.6, "inst_births": 96.4, "stunting": 34.2, "anemia_women": 52.1, "sanitation": 81.2, "water": 95.4, "insurance": 38.4},
    {"district": "Indore", "state": "Madhya Pradesh", "vaccination": 82.1, "inst_births": 98.2, "stunting": 31.5, "anemia_women": 49.8, "sanitation": 89.4, "water": 96.8, "insurance": 41.2},
    {"district": "Jabalpur", "state": "Madhya Pradesh", "vaccination": 76.4, "inst_births": 94.8, "stunting": 37.1, "anemia_women": 55.4, "sanitation": 76.5, "water": 93.8, "insurance": 36.8},
    {"district": "Balaghat", "state": "Madhya Pradesh", "vaccination": 73.1, "inst_births": 91.2, "stunting": 42.5, "anemia_women": 61.2, "sanitation": 64.2, "water": 89.5, "insurance": 44.5},

    # Odisha
    {"district": "Khurda", "state": "Odisha", "vaccination": 89.2, "inst_births": 98.8, "stunting": 26.5, "anemia_women": 58.4, "sanitation": 82.4, "water": 94.5, "insurance": 52.4},
    {"district": "Cuttack", "state": "Odisha", "vaccination": 87.8, "inst_births": 98.2, "stunting": 28.2, "anemia_women": 60.1, "sanitation": 79.8, "water": 93.8, "insurance": 49.8},
    {"district": "Kalahandi", "state": "Odisha", "vaccination": 78.4, "inst_births": 92.1, "stunting": 44.8, "anemia_women": 67.5, "sanitation": 56.4, "water": 88.2, "insurance": 64.2},

    # Assam
    {"district": "Kamrup Metropolitan", "state": "Assam", "vaccination": 76.8, "inst_births": 95.4, "stunting": 29.8, "anemia_women": 62.4, "sanitation": 88.5, "water": 94.2, "insurance": 38.5},
    {"district": "Dibrugarh", "state": "Assam", "vaccination": 72.4, "inst_births": 89.5, "stunting": 34.6, "anemia_women": 67.8, "sanitation": 79.2, "water": 91.5, "insurance": 42.1},
    {"district": "Cachar", "state": "Assam", "vaccination": 68.5, "inst_births": 84.2, "stunting": 40.5, "anemia_women": 71.2, "sanitation": 72.4, "water": 89.8, "insurance": 36.4},
]


def prepare_health_indicators():
    raw_path = RAW_DIR / "nfhs5_indicators_raw.json"
    raw_path.write_text(json.dumps(NFHS_5_INDICATORS_RAW, indent=2), encoding="utf-8")
    print(f"[OK] Saved raw NFHS-5 records: {raw_path} ({len(NFHS_5_INDICATORS_RAW)} records)")

    normalized_records = []
    indicator_mapping = [
        ("children_fully_vaccinated_pct", "vaccination", "Children age 12-23 months fully vaccinated"),
        ("institutional_births_pct", "inst_births", "Institutional births in health facilities"),
        ("stunted_children_under_5_pct", "stunting", "Children under 5 years who are stunted (height-for-age)"),
        ("anemic_pregnant_women_pct", "anemia_women", "Pregnant women age 15-49 years who are anaemic"),
        ("households_with_improved_sanitation_pct", "sanitation", "Population living in households with improved sanitation facility"),
        ("households_with_improved_drinking_water_pct", "water", "Population living in households with improved drinking-water source"),
        ("health_insurance_coverage_pct", "insurance", "Households with at least one member covered under health insurance")
    ]

    for item in NFHS_5_INDICATORS_RAW:
        norm = district_normalizer.normalize(item["district"], item["state"])

        for ind_name, key, description in indicator_mapping:
            val = float(item[key])
            assert 0.0 <= val <= 100.0, f"Indicator value out of bounds: {val} in {item['district']}"

            normalized_records.append({
                "district_id": str(norm["district_id"]),
                "district_name": norm["district_name"],
                "state": norm["state"],
                "country": norm["country"],
                "indicator_name": ind_name,
                "indicator_value": val,
                "unit": "%",
                "year": 2020,
                "source": "National Family Health Survey (NFHS-5) 2019-2021",
                "source_reference": f"IIPS Mumbai & MoHFW, Government of India. Factsheet Indicator: {description}",
                "metadata": {
                    "survey_round": "NFHS-5",
                    "description": description,
                    "target_population": "District Aggregate"
                },
                "data_type": "official"
            })

    proc_path = PROCESSED_DIR / "health_indicators_normalized.json"
    proc_path.write_text(json.dumps(normalized_records, indent=2), encoding="utf-8")
    print(f"[OK] Saved processed health indicators: {proc_path} ({len(normalized_records)} indicator records)")

    return normalized_records


if __name__ == "__main__":
    prepare_health_indicators()
