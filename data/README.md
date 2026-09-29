# GFD Challenge — Dataset Pipeline (Phase 2)

This directory contains the complete ingestion, normalization, validation, and database-loading pipeline for Phase 2 of the GFD Challenge DPI & Governance Platform.

---

## 1. Directory Structure

```
data/
├── raw/                      # Raw incoming source files (GeoJSON, JSON)
│   ├── districts_gis_raw.geojson
│   ├── census_2011_raw.json
│   ├── healthcare_facilities_raw.json
│   └── nfhs5_indicators_raw.json
├── processed/                # Normalized, schema-validated JSON datasets
│   ├── districts_normalized.json
│   ├── demographics_normalized.json
│   ├── infrastructure_normalized.json
│   ├── health_indicators_normalized.json
│   ├── investments_normalized.json
│   └── citizen_requests_normalized.json
├── scripts/                  # Standalone, reproducible pipeline scripts
│   ├── district_normalizer.py          # Canonical district resolver & UUID generator
│   ├── prepare_districts_gis.py        # EPSG:4326 GeoJSON polygons and centroids
│   ├── prepare_demographics.py         # Census of India 2011 demographics
│   ├── prepare_infrastructure.py       # HMIS / MoHFW healthcare facilities
│   ├── prepare_health_indicators.py    # NFHS-5 factsheet indicators
│   ├── prepare_investments.py          # Synthetic investment allocations
│   ├── generate_citizen_requests.py    # 8,000 synthetic citizen requests with hotspots
│   ├── profile_datasets.py             # Data quality checks & profiling report
│   └── load_all_to_database.py         # Master batch loader for Supabase/PostGIS
├── schemas/                  # Pydantic data contract schemas
│   ├── __init__.py
│   └── dataset_schemas.py
├── DATA_SOURCES.md           # Formal data provenance and registry
└── README.md                 # Pipeline documentation
```

---

## 2. Ingested Datasets

| Dataset | Primary Source | Scope | Records | Classification | Target Table |
|---|---|---|---|---|---|
| **Districts GIS** | Survey of India / DataMeet GIS | 44 Canonical Districts | 44 | `public` | `districts` |
| **Demographics** | Census of India 2011 (ORGI) | Total, Rural, Urban, Literacy | 44 | `official` | `demographics` |
| **Healthcare Infrastructure** | HMIS / MoHFW | DH, SDH, CHC Facilities & Beds | 56 | `official` | `infrastructure` |
| **Health Indicators** | NFHS-5 Factsheets (IIPS / MoHFW) | Immunization, Stunting, etc. | 308 | `official` | `health_indicators` |
| **Investments** | Simulation Model (demo-generated) | FY21-22 to FY23-24 across 5 sectors | 660 | `synthetic` | `investments` |
| **Citizen Requests** | Synthetic Demand Engine | 7 Sectors, multilingual, hotspots | 8,000 | `synthetic` | `citizen_requests` |

For detailed metadata, licensing, and publisher information, refer to [DATA_SOURCES.md](file:///d:/College/Projects/GFD%20Challenge/data/DATA_SOURCES.md).

---

## 3. Data Normalization & Canonical Key Layer

Different government sources use varying spelling conventions, historical names, and abbreviations (e.g. *Bangalore* vs *Bengaluru Urban*, *Gulbarga* vs *Kalaburagi*, *Madras* vs *Chennai*, *Poona* vs *Pune*).

The normalization layer ([`district_normalizer.py`](file:///d:/College/Projects/GFD%20Challenge/data/scripts/district_normalizer.py)):
1. Strips punctuation, whitespace, and suffix noise.
2. Resolves aliases to canonical `(District Name, State, Country)` tuples.
3. Computes a deterministic `UUID5` via a fixed project namespace.
4. Ensures all relational records reference the canonical `districts.id` foreign key.

---

## 4. Synthetic Data & Demand Hotspots

- **Investments**: Clearly tagged with `data_type = 'synthetic'` and `source = 'demo-generated'` to maintain full transparency.
- **Citizen Requests**: 8,000 records tagged with `is_synthetic = true` and `data_type = 'synthetic'`.
- **Hotspot Design**:
  - **Bahraich, Purnia, Gadchiroli, Kalahandi**: Severe healthcare infrastructure gaps (low beds/immunization) coupled with 4.0x–4.5x higher healthcare grievance volume.
  - **Jaisalmer, Jodhpur, Gaya, Kalaburagi**: Water stress and drought vulnerabilities coupled with 4.0x–5.0x higher water supply grievances.
  - **Wayanad, Darjeeling, Coimbatore, Pune**: Hilly terrain and rapid commuting bottlenecks generating elevated road and transport complaints.
  - **Balaghat, Cachar, Muzaffarpur**: High education and digital infrastructure grievances.

---

## 5. Reproducing the Pipeline

To regenerate all datasets from scratch and validate:

```bash
# 1. Run all preparation scripts in order
python data/scripts/prepare_districts_gis.py
python data/scripts/prepare_demographics.py
python data/scripts/prepare_infrastructure.py
python data/scripts/prepare_health_indicators.py
python data/scripts/prepare_investments.py
python data/scripts/generate_citizen_requests.py

# 2. Run data quality validation & profiling report
python data/scripts/profile_datasets.py

# 3. Dry-run database ingestion
python data/scripts/load_all_to_database.py --dry-run

# 4. Ingest into live Supabase / PostgreSQL (requires DATABASE_URL in .env)
python data/scripts/load_all_to_database.py
```

---

## 6. Known Limitations
- Census figures reflect the 2011 Census (the most recent complete official census available in India).
- HMIS facility listings focus on secondary/tertiary facilities (DH, SDH, CHC) rather than all sub-health centres.
- Investment spending is synthetically generated for demonstration because consolidated district-level capital expenditure data is not publicly published in an open, standardized API.
