#!/usr/bin/env python3
"""
District Investment Allocations Pipeline (Synthetic / Demonstration)
Generates explicitly tagged synthetic investment records for public infrastructure categories.
Outputs to data/processed/investments_normalized.json.
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from district_normalizer import district_normalizer

PROCESSED_DIR = Path(__file__).parent.parent / "processed"
DISTRICTS_FILE = PROCESSED_DIR / "districts_normalized.json"

CATEGORIES = ["healthcare", "education", "roads", "water", "electricity"]
FINANCIAL_YEARS = ["2021-2022", "2022-2023", "2023-2024"]

# Deterministic seed for exact reproducibility across runs
RANDOM_SEED = 42


def generate_investments():
    assert DISTRICTS_FILE.exists(), f"Districts file {DISTRICTS_FILE} not found. Run prepare_districts_gis.py first."
    districts = json.loads(DISTRICTS_FILE.read_text(encoding="utf-8"))

    rng = random.Random(RANDOM_SEED)
    investments = []

    for dist in districts:
        pop = dist.get("population_ref", 2000000)
        # Base funding per capita factor roughly scaled for realism (50 to 500 INR per capita per sector)
        scale_factor = pop / 1000000.0

        for fy in FINANCIAL_YEARS:
            for cat in CATEGORIES:
                # Add sector-specific variability and growth over financial years
                year_multiplier = 1.0 + (FINANCIAL_YEARS.index(fy) * 0.12)
                base_amount = rng.uniform(15000000.0, 85000000.0) * scale_factor * year_multiplier
                amount = round(base_amount, 2)

                investments.append({
                    "district_id": dist["id"],
                    "district_name": dist["name"],
                    "state": dist["state"],
                    "country": dist["country"],
                    "category": cat,
                    "amount": amount,
                    "currency": "INR",
                    "financial_year": fy,
                    "source": "demo-generated",
                    "source_reference": "GFD Synthetic Investment Engine (Simulation Model for MVP Evaluation)",
                    "data_type": "synthetic"
                })

    proc_path = PROCESSED_DIR / "investments_normalized.json"
    proc_path.write_text(json.dumps(investments, indent=2), encoding="utf-8")
    print(f"[OK] Saved processed investments: {proc_path} ({len(investments)} records across {len(districts)} districts)")
    return investments


if __name__ == "__main__":
    generate_investments()
