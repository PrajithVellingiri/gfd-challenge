"""
Infrastructure Intelligence Package (Phase 6).
Fuses citizen demand, request clusters, and public infrastructure datasets
to evaluate infrastructure pressure and potential gap signals.
"""

from .metrics import (
    calculate_population_ratio,
    calculate_percentile_rank,
    aggregate_healthcare_infrastructure,
    aggregate_district_investments,
    aggregate_health_indicators
)
from .demand_metrics import calculate_district_demand_metrics
from .gap_detector import GapSignalDetector
from .district_intelligence import DistrictIntelligenceAssembler
from .infrastructure_service import InfrastructureIntelligenceService, default_infrastructure_service

__all__ = [
    "calculate_population_ratio",
    "calculate_percentile_rank",
    "aggregate_healthcare_infrastructure",
    "aggregate_district_investments",
    "aggregate_health_indicators",
    "calculate_district_demand_metrics",
    "GapSignalDetector",
    "DistrictIntelligenceAssembler",
    "InfrastructureIntelligenceService",
    "default_infrastructure_service",
]
