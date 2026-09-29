"""
Infrastructure & Demographic Metrics Service (Phase 6).
Computes sector-specific infrastructure indicators, population normalizations,
relative cross-district percentiles, and maintains strict data provenance.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calculate_population_ratio(
    metric_value: Optional[float],
    population: Optional[int],
    multiplier: float = 10000.0
) -> Optional[float]:
    """
    Computes population-normalized ratio: (metric_value / population) * multiplier.
    Returns None if population is missing, zero, or metric_value is None.
    Avoids division by zero.
    """
    if metric_value is None or population is None or population <= 0:
        return None
    try:
        ratio = (float(metric_value) / float(population)) * multiplier
        return round(ratio, 4)
    except Exception:
        return None


def calculate_percentile_rank(
    values_by_id: Dict[str, Optional[float]],
    higher_is_better: bool = True
) -> Tuple[Dict[str, Optional[float]], bool]:
    """
    Computes percentile rank (0 to 100) for each entity across all valid values.
    Returns (percentile_dict, benchmark_available).
    If fewer than 3 valid values exist, benchmark_available is False.
    """
    valid_items = [(k, float(v)) for k, v in values_by_id.items() if v is not None]
    if len(valid_items) < 3:
        return ({k: None for k in values_by_id}, False)

    # Sort values
    sorted_values = sorted([v for _, v in valid_items])
    n = len(sorted_values)

    percentiles = {}
    for k, v in values_by_id.items():
        if v is None:
            percentiles[k] = None
            continue
        val = float(v)
        # Percentile rank: proportion of values <= val
        rank = sum(1 for x in sorted_values if x <= val)
        pct = round((rank / n) * 100.0, 1)
        if not higher_is_better:
            pct = round(100.0 - pct, 1)
        percentiles[k] = pct

    return (percentiles, True)


def aggregate_healthcare_infrastructure(
    facilities: List[Dict[str, Any]],
    population: Optional[int]
) -> Dict[str, Any]:
    """
    Aggregates HMIS healthcare infrastructure facilities for a district.
    Calculates beds, ICU beds, doctors, and ratios per 10,000 population.
    """
    if not facilities:
        return {
            "data_available": False,
            "facility_count": 0,
            "hospital_count": 0,
            "total_beds": 0,
            "icu_beds": 0,
            "doctor_count": 0,
            "beds_per_10000": None,
            "doctors_per_10000": None,
            "facility_breakdown": {}
        }

    total_beds = 0
    total_icu = 0
    total_doctors = 0
    facility_types: Dict[str, int] = {}
    hospitals = 0

    for fac in facilities:
        cap = fac.get("capacity_value") or {}
        ftype = cap.get("facility_type") or "Health Facility"
        facility_types[ftype] = facility_types.get(ftype, 0) + 1

        if "hospital" in ftype.lower():
            hospitals += 1

        beds = cap.get("bed_count") or cap.get("beds") or 0
        icu = cap.get("icu_beds") or 0
        docs = cap.get("doctors") or cap.get("doctor_count") or 0

        total_beds += int(beds)
        total_icu += int(icu)
        total_doctors += int(docs)

    return {
        "data_available": True,
        "facility_count": len(facilities),
        "hospital_count": hospitals,
        "total_beds": total_beds,
        "icu_beds": total_icu,
        "doctor_count": total_doctors,
        "beds_per_10000": calculate_population_ratio(total_beds, population, 10000.0),
        "doctors_per_10000": calculate_population_ratio(total_doctors, population, 10000.0),
        "facility_breakdown": facility_types
    }


def aggregate_district_investments(
    investments: List[Dict[str, Any]],
    population: Optional[int]
) -> Dict[str, Any]:
    """
    Aggregates investment data for a district by category and fiscal year.
    Preserves synthetic provenance metadata.
    """
    if not investments:
        return {
            "data_available": False,
            "total_investment": 0.0,
            "investment_per_capita": None,
            "by_sector": {},
            "by_year": {},
            "is_synthetic": True
        }

    total = 0.0
    by_sector: Dict[str, float] = {}
    by_year: Dict[str, float] = {}
    is_synth = True

    for inv in investments:
        amt = float(inv.get("amount") or 0.0)
        total += amt

        cat = (inv.get("category") or "other").lower()
        by_sector[cat] = by_sector.get(cat, 0.0) + amt

        yr = str(inv.get("financial_year") or "unknown")
        by_year[yr] = by_year.get(yr, 0.0) + amt

        if inv.get("data_type") == "official" or inv.get("is_synthetic") is False:
            is_synth = False

    per_capita = round(total / float(population), 2) if population and population > 0 else None

    return {
        "data_available": True,
        "total_investment": round(total, 2),
        "investment_per_capita": per_capita,
        "by_sector": {k: round(v, 2) for k, v in by_sector.items()},
        "by_year": {k: round(v, 2) for k, v in by_year.items()},
        "is_synthetic": is_synth,
        "currency": "INR"
    }


def aggregate_health_indicators(
    indicators: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Extracts key NFHS-5 factsheet indicators for health and water/sanitation context.
    """
    if not indicators:
        return {"data_available": False, "indicators": {}}

    res = {}
    for ind in indicators:
        name = ind.get("indicator_name")
        val = ind.get("indicator_value")
        if name and val is not None:
            res[name] = float(val)

    return {
        "data_available": True,
        "indicators": res,
        "survey_round": "NFHS-5 (2019-2021)",
        "source": "International Institute for Population Sciences (IIPS) & MoHFW"
    }
