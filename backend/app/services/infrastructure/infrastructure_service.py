"""
Infrastructure Intelligence Master Service (Phase 6).
Coordinates multi-dataset ingestion, population normalization, relative percentile benchmarking,
gap signal generation, and intelligence caching.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging

from app.config import settings
from app.db import (
    save_district_intelligence_records,
    fetch_district_intelligence,
    list_district_intelligence_records,
    fetch_clusters,
    list_citizen_requests,
    get_db_connection,
    get_supabase_client
)
from app.services.infrastructure.metrics import calculate_percentile_rank
from app.services.infrastructure.district_intelligence import DistrictIntelligenceAssembler

_possible_dirs = [
    Path(__file__).resolve().parents[4] / "data" / "processed",
    Path("data/processed").resolve(),
    Path("../data/processed").resolve(),
]
DATA_PROCESSED_DIR = next((d for d in _possible_dirs if d.exists()), _possible_dirs[0])


class InfrastructureIntelligenceService:
    """
    Fuses spatial, demographic, infrastructure, health indicator, and citizen demand
    datasets to detect public infrastructure pressure and gap signals across all districts.
    """

    SECTORS = ["Overall", "Healthcare", "Water", "Education", "Roads"]

    def __init__(self):
        self._cached_districts = None

    def _load_json_fallback(self, filename: str) -> List[Dict[str, Any]]:
        """Loads a processed JSON dataset from data/processed/ if database query is empty."""
        fpath = DATA_PROCESSED_DIR / filename
        if fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Could not read JSON fallback %s: %s", fpath, e)
        return []

    def load_districts(self) -> List[Dict[str, Any]]:
        """Loads canonical districts."""
        if settings.DATABASE_URL:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, name, state, country FROM public.districts ORDER BY name ASC;")
                        rows = cur.fetchall()
                        if rows:
                            return [dict(r) for r in rows]
                except Exception as e:
                    logger.warning("Failed to fetch districts from DB: %s", e)
                finally:
                    conn.close()

        # Fallback to local processed JSON
        raw = self._load_json_fallback("districts_normalized.json")
        return [
            {
                "id": str(d.get("district_id") or d.get("id")),
                "name": d.get("district_name") or d.get("name"),
                "state": d.get("state"),
                "country": d.get("country", "India")
            }
            for d in raw
        ]

    def load_demographics(self) -> Dict[str, Dict[str, Any]]:
        """Loads demographics keyed by district_id."""
        res: Dict[str, Dict[str, Any]] = {}
        if settings.DATABASE_URL:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT * FROM public.demographics;")
                        rows = cur.fetchall()
                        if rows:
                            for r in rows:
                                res[str(r["district_id"])] = dict(r)
                            return res
                except Exception as e:
                    logger.warning("Failed to fetch demographics from DB: %s", e)
                finally:
                    conn.close()

        # Fallback
        raw = self._load_json_fallback("demographics_normalized.json")
        for d in raw:
            did = str(d.get("district_id"))
            res[did] = d
        return res

    def load_infrastructure_facilities(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads infrastructure facilities grouped by district_id."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        if settings.DATABASE_URL:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT * FROM public.infrastructure;")
                        rows = cur.fetchall()
                        if rows:
                            for r in rows:
                                did = str(r["district_id"])
                                res.setdefault(did, []).append(dict(r))
                            return res
                except Exception as e:
                    logger.warning("Failed to fetch infrastructure from DB: %s", e)
                finally:
                    conn.close()

        raw = self._load_json_fallback("infrastructure_normalized.json")
        for f in raw:
            did = str(f.get("district_id"))
            res.setdefault(did, []).append(f)
        return res

    def load_health_indicators(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads health indicators grouped by district_id."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        if settings.DATABASE_URL:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT * FROM public.health_indicators;")
                        rows = cur.fetchall()
                        if rows:
                            for r in rows:
                                did = str(r["district_id"])
                                res.setdefault(did, []).append(dict(r))
                            return res
                except Exception as e:
                    logger.warning("Failed to fetch health indicators from DB: %s", e)
                finally:
                    conn.close()

        raw = self._load_json_fallback("health_indicators_normalized.json")
        for ind in raw:
            did = str(ind.get("district_id"))
            res.setdefault(did, []).append(ind)
        return res

    def load_investments(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads investments grouped by district_id."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        if settings.DATABASE_URL:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT * FROM public.investments;")
                        rows = cur.fetchall()
                        if rows:
                            for r in rows:
                                did = str(r["district_id"])
                                res.setdefault(did, []).append(dict(r))
                            return res
                except Exception as e:
                    logger.warning("Failed to fetch investments from DB: %s", e)
                finally:
                    conn.close()

        raw = self._load_json_fallback("investments_normalized.json")
        for inv in raw:
            did = str(inv.get("district_id"))
            res.setdefault(did, []).append(inv)
        return res

    def load_citizen_requests(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads citizen requests grouped by district_id."""
        res: Dict[str, List[Dict[str, Any]]] = {}
        if settings.DATABASE_URL:
            conn = get_db_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT id, district_id, category, urgency, status, created_at, location_name FROM public.citizen_requests;")
                        rows = cur.fetchall()
                        if rows:
                            for r in rows:
                                did = str(r.get("district_id"))
                                res.setdefault(did, []).append(dict(r))
                            return res
                except Exception as e:
                    logger.warning("Failed to fetch citizen requests from DB: %s", e)
                finally:
                    conn.close()

        raw = self._load_json_fallback("citizen_requests_normalized.json")
        for r in raw:
            did = str(r.get("district_id"))
            res.setdefault(did, []).append(r)
        return res

    def refresh_all_intelligence(self) -> Dict[str, Any]:
        """
        Executes full deterministic calculation of district intelligence across all districts and sectors.
        Updates public.district_intelligence.
        """
        districts = self.load_districts()
        demographics = self.load_demographics()
        infrastructure = self.load_infrastructure_facilities()
        health_indicators = self.load_health_indicators()
        investments = self.load_investments()
        citizen_requests = self.load_citizen_requests()
        all_clusters = fetch_clusters()

        # Map clusters by (district_id, category)
        clusters_by_dist_cat: Dict[tuple, List[Dict[str, Any]]] = {}
        for c in all_clusters:
            did = str(c.get("district_id")) if c.get("district_id") else None
            cat = str(c.get("category", "")).lower()
            clusters_by_dist_cat.setdefault((did, cat), []).append(c)

        all_generated_records: List[Dict[str, Any]] = []

        # We compute for each sector across all districts to obtain relative percentiles
        for sector in self.SECTORS:
            demand_per_10k_by_dist: Dict[str, Optional[float]] = {}
            infra_ratio_by_dist: Dict[str, Optional[float]] = {}

            for d in districts:
                did = str(d["id"])
                pop = demographics.get(did, {}).get("population")

                # Filter requests for this sector
                all_dist_reqs = citizen_requests.get(did, [])
                if sector == "Overall":
                    sec_reqs = all_dist_reqs
                else:
                    sec_reqs = [r for r in all_dist_reqs if (r.get("category") or "").lower() == sector.lower()]

                req_count = len(sec_reqs)
                if pop and pop > 0:
                    demand_per_10k_by_dist[did] = (req_count / float(pop)) * 10000.0
                else:
                    demand_per_10k_by_dist[did] = None

                # Compute infra availability ratio for this sector
                dist_facs = infrastructure.get(did, [])
                if sector.lower() == "healthcare":
                    tot_beds = sum(
                        int((f.get("capacity_value") or {}).get("bed_count") or (f.get("capacity_value") or {}).get("beds") or 0)
                        for f in dist_facs
                    )
                    if pop and pop > 0:
                        infra_ratio_by_dist[did] = (tot_beds / float(pop)) * 10000.0
                    else:
                        infra_ratio_by_dist[did] = None
                else:
                    # Generic facility count per capita
                    sec_facs = [f for f in dist_facs if (f.get("category") or "").lower() == sector.lower()]
                    if pop and pop > 0:
                        infra_ratio_by_dist[did] = (len(sec_facs) / float(pop)) * 10000.0
                    else:
                        infra_ratio_by_dist[did] = float(len(sec_facs)) if sec_facs else None

            # Calculate relative percentiles across districts
            demand_pcts, _ = calculate_percentile_rank(demand_per_10k_by_dist, higher_is_better=True)
            infra_pcts, _ = calculate_percentile_rank(infra_ratio_by_dist, higher_is_better=True)

            # Assemble record for each district
            for d in districts:
                did = str(d["id"])
                dname = d["name"]
                state = d["state"]

                dist_demo = demographics.get(did)
                dist_facs = [f for f in infrastructure.get(did, []) if sector == "Overall" or (f.get("category") or "").lower() == sector.lower()]
                dist_inds = health_indicators.get(did, [])
                dist_invs = investments.get(did, [])
                all_dist_reqs = citizen_requests.get(did, [])
                if sector == "Overall":
                    sec_reqs = all_dist_reqs
                    sec_clusters = [c for c in all_clusters if str(c.get("district_id")) == did]
                else:
                    sec_reqs = [r for r in all_dist_reqs if (r.get("category") or "").lower() == sector.lower()]
                    sec_clusters = clusters_by_dist_cat.get((did, sector.lower()), [])

                record = DistrictIntelligenceAssembler.assemble_sector_intelligence(
                    district_id=did,
                    district_name=dname,
                    state=state,
                    sector=sector,
                    demographics=dist_demo,
                    facilities=dist_facs,
                    indicators=dist_inds,
                    investments=dist_invs,
                    requests=sec_reqs,
                    clusters=sec_clusters,
                    demand_percentile=demand_pcts.get(did),
                    infrastructure_percentile=infra_pcts.get(did)
                )
                all_generated_records.append(record)

        # Persist generated records
        save_district_intelligence_records(all_generated_records)

        # Summary of generated signals
        gap_count = sum(1 for r in all_generated_records if r.get("mismatch_signal") == "potential_gap")
        pressure_count = sum(1 for r in all_generated_records if r.get("mismatch_signal") == "infrastructure_pressure")

        return {
            "success": True,
            "districts_processed": len(districts),
            "sectors_per_district": len(self.SECTORS),
            "total_records_generated": len(all_generated_records),
            "potential_gaps_identified": gap_count,
            "infrastructure_pressure_signals": pressure_count
        }

    def get_district_intelligence(
        self,
        district_id: str,
        sector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves intelligence records for a specific district."""
        records = fetch_district_intelligence(district_id, sector=sector)
        if not records:
            # Lazy initialize if empty
            self.refresh_all_intelligence()
            records = fetch_district_intelligence(district_id, sector=sector)
        return records

    def list_district_intelligence(
        self,
        sector: Optional[str] = None,
        state: Optional[str] = None,
        mismatch_signal: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Lists district intelligence records with optional filters."""
        records = list_district_intelligence_records(
            sector=sector,
            mismatch_signal=mismatch_signal,
            limit=limit
        )
        if not records:
            self.refresh_all_intelligence()
            records = list_district_intelligence_records(
                sector=sector,
                mismatch_signal=mismatch_signal,
                limit=limit
            )

        if state:
            records = [r for r in records if (r.get("state") or "").lower() == state.lower()]
        return records

    def get_gap_signals(
        self,
        sector: Optional[str] = None,
        min_severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves districts with potential infrastructure gap or pressure signals.
        """
        all_recs = self.list_district_intelligence(sector=sector)
        flagged = []
        for r in all_recs:
            sig = r.get("gap_signal") or {}
            sig_type = sig.get("signal_type")
            sev = sig.get("severity")

            if sig_type in ("potential_gap", "infrastructure_pressure", "demand_supply_signal"):
                if min_severity and min_severity.lower() == "high" and sev != "high":
                    continue
                flagged.append({
                    "district_id": r["district_id"],
                    "district_name": r.get("district_name"),
                    "state": r.get("state"),
                    "sector": r["sector"],
                    "signal_type": sig_type,
                    "severity": sev,
                    "demand_percentile": r.get("demand_percentile"),
                    "infrastructure_percentile": r.get("infrastructure_percentile"),
                    "summary": sig.get("summary"),
                    "evidence": sig.get("evidence"),
                    "data_sources": r.get("data_sources")
                })

        return flagged


default_infrastructure_service = InfrastructureIntelligenceService()
