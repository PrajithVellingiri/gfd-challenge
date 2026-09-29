# Phase 6 — Infrastructure Intelligence & Gap Detection

## 1. Overview & Objective

While Phase 5 established collective citizen demand intelligence (embeddings, duplicates, clusters, emerging issues), **Phase 6 (Infrastructure Intelligence & Gap Detection)** connects citizen demand with public infrastructure availability and demographic baselines across India's districts.

Phase 6 produces:
1. **Per-Capita Infrastructure Indicators**: Normalizing healthcare facilities, hospital beds, and doctors by Census population baselines.
2. **Citizen Demand Normalization**: 7-day growth trends, request volume per 10,000 population, and cluster concentrations.
3. **Relative Cross-District Percentiles**: Standardized comparative rankings (0th to 100th percentile) across all 44 canonical districts rather than arbitrary absolute cutoffs.
4. **Explainable Gap & Pressure Signals**: Transparent, rule-based indicators identifying potential shortages, infrastructure pressure, or unserved areas without opaque scoring.
5. **Strict Data Provenance**: Every record clearly delineates official baselines (Census 2011, HMIS, NFHS-5) and synthetic hackathon datasets with timestamps, citations, and limitation notes.

```
       Citizen Demand (Phase 3-5)          Public Infrastructure & Demographics (Phase 1-2)
  (Total requests, 7d growth, per 10k)       (Census 2011, HMIS facilities, NFHS-5, Investments)
                   \                                        /
                    \                                      /
                     ▼                                    ▼
                 Relative Cross-District Percentile Ranking (0 - 100%)
                                          ↓
               Explainable Decision-Support Indicators & Gap Signals
               - potential_gap (High Demand + Low Infrastructure)
               - infrastructure_pressure (High Demand + Moderate Infrastructure)
               - demand_supply_signal (Concentrated Grievance Clusters)
               - balanced (Demand and Infrastructure in Alignment)
               - insufficient_data (Sample size or public records missing)
```

---

## 2. Strict Phase Boundaries

In strict adherence to the contest roadmap:
- **Included in Phase 6**:
  - District-level aggregation of demand and infrastructure supply.
  - Population-normalized rates (zero-divisor safe).
  - Relative percentile benchmarks across districts.
  - Multi-dataset provenance tracking with synthetic flags.
  - Decision-support gap signals with structured evidence (`what_was_observed`, `infrastructure_observed`, `why_signal_generated`).
  - Reusable frontend metric cards and explainable badges.
- **Explicitly Deferred to Phase 7**:
  - Final priority score calculation (composite single-score ranking).
  - Machine learning priority models.
  - Concrete project recommendations (e.g. "Build a 50-bed PHC in Taluk X").
  - Policymaker dashboards and GIS choropleth map layers.
  - What-if investment simulations and demand forecasting.

---

## 3. Database Schema (Migration 007)

Migration `007_infrastructure_intelligence.sql` introduces:

### `public.district_intelligence`
| Column | Type | Description |
|---|---|---|
| `id` | `UUID PRIMARY KEY` | Unique record identifier |
| `district_id` | `UUID REFERENCES public.districts(id)` | Foreign key to canonical district |
| `sector` | `VARCHAR(100)` | Sector (`Overall`, `Healthcare`, `Water`, `Education`, `Roads`) |
| `population` | `BIGINT` | Census 2011 population baseline |
| `population_source` | `VARCHAR(255)` | Source reference note |
| `total_requests` | `INT` | Total citizen requests recorded in sector |
| `requests_last_7_days` | `INT` | Recent 7-day request volume |
| `requests_previous_7_days` | `INT` | Prior 7-day request volume |
| `request_growth_percentage` | `NUMERIC(8,2)` | Period-over-period percentage change |
| `requests_per_10000` | `NUMERIC(10,4)` | Normalized citizen demand per 10,000 residents |
| `demand_percentile` | `NUMERIC(5,2)` | Relative cross-district demand rank (0-100) |
| `infrastructure_percentile` | `NUMERIC(5,2)` | Relative cross-district infrastructure supply rank (0-100) |
| `demand_metrics` | `JSONB` | Granular demand metrics & sector breakdown |
| `infrastructure_metrics` | `JSONB` | Facilities, beds, doctors, or coverage indicators |
| `health_metrics` | `JSONB` | NFHS-5 factsheet indicators |
| `investment_metrics` | `JSONB` | Outlay allocation & project counts |
| `cluster_metrics` | `JSONB` | Phase 5 cluster concentration metrics |
| `mismatch_signal` | `VARCHAR(100)` | Primary signal key (`potential_gap`, `balanced`, etc.) |
| `gap_signal` | `JSONB` | Structured rationale and evidence payload |
| `data_sources` | `JSONB` | Provenance records with synthetic flags |
| `computed_at` | `TIMESTAMPTZ` | Timestamp when intelligence was generated |

---

## 4. Key Calculation Rules & Formulas

### 4.1 Population Normalization
$$\text{Per-Capita Ratio} = \left(\frac{\text{Metric Value}}{\text{Population}}\right) \times \text{Multiplier}$$
- Handled safely: If $\text{Population} \le 0$ or is `None`, returns `None` (no division by zero).

### 4.2 Cross-District Percentile Ranking
$$\text{Percentile}(x) = \left(\frac{|\{y \in V : y \le x\}|}{|V|}\right) \times 100$$
- If $|V| < 3$, `benchmark_available` is flagged as `False` to prevent misleading rankings on tiny samples.

### 4.3 Explainable Gap Signal Logic
- **`potential_gap`**: $\text{Demand Percentile} \ge 60$ and $\text{Infrastructure Percentile} \le 40$. Severity is `high` if demand $\ge 80$ and infrastructure $\le 25$.
- **`infrastructure_pressure`**: $\text{Demand Percentile} \ge 75$ and $\text{Infrastructure Percentile} \le 65$.
- **`demand_supply_signal`**: Top grievance cluster accounts for $\ge 50\%$ of requests in the district sector.
- **`adequate_coverage`**: $\text{Demand Percentile} \le 30$ and $\text{Infrastructure Percentile} \ge 70$.
- **`balanced`**: Demand and infrastructure are within typical comparable ranges.
- **`insufficient_data`**: Missing population or supply datasets.

---

## 5. Provenance & Transparency Standards

Every record in `public.district_intelligence` tracks explicit provenance:
- **Census 2011 Demographics**: Marked as official (`is_synthetic: false`), with explicit notation that it represents a historical decennial baseline, not 2026 projected population.
- **HMIS Healthcare Facilities**: Marked as official (`is_synthetic: false`), source MoHFW GoI.
- **NFHS-5 Factsheets**: Marked as official (`is_synthetic: false`), source IIPS Mumbai & MoHFW.
- **Public Investments**: Marked as synthetic (`is_synthetic: true`), source GFD Synthetic Investment Engine.
- **Citizen Grievance Demand**: Marked as hybrid/synthetic (`is_synthetic: true`), source GFD Citizen Submission Engine.

---

## 6. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/infrastructure/districts` | List district intelligence records with sector and signal filters |
| `GET` | `/api/infrastructure/districts/{district_id}` | Retrieve complete multi-sector intelligence for a district |
| `GET` | `/api/infrastructure/districts/{district_id}/sectors` | Summary of analyzed sectors for a district |
| `GET` | `/api/infrastructure/gap-signals` | List all detected potential gap and infrastructure pressure signals |
| `POST` | `/api/infrastructure/refresh` | Recompute intelligence benchmarks across all 44 districts |

---

## 7. Privacy & Anti-Leakage Guarantees

All infrastructure intelligence endpoints output aggregated statistical data at the district or taluk level.
- No citizen identifiers (`citizen_name`, `email`, `phone_number`, `user_id`) are ever returned in infrastructure responses.
- Raw citizen complaint text with potential PII is excluded; only cluster labels and category counts are incorporated.
