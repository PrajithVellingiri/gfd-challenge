-- =============================================================================
-- Migration: 007_infrastructure_intelligence.sql
-- Description: Phase 6 schema for Infrastructure Intelligence & Gap Detection:
--              - district_intelligence table storing combined citizen demand,
--                infrastructure availability, relative benchmarks, and gap signals.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.district_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES public.districts(id) ON DELETE CASCADE,
    sector VARCHAR(100) NOT NULL,
    population BIGINT,
    population_source VARCHAR(255) DEFAULT 'Census of India 2011',
    total_requests INT NOT NULL DEFAULT 0,
    requests_last_7_days INT NOT NULL DEFAULT 0,
    requests_previous_7_days INT NOT NULL DEFAULT 0,
    request_growth_percentage NUMERIC(8, 2),
    requests_per_10000 NUMERIC(10, 4),
    demand_percentile NUMERIC(5, 2),
    infrastructure_percentile NUMERIC(5, 2),
    demand_metrics JSONB DEFAULT '{}'::jsonb,
    infrastructure_metrics JSONB DEFAULT '{}'::jsonb,
    health_metrics JSONB DEFAULT '{}'::jsonb,
    investment_metrics JSONB DEFAULT '{}'::jsonb,
    cluster_metrics JSONB DEFAULT '{}'::jsonb,
    mismatch_signal VARCHAR(100) DEFAULT 'balanced',
    gap_signal JSONB DEFAULT '{}'::jsonb,
    data_sources JSONB DEFAULT '[]'::jsonb,
    computed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_district_intelligence_district_sector UNIQUE (district_id, sector)
);

CREATE INDEX IF NOT EXISTS idx_district_intel_district_id 
    ON public.district_intelligence (district_id);

CREATE INDEX IF NOT EXISTS idx_district_intel_sector 
    ON public.district_intelligence (sector);

CREATE INDEX IF NOT EXISTS idx_district_intel_mismatch_signal 
    ON public.district_intelligence (mismatch_signal);

CREATE INDEX IF NOT EXISTS idx_district_intel_demand_pct 
    ON public.district_intelligence (demand_percentile);

CREATE INDEX IF NOT EXISTS idx_district_intel_infra_pct 
    ON public.district_intelligence (infrastructure_percentile);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_district_intelligence_updated_at ON public.district_intelligence;
CREATE TRIGGER trigger_district_intelligence_updated_at
    BEFORE UPDATE ON public.district_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- Row Level Security
ALTER TABLE public.district_intelligence ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'district_intelligence' AND policyname = 'Anyone can view district intelligence') THEN
        CREATE POLICY "Anyone can view district intelligence" 
            ON public.district_intelligence FOR SELECT 
            TO authenticated, anon
            USING (true);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'district_intelligence' AND policyname = 'Admins can manage district intelligence') THEN
        CREATE POLICY "Admins can manage district intelligence" 
            ON public.district_intelligence FOR ALL 
            TO authenticated
            USING (public.get_current_user_role() = 'admin')
            WITH CHECK (public.get_current_user_role() = 'admin');
    END IF;
END $$;
