# Phase 5 — Request Intelligence

## 1. Overview & Objective

While Phase 4 focuses on understanding individual citizen requests in isolation (text, audio, vision), **Phase 5 (Request Intelligence)** establishes the relational intelligence layer for the **GFD Challenge DPI Platform**.

Phase 5 transforms individual complaints into relational civic patterns:
```
Individual Citizen Requests
            ↓
Semantic Vector Embeddings (768-dim)
            ↓
Pairwise Cosine Similarity & Nearest Neighbors
            ↓
Duplicate / Near-Duplicate Detection (Geographically Verified)
            ↓
District-Aware Semantic Clustering (DBSCAN)
            ↓
Emerging Issue & Surge Detection (Period-over-Period Growth)
```

The objective is to reveal **what many citizens are demanding as a collective community**, without conflating geographically separate needs or violating citizen privacy.

---

## 2. Strict Phase Boundaries

In accordance with contest requirements, Phase 5 is strictly bounded to request intelligence:
- **Included in Phase 5**: Semantic embeddings, similarity search, duplicate detection, DBSCAN clustering, and emerging issue surge signals.
- **Explicitly Deferred to Later Phases**: Infrastructure gap scoring, demographic correlations, government investment analysis, ML priority scoring, project recommendations, and policymaker dashboards.

---

## 3. Architecture & Components

The intelligence layer resides under `backend/app/services/intelligence/`:

| Module | Purpose |
|---|---|
| [`embeddings.py`](file:///d:/College/Projects/GFD%20Challenge/backend/app/services/intelligence/embeddings.py) | Abstraction provider for generating 768-dim vectors via Gemini (`models/text-embedding-004`) or deterministic mock fallback. |
| [`similarity.py`](file:///d:/College/Projects/GFD%20Challenge/backend/app/services/intelligence/similarity.py) | Cosine similarity/distance math and top-K nearest-neighbor ranking. |
| [`duplicate_detector.py`](file:///d:/College/Projects/GFD%20Challenge/backend/app/services/intelligence/duplicate_detector.py) | Distinguishes true duplicates from geographically separated similar requests. |
| [`clustering.py`](file:///d:/College/Projects/GFD%20Challenge/backend/app/services/intelligence/clustering.py) | District-aware & category-aware DBSCAN clustering with deterministic label synthesis. |
| [`emerging_issues.py`](file:///d:/College/Projects/GFD%20Challenge/backend/app/services/intelligence/emerging_issues.py) | Scans temporal windows for accelerating request frequency and sudden surges. |
| [`intelligence_service.py`](file:///d:/College/Projects/GFD%20Challenge/backend/app/services/intelligence/intelligence_service.py) | Master facade orchestrating all relational operations and batch processing. |

---

## 4. Vector Storage & `pgvector` Integration

- **Extension**: `pgvector` enabled in Supabase / PostgreSQL.
- **Dimension**: 768 dimensions (aligned with `models/text-embedding-004` and `public.ai_analyses.embedding vector(768)`).
- **Index**: `HNSW` vector index using `vector_cosine_ops` on `public.request_embeddings(embedding)`.
- **Database Schema (Migration 006)**:
  - `public.request_embeddings`: 1-to-1 table linking request UUID to 768-dim vector, model name, and version.
  - `public.request_similarities`: Directed graph storing similarity scores (`NUMERIC(5,4)`), relationship types (`duplicate`, `similar`, `related`), and timestamps.
  - `public.request_clusters`: Clusters labeled by category, district, and member request count.
  - `public.cluster_memberships`: M-to-M junction table with member similarity scores.
  - `public.emerging_issues`: Trend records with current count, previous count, growth percentage, and acceleration indicator.

---

## 5. Duplicate vs. Similar Logic (Geographic Awareness)

> [!IMPORTANT]
> Semantic similarity alone does **not** make two requests duplicates. Two citizens in different villages asking for a drinking water pipeline are facing the **same type of infrastructure deficit**, but require **two distinct capital investments**.

The classification algorithm enforces:
1. **Duplicate**:
   - Cosine similarity $\ge \text{DUPLICATE\_SIMILARITY\_THRESHOLD}$ (default: `0.90`) **AND**
   - Verified co-location (same `district_id`, or GPS coordinates within $15\text{ km}$, or identical location name).
2. **Similar**:
   - Cosine similarity $\ge \text{SIMILARITY\_THRESHOLD}$ (default: `0.75`), **OR**
   - Cosine similarity $\ge 0.90$ but geographically separated in different administrative districts.
3. **Related**:
   - Cosine similarity between $0.60$ and $0.75$ within related civic sectors.

---

## 6. District-Aware Semantic Clustering

To prevent unrealistic cross-district merging:
1. Citizen requests are partitioned by `(district_id, category)` pairs.
2. For each partition with at least `min_samples` (default: `2`), a pairwise cosine distance matrix is constructed ($d = 1 - \text{sim}$).
3. `sklearn.cluster.DBSCAN(eps=0.35, min_samples=2, metric='precomputed')` identifies dense clusters.
4. **Deterministic Label Synthesis**:
   - The cluster label is synthesized from the most frequent `sub_category` (e.g., *"Hospital Access"*, *"Pothole Repair"*, *"Drinking Water Contamination"*).
   - If sub-category is absent, top keywords are used (e.g., *"Healthcare: Oxygen & Clinic"*).
   - No additional LLM calls are wasted simply to name clusters.

---

## 7. Emerging Issue & Surge Detection

Emerging issue detection scans request arrival timestamps:
- **Current Observation Window**: $[T_0 - W, T_0]$ (default: $W = 7\text{ days}$).
- **Previous Observation Window**: $[T_0 - 2W, T_0 - W]$.
- **Metrics**:
  - `current_count`: Count in current window.
  - `previous_count`: Count in previous window.
  - `growth_percentage`:
    $$\text{growth} = \frac{\text{current} - \text{previous}}{\text{previous}} \times 100\%$$
    *(If `previous_count == 0`, `growth_percentage = None` to avoid inventing fake infinite values).*
  - `indicator`:
    - `new`: `previous == 0` and `current >= min_threshold` (sudden onset).
    - `increasing`: $\text{growth} \ge +25\%$.
    - `stable`: $-25\% \le \text{growth} < +25\%$.
    - `decreasing`: $\text{growth} < -25\%$.

> [!NOTE]
> All emerging issue outputs are explicitly labeled: `"AI/data-derived signal (advisory governance triage)"`. They are never represented as official government findings.

---

## 8. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/requests/{id}/similar` | Returns anonymized list of similar requests with similarity scores and explanations. |
| `GET` | `/api/requests/{id}/duplicates` | Returns verified duplicate/near-duplicate groups for a request. |
| `POST` | `/api/requests/{id}/intelligence` | Generates embedding and triggers similarity search for a specific request. |
| `GET` | `/api/intelligence/clusters` | Lists semantic clusters (filterable by `district_id`, `category`). |
| `GET` | `/api/intelligence/clusters/{id}` | Retrieves details for a specific cluster. |
| `GET` | `/api/intelligence/emerging-issues` | Lists surging civic demand signals (filterable by `window_days`, `district_id`). |
| `POST` | `/api/intelligence/process-pending` | Batch processes pending requests for embeddings, similarity, and clustering. |

---

## 9. Privacy & Security Model

- **No Personal Data Leakage**: The `/similar` and `/duplicates` endpoints return strictly anonymized records (`request_id`, `similarity_score`, `category`, `sub_category`, `district_id`, `relationship_type`, `explanation`). Citizen names, emails, phone numbers, and full complaint texts from other citizens are **never** returned.
- **Ownership Authorization**: Citizens may query similar requests or duplicate groups only for requests they own.

---

## 10. Configuration & Thresholds

Configured in `backend/app/config.py` and `.env`:

```env
EMBEDDING_PROVIDER=gemini                  # 'gemini', 'local', or 'mock'
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_DIMENSION=768
DUPLICATE_SIMILARITY_THRESHOLD=0.90        # Configurable starting point
SIMILARITY_THRESHOLD=0.75                  # Minimum threshold for similar edge
TOP_K_SIMILAR_REQUESTS=10                  # Max nearest neighbors to retrieve
CLUSTER_EPS=0.35                           # DBSCAN cosine distance threshold
CLUSTER_MIN_SAMPLES=2                      # Minimum cluster size
```

---

## 11. Known Limitations

1. **Temporal Clustering**: Standard DBSCAN groups requests based on static semantic similarity; temporal decay weighting can be introduced in future iterations.
2. **Rural Locality Names**: If GPS coordinates are not provided by the citizen, co-location relies on district boundaries or user-entered landmark names.
