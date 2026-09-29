# Data Provenance Registry & Source Documentation

This registry documents all datasets ingested, normalized, or generated in **Phase 2: Dataset Pipeline** for the GFD Challenge DPI Platform.

> [!IMPORTANT]
> **Data Type Distinction Policy**:
> - **`official`**: Official government statistics and reports published by government statutory bodies (e.g., Office of the Registrar General & Census Commissioner, Ministry of Health and Family Welfare, IIPS).
> - **`public`**: Open data released under public/open-government licenses (e.g., data.gov.in, OpenStreetMap / DataMeet GIS under ODbL/CC-BY).
> - **`synthetic`**: Programmatically generated demo data designed to simulate real-world conditions for testing, ML preparation, and MVP evaluation. **Synthetic data is never presented as official government data.**

---

## 1. Registry of Datasets

### A. Demographics (Census of India 2011)
- **Dataset Name**: District-Level Primary Census Abstract (PCA) 2011
- **Description**: District-level population breakdown (total, rural, urban, sex ratio, and literacy rate) across representative Indian districts.
- **Source**: Office of the Registrar General & Census Commissioner, India (ORGI), Ministry of Home Affairs, Government of India.
- **Source URL**: [https://censusindia.gov.in/](https://censusindia.gov.in/) & [https://data.gov.in/resource/district-wise-census-2011](https://data.gov.in/)
- **Publisher**: Ministry of Home Affairs, Government of India
- **License**: Government Open Data License - India (GODL)
- **Retrieval / Publication Date**: Census 2011 Final Tables / Ingested 2026
- **Year**: 2011
- **Data Type**: `official`
- **Processing Steps**:
  1. Extracted district-level records from Census PCA tables.
  2. Normalized state and district names through the canonical normalizer.
  3. Validated `population >= 0`, `rural_population + urban_population <= population`.
  4. Structured literacy rate and sex ratio into `demographic_indicators` JSONB.
- **Target Table**: `public.demographics`

---

### B. Healthcare Infrastructure (HMIS / MoHFW)
- **Dataset Name**: National Health Facility Infrastructure Directory (HMIS / NHM)
- **Description**: Public health facilities including District Hospitals (DH), Sub-Divisional Hospitals (SDH), Community Health Centres (CHC), and Primary Health Centres (PHC) with bed capacities and facility tiers.
- **Source**: Health Management Information System (HMIS) & National Health Mission (NHM), Ministry of Health & Family Welfare (MoHFW), Government of India.
- **Source URL**: [https://hmis.mohfw.gov.in/](https://hmis.mohfw.gov.in/) & [https://data.gov.in/](https://data.gov.in/)
- **Publisher**: Ministry of Health & Family Welfare (MoHFW), Government of India
- **License**: Government Open Data License - India (GODL)
- **Retrieval Date**: MoHFW 2022-2023 Infrastructure Reports / Ingested 2026
- **Year**: 2022-2023
- **Data Type**: `official`
- **Processing Steps**:
  1. Filtered public facilities by administrative tier and district.
  2. Resolved district names to canonical `districts.id`.
  3. Normalised facility categories and bed capacities into `capacity_value` JSONB.
  4. Associated coordinates where available; preserved district-level association without fabricating coordinates.
- **Target Table**: `public.infrastructure`

---

### C. Health Indicators (NFHS-5 District Factsheets)
- **Dataset Name**: National Family Health Survey (NFHS-5) District Factsheet Indicators
- **Description**: Key district-level health and maternal/child nutrition indicators covering institutional births, full immunization, child stunting, anemia among pregnant women, improved sanitation, and health insurance.
- **Source**: International Institute for Population Sciences (IIPS) & Ministry of Health and Family Welfare (MoHFW).
- **Source URL**: [http://rchiips.org/nfhs/factsheet_NFHS-5.shtml](http://rchiips.org/nfhs/factsheet_NFHS-5.shtml)
- **Publisher**: IIPS Mumbai / MoHFW, Government of India
- **License**: Public Official Statistics (MoHFW)
- **Retrieval Date**: NFHS-5 Final Factsheets (2019-2021) / Ingested 2026
- **Year**: 2020
- **Data Type**: `official`
- **Processing Steps**:
  1. Extracted standardized percentage indicators from district factsheets.
  2. Linked each factsheet to canonical district UUIDs.
  3. Stored indicators with indicator name, value, unit (`%`), year, and metadata.
- **Target Table**: `public.health_indicators`

---

### D. District GIS Boundaries
- **Dataset Name**: India District Boundaries GeoJSON (EPSG:4326)
- **Description**: Spatial boundary polygons and centroids for administrative districts formatted in EPSG:4326 (WGS 84).
- **Source**: Survey of India / DataMeet Community Geospatial Project / Open Government Data.
- **Source URL**: [https://github.com/datameet/maps](https://github.com/datameet/maps) & [https://data.gov.in/](https://data.gov.in/)
- **Publisher**: DataMeet / Survey of India
- **License**: Open Database License (ODbL) / Creative Commons Attribution (CC-BY 4.0)
- **Retrieval Date**: Updated 2021-2023 / Ingested 2026
- **Year**: 2021
- **Data Type**: `public`
- **Processing Steps**:
  1. Validated polygon topologies using `shapely.geometry.is_valid`.
  2. Ensured CRS is strictly EPSG:4326.
  3. Computed polygon centroids (`ST_Centroid`).
  4. Linked each boundary to canonical district name, state, and country.
- **Target Table**: `public.districts`

---

### E. Government Investment Allocations
- **Dataset Name**: District Infrastructure Investment Dataset (Demonstration / Synthetic)
- **Description**: Public infrastructure budget expenditure and project allocations across healthcare, water, roads, education, and electricity.
- **Source**: Generated programmatically for system demonstration and pipeline evaluation due to the lack of an open, standardized, district-level consolidated expenditure dataset.
- **Source URL**: Internal Synthetic Generator (`data/scripts/generate_investments.py`)
- **Publisher**: GFD Challenge Synthetic Data Engine
- **License**: MIT
- **Retrieval / Generation Date**: 2026-09-29
- **Year**: FY 2021-2022, 2022-2023, 2023-2024
- **Data Type**: `synthetic`
- **Metadata Tag**: `data_type = 'synthetic'`, `source = 'demo-generated'`
- **Target Table**: `public.investments`

---

### F. Citizen Demand & Grievances Dataset
- **Dataset Name**: Citizen Demand & Public Infrastructure Grievance Dataset (Synthetic)
- **Description**: 8,000 synthetic citizen reports across 7 critical infrastructure sectors (healthcare, education, roads, water, transportation, electricity, digital infrastructure) with realistic geographic distributions, multilingual text, and distinct demand hotspots.
- **Source**: Internal Synthetic Generator (`data/scripts/generate_citizen_requests.py`)
- **Source URL**: Internal Synthetic Generator
- **Publisher**: GFD Challenge Synthetic Data Engine
- **License**: MIT
- **Retrieval / Generation Date**: 2026-09-29
- **Year**: 2025-2026
- **Data Type**: `synthetic`
- **Metadata Tag**: `data_type = 'synthetic'`, `is_synthetic = true`, `source_type = 'web|mobile_app|ivr|sms'`
- **Target Table**: `public.citizen_requests`
