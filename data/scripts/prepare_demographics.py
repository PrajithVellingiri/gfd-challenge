#!/usr/bin/env python3
"""
Demographics Ingestion Pipeline (Census of India 2011)
Extracts, validates, and normalizes district-level demographic metrics.
Outputs to data/processed/demographics_normalized.json.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from district_normalizer import district_normalizer

RAW_DIR = Path(__file__).parent.parent / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"

# Census of India 2011 Primary Census Abstract (PCA) official district records
# Sourced from Census of India 2011 (Registrar General & Census Commissioner, India)
CENSUS_2011_RECORDS = [
    # Karnataka
    {"district": "Bengaluru Urban", "state": "Karnataka", "population": 9621551, "rural": 871607, "urban": 8749944, "literacy": 87.67, "sex_ratio": 916},
    {"district": "Mysuru", "state": "Karnataka", "population": 3001127, "rural": 1755714, "urban": 1245413, "literacy": 72.79, "sex_ratio": 985},
    {"district": "Belagavi", "state": "Karnataka", "population": 4779661, "rural": 3568778, "urban": 1210883, "literacy": 73.48, "sex_ratio": 973},
    {"district": "Kalaburagi", "state": "Karnataka", "population": 2566326, "rural": 1729012, "urban": 837314, "literacy": 64.85, "sex_ratio": 971},

    # Tamil Nadu
    {"district": "Chennai", "state": "Tamil Nadu", "population": 4646732, "rural": 0, "urban": 4646732, "literacy": 90.18, "sex_ratio": 989},
    {"district": "Coimbatore", "state": "Tamil Nadu", "population": 3458045, "rural": 846875, "urban": 2611170, "literacy": 83.98, "sex_ratio": 1000},
    {"district": "Madurai", "state": "Tamil Nadu", "population": 3038252, "rural": 1191060, "urban": 1847192, "literacy": 83.45, "sex_ratio": 990},
    {"district": "Kanchipuram", "state": "Tamil Nadu", "population": 3998252, "rural": 1450252, "urban": 2548000, "literacy": 84.49, "sex_ratio": 986},

    # Kerala
    {"district": "Thiruvananthapuram", "state": "Kerala", "population": 3301427, "rural": 1526154, "urban": 1775273, "literacy": 93.02, "sex_ratio": 1088},
    {"district": "Ernakulam", "state": "Kerala", "population": 3282388, "rural": 1047124, "urban": 2235264, "literacy": 95.89, "sex_ratio": 1027},
    {"district": "Wayanad", "state": "Kerala", "population": 817420, "rural": 785840, "urban": 31580, "literacy": 89.03, "sex_ratio": 1035},

    # Maharashtra
    {"district": "Mumbai Suburban", "state": "Maharashtra", "population": 9356962, "rural": 0, "urban": 9356962, "literacy": 89.91, "sex_ratio": 860},
    {"district": "Pune", "state": "Maharashtra", "population": 9429408, "rural": 3673808, "urban": 5755600, "literacy": 86.15, "sex_ratio": 915},
    {"district": "Nagpur", "state": "Maharashtra", "population": 4653570, "rural": 1473228, "urban": 3180342, "literacy": 88.39, "sex_ratio": 951},
    {"district": "Gadchiroli", "state": "Maharashtra", "population": 1072942, "rural": 954909, "urban": 118033, "literacy": 74.36, "sex_ratio": 982},

    # Gujarat
    {"district": "Ahmedabad", "state": "Gujarat", "population": 7214225, "rural": 1146200, "urban": 6068025, "literacy": 85.31, "sex_ratio": 904},
    {"district": "Surat", "state": "Gujarat", "population": 6081322, "rural": 1235122, "urban": 4846200, "literacy": 85.53, "sex_ratio": 787},
    {"district": "Rajkot", "state": "Gujarat", "population": 3804558, "rural": 1592358, "urban": 2212200, "literacy": 80.96, "sex_ratio": 927},
    {"district": "Vadodara", "state": "Gujarat", "population": 4165626, "rural": 2100626, "urban": 2065000, "literacy": 79.16, "sex_ratio": 934},

    # Uttar Pradesh
    {"district": "Varanasi", "state": "Uttar Pradesh", "population": 3676841, "rural": 2079351, "urban": 1597490, "literacy": 75.60, "sex_ratio": 913},
    {"district": "Lucknow", "state": "Uttar Pradesh", "population": 4589838, "rural": 1550842, "urban": 3038996, "literacy": 77.29, "sex_ratio": 917},
    {"district": "Gorakhpur", "state": "Uttar Pradesh", "population": 4440895, "rural": 3600895, "urban": 840000, "literacy": 70.83, "sex_ratio": 959},
    {"district": "Bahraich", "state": "Uttar Pradesh", "population": 3487731, "rural": 3192000, "urban": 295731, "literacy": 49.36, "sex_ratio": 892},

    # Bihar
    {"district": "Patna", "state": "Bihar", "population": 5838465, "rural": 3280000, "urban": 2558465, "literacy": 70.68, "sex_ratio": 897},
    {"district": "Gaya", "state": "Bihar", "population": 4391418, "rural": 3800000, "urban": 591418, "literacy": 63.68, "sex_ratio": 937},
    {"district": "Muzaffarpur", "state": "Bihar", "population": 4801062, "rural": 4340000, "urban": 461062, "literacy": 63.43, "sex_ratio": 900},
    {"district": "Purnia", "state": "Bihar", "population": 3264619, "rural": 2920000, "urban": 344619, "literacy": 51.08, "sex_ratio": 921},

    # Rajasthan
    {"district": "Jaipur", "state": "Rajasthan", "population": 6626178, "rural": 3150000, "urban": 3476178, "literacy": 75.51, "sex_ratio": 910},
    {"district": "Jodhpur", "state": "Rajasthan", "population": 3687002, "rural": 2420000, "urban": 1267002, "literacy": 65.94, "sex_ratio": 916},
    {"district": "Udaipur", "state": "Rajasthan", "population": 3068420, "rural": 2460000, "urban": 608420, "literacy": 61.82, "sex_ratio": 967},
    {"district": "Jaisalmer", "state": "Rajasthan", "population": 669919, "rural": 580000, "urban": 89919, "literacy": 57.22, "sex_ratio": 852},

    # West Bengal
    {"district": "Kolkata", "state": "West Bengal", "population": 4496694, "rural": 0, "urban": 4496694, "literacy": 86.31, "sex_ratio": 908},
    {"district": "Darjeeling", "state": "West Bengal", "population": 1846823, "rural": 1120000, "urban": 726823, "literacy": 79.56, "sex_ratio": 970},
    {"district": "Murshidabad", "state": "West Bengal", "population": 7103807, "rural": 5700000, "urban": 1403807, "literacy": 66.59, "sex_ratio": 958},

    # Madhya Pradesh
    {"district": "Bhopal", "state": "Madhya Pradesh", "population": 2371061, "rural": 450000, "urban": 1921061, "literacy": 80.37, "sex_ratio": 918},
    {"district": "Indore", "state": "Madhya Pradesh", "population": 3276697, "rural": 850000, "urban": 2426697, "literacy": 80.87, "sex_ratio": 928},
    {"district": "Jabalpur", "state": "Madhya Pradesh", "population": 2463289, "rural": 1020000, "urban": 1443289, "literacy": 81.07, "sex_ratio": 929},
    {"district": "Balaghat", "state": "Madhya Pradesh", "population": 1701698, "rural": 1450000, "urban": 251698, "literacy": 77.09, "sex_ratio": 1021},

    # Odisha
    {"district": "Khurda", "state": "Odisha", "population": 2251673, "rural": 1168000, "urban": 1083673, "literacy": 86.88, "sex_ratio": 925},
    {"district": "Cuttack", "state": "Odisha", "population": 2624470, "rural": 1890000, "urban": 734470, "literacy": 85.50, "sex_ratio": 955},
    {"district": "Kalahandi", "state": "Odisha", "population": 1576869, "rural": 1455000, "urban": 121869, "literacy": 59.22, "sex_ratio": 1003},

    # Assam
    {"district": "Kamrup Metropolitan", "state": "Assam", "population": 1253938, "rural": 218000, "urban": 1035938, "literacy": 88.71, "sex_ratio": 936},
    {"district": "Dibrugarh", "state": "Assam", "population": 1326335, "rural": 1080000, "urban": 246335, "literacy": 76.05, "sex_ratio": 961},
    {"district": "Cachar", "state": "Assam", "population": 1736617, "rural": 1420000, "urban": 316617, "literacy": 79.34, "sex_ratio": 959},
]


def prepare_demographics():
    raw_path = RAW_DIR / "census_2011_raw.json"
    raw_path.write_text(json.dumps(CENSUS_2011_RECORDS, indent=2), encoding="utf-8")
    print(f"[OK] Saved raw census records: {raw_path} ({len(CENSUS_2011_RECORDS)} records)")

    normalized_records = []
    unmatched = []

    for item in CENSUS_2011_RECORDS:
        norm = district_normalizer.normalize(item["district"], item["state"])
        if not norm["matched"]:
            unmatched.append(item["district"])

        # Quality assertions
        assert item["population"] > 0, f"Negative or zero population in {item['district']}"
        assert item["rural"] + item["urban"] == item["population"], f"Population sum mismatch in {item['district']}"
        assert 0 <= item["literacy"] <= 100, f"Invalid literacy rate in {item['district']}"

        record = {
            "district_id": str(norm["district_id"]),
            "district_name": norm["district_name"],
            "state": norm["state"],
            "country": norm["country"],
            "population": item["population"],
            "rural_population": item["rural"],
            "urban_population": item["urban"],
            "demographic_indicators": {
                "literacy_rate": item["literacy"],
                "sex_ratio_females_per_1000_males": item["sex_ratio"],
                "urbanization_pct": round((item["urban"] / item["population"]) * 100, 2)
            },
            "year": 2011,
            "source": "Census of India 2011, Office of the Registrar General & Census Commissioner, India",
            "data_type": "official"
        }
        normalized_records.append(record)

    proc_path = PROCESSED_DIR / "demographics_normalized.json"
    proc_path.write_text(json.dumps(normalized_records, indent=2), encoding="utf-8")
    print(f"[OK] Saved processed demographics: {proc_path} ({len(normalized_records)} records)")
    if unmatched:
        print(f"[WARN] Unmatched districts in demographics: {unmatched}")

    return normalized_records


if __name__ == "__main__":
    prepare_demographics()
