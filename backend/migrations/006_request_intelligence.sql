-- =============================================================================
-- Migration: 006_request_intelligence.sql
-- Description: Phase 5 schema for Request Intelligence:
--              - request_embeddings: 768-dim semantic vectors
--              - request_similarities: similarity/duplicate/related edges
--              - request_clusters & cluster_memberships: semantic clustering
--              - emerging_issues: demand growth & acceleration indicators
-- =============================================================================

-- 1. Request Embeddings
CREATE TABLE IF NOT EXISTS public.request_embeddings (
    request_id UUID PRIMARY KEY REFERENCES public.citizen_requests(id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'models/text-embedding-004',
    embedding_version VARCHAR(50) DEFAULT 'v1.0',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- Attempt vector HNSW index if pgvector is enabled
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        BEGIN
            CREATE INDEX IF NOT EXISTS idx_request_embeddings_vector
                ON public.request_embeddings USING hnsw (embedding vector_cosine_ops);
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END;
    END IF;
END $$;

-- 2. Request Similarities (Graph edges)
CREATE TABLE IF NOT EXISTS public.request_similarities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_request_id UUID NOT NULL REFERENCES public.citizen_requests(id) ON DELETE CASCADE,
    target_request_id UUID NOT NULL REFERENCES public.citizen_requests(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5,4) NOT NULL CHECK (similarity_score >= -1.0 AND similarity_score <= 1.0),
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN ('similar', 'duplicate', 'related')),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_request_similarity_pair UNIQUE (source_request_id, target_request_id),
    CONSTRAINT chk_no_self_similarity CHECK (source_request_id <> target_request_id)
);

CREATE INDEX IF NOT EXISTS idx_similarities_source ON public.request_similarities(source_request_id);
CREATE INDEX IF NOT EXISTS idx_similarities_target ON public.request_similarities(target_request_id);
CREATE INDEX IF NOT EXISTS idx_similarities_rel_type ON public.request_similarities(relationship_type);
CREATE INDEX IF NOT EXISTS idx_similarities_score ON public.request_similarities(similarity_score DESC);

-- 3. Request Clusters
CREATE TABLE IF NOT EXISTS public.request_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_label VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    district_id UUID REFERENCES public.districts(id) ON DELETE SET NULL,
    request_count INT NOT NULL DEFAULT 0,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_clusters_category ON public.request_clusters(category);
CREATE INDEX IF NOT EXISTS idx_clusters_district ON public.request_clusters(district_id);
CREATE INDEX IF NOT EXISTS idx_clusters_req_count ON public.request_clusters(request_count DESC);

-- 4. Cluster Memberships (Many-to-Many)
CREATE TABLE IF NOT EXISTS public.cluster_memberships (
    cluster_id UUID NOT NULL REFERENCES public.request_clusters(id) ON DELETE CASCADE,
    request_id UUID NOT NULL REFERENCES public.citizen_requests(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5,4),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (cluster_id, request_id)
);

CREATE INDEX IF NOT EXISTS idx_cluster_memberships_req ON public.cluster_memberships(request_id);

-- 5. Emerging Issues
CREATE TABLE IF NOT EXISTS public.emerging_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    district_id UUID REFERENCES public.districts(id) ON DELETE SET NULL,
    current_count INT NOT NULL DEFAULT 0,
    previous_count INT NOT NULL DEFAULT 0,
    growth_percentage NUMERIC(8,2),
    indicator VARCHAR(50) NOT NULL DEFAULT 'increasing' CHECK (indicator IN ('increasing', 'stable', 'decreasing', 'new')),
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_emerging_issues_category ON public.emerging_issues(category);
CREATE INDEX IF NOT EXISTS idx_emerging_issues_district ON public.emerging_issues(district_id);
CREATE INDEX IF NOT EXISTS idx_emerging_issues_indicator ON public.emerging_issues(indicator);

-- 6. Updated_at Triggers
DROP TRIGGER IF EXISTS trigger_request_clusters_updated_at ON public.request_clusters;
CREATE TRIGGER trigger_request_clusters_updated_at
    BEFORE UPDATE ON public.request_clusters
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS trigger_emerging_issues_updated_at ON public.emerging_issues;
CREATE TRIGGER trigger_emerging_issues_updated_at
    BEFORE UPDATE ON public.emerging_issues
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- 7. Row Level Security
ALTER TABLE public.request_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.request_similarities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.request_clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cluster_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.emerging_issues ENABLE ROW LEVEL SECURITY;

-- Read policies for public aggregate intelligence
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'request_clusters' AND policyname = 'Anyone can view clusters') THEN
        CREATE POLICY "Anyone can view clusters" ON public.request_clusters FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'emerging_issues' AND policyname = 'Anyone can view emerging issues') THEN
        CREATE POLICY "Anyone can view emerging issues" ON public.emerging_issues FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'cluster_memberships' AND policyname = 'Anyone can view cluster memberships') THEN
        CREATE POLICY "Anyone can view cluster memberships" ON public.cluster_memberships FOR SELECT USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'request_similarities' AND policyname = 'Anyone can view similarities') THEN
        CREATE POLICY "Anyone can view similarities" ON public.request_similarities FOR SELECT USING (true);
    END IF;
END $$;
