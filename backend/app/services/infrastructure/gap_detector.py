"""
Infrastructure Gap Detection & Mismatch Analysis Service (Phase 6).
Generates explainable, decision-support gap signals by comparing citizen demand
with observed public infrastructure availability across districts.
Strictly avoids opaque priority scoring or premature conclusions.
"""

from typing import Dict, Any, List, Optional, Tuple


class GapSignalDetector:
    """
    Evaluates relative demand vs infrastructure percentiles to generate
    transparent, explainable infrastructure pressure and gap signals.
    """

    @staticmethod
    def evaluate_sector_gap_signal(
        sector: str,
        demand_percentile: Optional[float],
        infrastructure_percentile: Optional[float],
        demand_metrics: Dict[str, Any],
        infrastructure_metrics: Dict[str, Any],
        cluster_metrics: Optional[Dict[str, Any]] = None,
        data_sources: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates demand vs supply mismatch for a specific sector in a district.
        Returns a structured signal with complete explainable evidence.
        """
        # If insufficient data to benchmark
        if demand_percentile is None and infrastructure_percentile is None:
            return {
                "signal_type": "insufficient_data",
                "severity": "none",
                "mismatch_state": "insufficient_data",
                "summary": f"Insufficient data to evaluate {sector} infrastructure pressure.",
                "evidence": {
                    "what_was_observed": "No benchmarkable citizen requests or infrastructure records available.",
                    "infrastructure_observed": "Data unavailable.",
                    "why_signal_generated": "Both demand and infrastructure datasets lack sufficient coverage for relative ranking.",
                    "datasets_used": [ds.get("metric") for ds in (data_sources or [])]
                }
            }

        if infrastructure_percentile is None or not infrastructure_metrics.get("data_available", True):
            # Demand exists but infrastructure data not in public datasets
            tot_req = demand_metrics.get("total_requests", 0)
            return {
                "signal_type": "demand_signal_only",
                "severity": "low" if (demand_percentile or 0) < 70 else "medium",
                "mismatch_state": "infrastructure_data_absent",
                "summary": f"Active citizen demand observed ({tot_req} requests), but public {sector} infrastructure dataset is unavailable.",
                "evidence": {
                    "what_was_observed": f"{tot_req} citizen requests recorded (Demand percentile: {demand_percentile or 'N/A'}).",
                    "infrastructure_observed": f"No public {sector} facility data available in benchmark registry.",
                    "why_signal_generated": "Demand exists without matching public supply dataset.",
                    "datasets_used": [ds.get("metric") for ds in (data_sources or [])]
                }
            }

        dp = float(demand_percentile or 0.0)
        ip = float(infrastructure_percentile or 50.0)
        gap_delta = dp - ip  # positive means demand exceeds relative infrastructure

        # Check for cluster concentration
        top_cluster = cluster_metrics.get("top_cluster") if cluster_metrics else None
        top_cluster_share = cluster_metrics.get("top_cluster_percentage", 0.0) if cluster_metrics else 0.0

        # Rules for signals
        # 1. Potential Gap (High demand + low infrastructure)
        if dp >= 60.0 and ip <= 40.0:
            severity = "high" if (dp >= 80.0 and ip <= 25.0) else "medium"
            signal_type = "potential_gap"
            mismatch_state = "high_demand_low_infrastructure"
            desc = (
                f"High observed citizen demand ({dp:.0f}th percentile) coincides with "
                f"relatively low observed {sector.lower()} infrastructure ({ip:.0f}th percentile)."
            )
            why = (
                f"Citizen demand is significantly higher than most districts while observed "
                f"infrastructure availability per capita is among the lower tiers."
            )

        # 2. Infrastructure Pressure (High demand with moderate infrastructure)
        elif dp >= 75.0 and ip <= 65.0:
            severity = "medium"
            signal_type = "infrastructure_pressure"
            mismatch_state = "high_demand_moderate_infrastructure"
            desc = (
                f"Substantial citizen demand ({dp:.0f}th percentile) is placing pressure on "
                f"moderate existing infrastructure ({ip:.0f}th percentile)."
            )
            why = f"High citizen grievance density indicates potential localized capacity strain."

        # 3. Demand / Supply Signal (Strong cluster concentration or sudden surge)
        elif top_cluster_share >= 50.0 and dp >= 50.0:
            severity = "medium"
            signal_type = "demand_supply_signal"
            mismatch_state = "concentrated_cluster_demand"
            desc = (
                f"Concentrated citizen demand detected: {top_cluster_share:.0f}% of {sector.lower()} "
                f"requests cluster around '{top_cluster}'."
            )
            why = f"Distinct grievance cluster indicates a specific infrastructure deficiency."

        # 4. Low demand + High infrastructure
        elif dp <= 30.0 and ip >= 70.0:
            severity = "none"
            signal_type = "adequate_coverage"
            mismatch_state = "low_demand_high_infrastructure"
            desc = (
                f"Low relative citizen demand ({dp:.0f}th percentile) with relatively high "
                f"observed infrastructure availability ({ip:.0f}th percentile)."
            )
            why = f"Infrastructure availability appears favorable relative to reported citizen grievances."

        # 5. Balanced
        else:
            severity = "low"
            signal_type = "balanced"
            mismatch_state = "balanced"
            desc = (
                f"Observed demand ({dp:.0f}th percentile) and infrastructure availability "
                f"({ip:.0f}th percentile) are relatively balanced."
            )
            why = f"Demand and infrastructure metrics are in similar relative tiers across districts."

        # Concrete observations for explainability
        what_observed = f"{demand_metrics.get('total_requests', 0)} requests ({demand_metrics.get('requests_per_10000', 'N/A')} per 10k population, {dp:.0f}th percentile)."
        if sector.lower() == "healthcare":
            infra_observed = f"{infrastructure_metrics.get('hospital_count', 0)} hospitals, {infrastructure_metrics.get('total_beds', 0)} beds ({infrastructure_metrics.get('beds_per_10000', 'N/A')} beds/10k, {ip:.0f}th percentile)."
        else:
            infra_observed = f"{infrastructure_metrics.get('facility_count', 0)} facilities observed ({ip:.0f}th percentile)."

        return {
            "signal_type": signal_type,
            "severity": severity,
            "mismatch_state": mismatch_state,
            "demand_percentile": dp,
            "infrastructure_percentile": ip,
            "gap_delta": round(gap_delta, 1),
            "summary": desc,
            "evidence": {
                "what_was_observed": what_observed,
                "infrastructure_observed": infra_observed,
                "why_signal_generated": why,
                "datasets_used": [ds.get("metric") for ds in (data_sources or [])]
            }
        }
