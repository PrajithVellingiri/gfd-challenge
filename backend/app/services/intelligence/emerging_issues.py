"""
Emerging Issue Detection Service (Phase 5).
Detects accelerating citizen grievances and sudden surge patterns across temporal observation windows.
Transparently reports growth percentages and labels all signals as data-derived indicators.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from collections import defaultdict


def parse_timestamp(ts: Any) -> Optional[datetime]:
    """Parses ISO timestamp string or datetime object into UTC datetime."""
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        # Support standard ISO format
        clean_str = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


class EmergingIssueDetector:
    """
    Identifies surging civic demands by comparing request frequencies across
    consecutive time windows (e.g. current 7 days vs previous 7 days).
    """

    def __init__(self, window_days: int = 7, min_current_threshold: int = 3):
        self.window_days = window_days
        self.min_current_threshold = min_current_threshold

    def detect_emerging_issues(
        self,
        requests: List[Dict[str, Any]],
        reference_time: Optional[datetime] = None,
        district_id_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scans requests and flags groups with substantial period-over-period growth or sudden onset.
        """
        if not requests:
            return []

        # Filter by district/category if requested
        filtered_reqs = []
        parsed_dates = []

        for r in requests:
            d_id = str(r.get("district_id")) if r.get("district_id") else None
            cat = str(r.get("category") or "Other").strip().capitalize()

            if district_id_filter and str(district_id_filter) != str(d_id):
                continue
            if category_filter and category_filter.lower() != cat.lower():
                continue

            dt = parse_timestamp(r.get("created_at"))
            if dt:
                filtered_reqs.append((r, dt, d_id, cat))
                parsed_dates.append(dt)

        if not filtered_reqs:
            return []

        # Determine reference time T0 (latest record timestamp or provided)
        t_current_end = reference_time or max(parsed_dates)
        t_current_start = t_current_end - timedelta(days=self.window_days)
        t_prev_start = t_current_start - timedelta(days=self.window_days)

        # Count current vs previous by (district_id, category, sub_category)
        groups = defaultdict(lambda: {"current": 0, "previous": 0, "sample_summaries": []})

        for req, dt, d_id, cat in filtered_reqs:
            sub_cat = req.get("sub_category") or "General"
            key = (d_id, cat, sub_cat)

            if t_current_start <= dt <= t_current_end:
                groups[key]["current"] += 1
                if req.get("summary") and len(groups[key]["sample_summaries"]) < 3:
                    groups[key]["sample_summaries"].append(req["summary"])
            elif t_prev_start <= dt < t_current_start:
                groups[key]["previous"] += 1

        emerging_issues = []

        for (d_id, cat, sub_cat), counts in groups.items():
            curr = counts["current"]
            prev = counts["previous"]

            # Only evaluate issues meeting minimum current threshold
            if curr < self.min_current_threshold:
                continue

            growth_pct: Optional[float] = None
            if prev == 0:
                growth_pct = None  # None instead of inventing 100% or infinity
                indicator = "new"
                title = f"New surge in {sub_cat} ({cat})"
            else:
                growth_pct = round(((curr - prev) / prev) * 100.0, 1)
                if growth_pct >= 25.0:
                    indicator = "increasing"
                    title = f"Increasing {sub_cat} requests (+{growth_pct:.0f}%)"
                elif growth_pct <= -25.0:
                    indicator = "decreasing"
                    title = f"Decreasing {sub_cat} requests ({growth_pct:.0f}%)"
                else:
                    indicator = "stable"
                    title = f"Stable demand for {sub_cat}"

            # Only flag issues that are new or increasing as emerging issues
            if indicator in ("new", "increasing"):
                issue_id = str(uuid4())
                summary_text = f"{curr} requests in current {self.window_days}-day window vs {prev} in previous window."
                if counts["sample_summaries"]:
                    summary_text += f" Sample: {counts['sample_summaries'][0]}"

                emerging_issues.append({
                    "id": issue_id,
                    "title": title,
                    "description": summary_text,
                    "category": cat,
                    "sub_category": sub_cat,
                    "district_id": d_id,
                    "current_count": curr,
                    "previous_count": prev,
                    "growth_percentage": growth_pct,
                    "indicator": indicator,
                    "signal_type": "AI/data-derived signal (advisory governance triage)"
                })

        # Sort by current count and growth
        emerging_issues.sort(
            key=lambda x: (x["current_count"], x["growth_percentage"] or 9999.0),
            reverse=True
        )
        return emerging_issues
