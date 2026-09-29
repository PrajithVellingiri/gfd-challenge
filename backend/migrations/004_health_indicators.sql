-- =============================================================================
-- Migration: 004_health_indicators.sql
-- Description: Phase 2 schema additions:
--              1. health_indicators table (NFHS-5 factsheet indicators)
--              2. citizen_requests district_id, source_type, is_synthetic columns
--              3. data_type provenance metadata columns across datasets
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. HEALTH INDICATORS TABLE (NFHS-5 District Indicators)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.health_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES public.districts(id) ON DELETE CASCADE,
    indicator_name VARCHAR(150) NOT NULL,
    indicator_value NUMERIC(10, 4) NOT NULL,
    unit VARCHAR(50) NOT NULL DEFAULT '%',
    year INTEGER NOT NULL,
    source VARCHAR(255) NOT NULL,
    source_reference TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_health_indicator_district_name_year UNIQUE (district_id, indicator_name, year)
);

CREATE INDEX IF NOT EXISTS idx_health_indicators_district_id 
    ON public.health_indicators (district_id);

CREATE INDEX IF NOT EXISTS idx_health_indicators_indicator_name 
    ON public.health_indicators (indicator_name);

CREATE INDEX IF NOT EXISTS idx_health_indicators_year 
    ON public.health_indicators (year);

-- Enable RLS on health_indicators
ALTER TABLE public.health_indicators ENABLE ROW LEVEL SECURITY;

-- Read policy: transparent public access
DROP POLICY IF EXISTS "Anyone can view health indicators" ON public.health_indicators;
CREATE POLICY "Anyone can view health indicators"
    ON public.health_indicators FOR SELECT
    TO authenticated, anon
    USING (true);

-- Write policy: admin only
DROP POLICY IF EXISTS "Admins can manage health indicators" ON public.health_indicators;
CREATE POLICY "Admins can manage health indicators"
    ON public.health_indicators FOR ALL
    TO authenticated
    USING (public.get_current_user_role() = 'admin')
    WITH CHECK (public.get_current_user_role() = 'admin');

-- -----------------------------------------------------------------------------
-- 2. EXTEND CITIZEN_REQUESTS TABLE FOR CANONICAL DISTRICT & PROVENANCE
-- -----------------------------------------------------------------------------
ALTER TABLE public.citizen_requests 
    ADD COLUMN IF NOT EXISTS district_id UUID REFERENCES public.districts(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'web',
    ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS data_type VARCHAR(50) NOT NULL DEFAULT 'synthetic';

CREATE INDEX IF NOT EXISTS idx_citizen_requests_district_id 
    ON public.citizen_requests (district_id);

CREATE INDEX IF NOT EXISTS idx_citizen_requests_is_synthetic 
    ON public.citizen_requests (is_synthetic);

-- -----------------------------------------------------------------------------
-- 3. PROVENANCE DATA_TYPE COLUMNS ON EXISTING TABLES
-- -----------------------------------------------------------------------------
ALTER TABLE public.demographics 
    ADD COLUMN IF NOT EXISTS data_type VARCHAR(50) NOT NULL DEFAULT 'official';

ALTER TABLE public.infrastructure 
    ADD COLUMN IF NOT EXISTS data_type VARCHAR(50) NOT NULL DEFAULT 'official';

ALTER TABLE public.investments 
    ADD COLUMN IF NOT EXISTS data_type VARCHAR(50) NOT NULL DEFAULT 'synthetic';
