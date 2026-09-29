"""
District Intelligence Representation & Assembler (Phase 6).
Fuses demographics, public infrastructure, health indicators, synthetic investments,
and citizen demand into unified district intelligence records with complete provenance.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from app.services.infrastructure.metrics import (
    aggregate_healthcare_infrastructure,
    aggregate_district_investments,
    aggregate_health_indicators
)
from app.services.infrastructure.demand_metrics import calculate_district_demand_metrics
from app.services.infrastructure.gap_detector import GapSignalDetector


class DistrictIntelligenceAssembler:
    """
    Assembles holistic district-level intelligence by fusing multidimensional DPI datasets.
    """

    @staticmethod
    def build_data_provenance_records(
        has_census: bool = True,
        has_hmis: bool = True,
        has_nfhs: bool = True,
        has_investments: bool = True,
        has_requests: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Builds transparent provenance records for all data sources consumed.
        """
        records = []
        if has_census:
            records.append({
                "metric": "Demographics & Population",
                "source": "Census of India 2011, Office of the Registrar General & Census Commissioner, India",
                "source_type": "official",
                "is_synthetic": False,
                "data_type": "official",
                "source_year": 2011,
                "notes": "Historical decennial baseline; not projected 2026 population."
            })
        if has_hmis:
            records.append({
                "metric": "Healthcare Infrastructure",
                "source": "Health Management Information System (HMIS) / MoHFW, Government of India",
                "source_type": "official",
                "is_synthetic": False,
                "data_type": "official",
                "source_year": 2023,
                "notes": "Public health facility master: District Hospitals, CHCs, bed capacity, doctors."
            })
        if has_nfhs:
            records.append({
                "metric": "Health & Water Indicators",
                "source": "National Family Health Survey (NFHS-5) 2019-2021, IIPS Mumbai & MoHFW",
                "source_type": "official",
                "is_synthetic": False,
                "data_type": "official",
                "source_year": 2020,
                "notes": "District factsheet indicators: immunization, institutional deliveries, sanitation."
            })
        if has_investments:
            records.append({
                "metric": "Public Capital Investments",
                "source": "GFD Synthetic Investment Engine (Simulation Model for MVP Evaluation)",
                "source_type": "synthetic",
                "is_synthetic": True,
                "data_type": "synthetic",
                "source_year": 2022,
                "notes": "Synthetic capital outlay allocations created for DPI Hackathon challenge."
            })
        if has_requests:
            records.append({
                "metric": "Citizen Grievances & Demand",
                "source": "GFD Citizen Submission Portal & Hotspot Demand Engine",
                "source_type": "synthetic_and_user",
                "is_synthetic": True,
                "data_type": "hybrid",
                "source_year": 2025,
                "notes": "Citizen requests represent active civic feedback, not a random survey."
            })
        return records

    @classmethod
    def assemble_sector_intelligence(
        cls,
        district_id: str,
        district_name: str,
        state: str,
        sector: str,
        demographics: Optional[Dict[str, Any]],
        facilities: List[Dict[str, Any]],
        indicators: List[Dict[str, Any]],
        investments: List[Dict[str, Any]],
        requests: List[Dict[str, Any]],
        clusters: Optional[List[Dict[str, Any]]] = None,
        demand_percentile: Optional[float] = None,
        infrastructure_percentile: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assembles a complete district intelligence profile for a specific infrastructure sector.
        """
        population = demographics.get("population") if demographics else None
        pop_source = demographics.get("source") if demographics else "Census 2011"

        # 1. Demand metrics
        demand_metrics = calculate_district_demand_metrics(
            requests=requests,
            population=population,
            clusters=clusters
        )

        # 2. Sector Infrastructure metrics
        if sector.lower() == "healthcare":
            infra_metrics = aggregate_healthcare_infrastructure(facilities, population)
        elif sector.lower() == "water":
            # Extract water indicators from NFHS-5
            water_inds = {
                ind.get("indicator_name"): ind.get("indicator_value")
                for ind in indicators
                if "water" in str(ind.get("indicator_name")).lower() or "sanitation" in str(ind.get("indicator_name")).lower()
            }
            infra_metrics = {
                "data_available": len(water_inds) > 0,
                "facility_count": len(facilities),
                "indicators": water_inds
            }
        elif sector.lower() == "education":
            lit = demographics.get("demographic_indicators", {}).get("literacy_rate") if demographics else None
            infra_metrics = {
                "data_available": lit is not None,
                "facility_count": len(facilities),
                "literacy_rate": lit
            }
        else:
            infra_metrics = {
                "data_available": len(facilities) > 0,
                "facility_count": len(facilities)
            }

        # 3. Health context
        health_metrics = aggregate_health_indicators(indicators)

        # 4. Investment context
        sector_investments = [
            inv for inv in investments 
            if (inv.get("category") or "").lower() == sector.lower()
        ]
        invest_metrics = aggregate_district_investments(sector_investments, population)

        # 5. Provenance records
        data_sources = cls.build_data_provenance_records(
            has_census=demographics is not None,
            has_hmis=len(facilities) > 0,
            has_nfhs=len(indicators) > 0,
            has_investments=len(investments) > 0,
            has_requests=len(requests) > 0
        )

        # 6. Evaluate gap signal
        gap_signal = GapSignalDetector.evaluate_sector_gap_signal(
            sector=sector,
            demand_percentile=demand_percentile,
            infrastructure_percentile=infrastructure_percentile,
            demand_metrics=demand_metrics,
            infrastructure_metrics=infra_metrics,
            cluster_metrics=demand_metrics.get("cluster_metrics"),
            data_sources=data_sources
        )

        return {
            "id": str(uuid4()),
            "district_id": str(district_id),
            "district_name": district_name,
            "state": state,
            "sector": sector,
            "population": population,
            "population_source": pop_source,
            "total_requests": demand_metrics["total_requests"],
            "requests_last_7_days": demand_metrics["requests_last_7_days"],
            "requests_previous_7_days": demand_metrics["requests_previous_7_days"],
            "request_growth_percentage": demand_metrics["request_growth_percentage"],
            "requests_per_10000": demand_metrics["requests_per_10000"],
            "demand_percentile": demand_percentile,
            "infrastructure_percentile": infrastructure_percentile,
            "demand_metrics": demand_metrics,
            "infrastructure_metrics": infra_metrics,
            "health_metrics": health_metrics,
            "investment_metrics": invest_metrics,
            "cluster_metrics": demand_metrics.get("cluster_metrics", {}),
            "mismatch_signal": gap_signal.get("signal_type", "balanced"),
            "gap_signal": gap_signal,
            "data_sources": data_sources,
            "computed_at": datetime.now(timezone.utc).isoformat()
        }
