-- =============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core schema for GFD Challenge 1 (PostGIS, Users, Districts,
--              Citizen Requests, Infrastructure, Demographics, Investments, AI Analyses)
-- =============================================================================

-- Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- -----------------------------------------------------------------------------
-- Helper function: automatic updated_at timestamp trigger
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 1. USERS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'citizen' 
        CHECK (role IN ('citizen', 'policymaker', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 2. DISTRICTS TABLE (Supports BRICS countries and PostGIS spatial boundaries)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    population_ref BIGINT,
    boundary GEOMETRY(MultiPolygon, 4326),
    centroid GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_district_name_state_country UNIQUE (name, state, country)
);

CREATE TRIGGER trigger_districts_updated_at
    BEFORE UPDATE ON public.districts
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 3. CITIZEN REQUESTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.citizen_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    language VARCHAR(50) NOT NULL DEFAULT 'en',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOGRAPHY(Point, 4326),
    location_name TEXT,
    urgency VARCHAR(50) NOT NULL DEFAULT 'medium'
        CHECK (urgency IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(50) NOT NULL DEFAULT 'submitted'
        CHECK (status IN ('submitted', 'under_review', 'in_progress', 'resolved', 'rejected')),
    image_path TEXT,
    audio_path TEXT,
    -- Future-proof AI processing fields (Phase 2+ nullable)
    extracted_intent TEXT,
    ai_category VARCHAR(100),
    ai_confidence DOUBLE PRECISION,
    extracted_entities JSONB DEFAULT '[]'::jsonb,
    ai_analysis JSONB DEFAULT '{}'::jsonb,
    cluster_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Trigger to automatically synchronize PostGIS location geography from lat/lon
CREATE OR REPLACE FUNCTION public.sync_citizen_request_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_citizen_requests_location
    BEFORE INSERT OR UPDATE OF latitude, longitude ON public.citizen_requests
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_citizen_request_location();

CREATE TRIGGER trigger_citizen_requests_updated_at
    BEFORE UPDATE ON public.citizen_requests
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 4. INFRASTRUCTURE TABLE (Generic for healthcare, education, roads, water, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.infrastructure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID REFERENCES public.districts(id) ON DELETE SET NULL,
    category VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    location GEOGRAPHY(Point, 4326),
    capacity_value JSONB DEFAULT '{}'::jsonb,
    source VARCHAR(255),
    source_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Trigger to automatically synchronize PostGIS location geography for infrastructure
CREATE OR REPLACE FUNCTION public.sync_infrastructure_location()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_infrastructure_location
    BEFORE INSERT OR UPDATE OF latitude, longitude ON public.infrastructure
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_infrastructure_location();

CREATE TRIGGER trigger_infrastructure_updated_at
    BEFORE UPDATE ON public.infrastructure
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 5. DEMOGRAPHICS TABLE (Extensible for Census / NFHS data)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.demographics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES public.districts(id) ON DELETE CASCADE,
    population BIGINT NOT NULL,
    rural_population BIGINT,
    urban_population BIGINT,
    demographic_indicators JSONB DEFAULT '{}'::jsonb,
    year INTEGER NOT NULL,
    source VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_demographics_district_year UNIQUE (district_id, year)
);

-- -----------------------------------------------------------------------------
-- 6. INVESTMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.investments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES public.districts(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    financial_year VARCHAR(20) NOT NULL,
    source VARCHAR(255),
    source_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TRIGGER trigger_investments_updated_at
    BEFORE UPDATE ON public.investments
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- 7. AI ANALYSES TABLE (Separate table for flexible AI analysis output)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.ai_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES public.citizen_requests(id) ON DELETE CASCADE,
    detected_language VARCHAR(50),
    translated_text TEXT,
    extracted_category VARCHAR(100),
    extracted_location TEXT,
    extracted_urgency VARCHAR(50),
    entities JSONB DEFAULT '[]'::jsonb,
    confidence DOUBLE PRECISION,
    model_name VARCHAR(100),
    analysis_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_ai_analysis_request UNIQUE (request_id)
);

-- -----------------------------------------------------------------------------
-- 8. INDEXES (Spatial GIST + B-Tree)
-- -----------------------------------------------------------------------------
-- Spatial indexes
CREATE INDEX IF NOT EXISTS idx_citizen_requests_location 
    ON public.citizen_requests USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_infrastructure_location 
    ON public.infrastructure USING GIST (location);

CREATE INDEX IF NOT EXISTS idx_districts_boundary 
    ON public.districts USING GIST (boundary);

CREATE INDEX IF NOT EXISTS idx_districts_centroid 
    ON public.districts USING GIST (centroid);

-- B-Tree indexes for efficient queries and joins
CREATE INDEX IF NOT EXISTS idx_citizen_requests_user_id 
    ON public.citizen_requests (user_id);

CREATE INDEX IF NOT EXISTS idx_citizen_requests_status 
    ON public.citizen_requests (status);

CREATE INDEX IF NOT EXISTS idx_citizen_requests_category 
    ON public.citizen_requests (category);

CREATE INDEX IF NOT EXISTS idx_citizen_requests_created_at 
    ON public.citizen_requests (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_infrastructure_district_id 
    ON public.infrastructure (district_id);

CREATE INDEX IF NOT EXISTS idx_infrastructure_category 
    ON public.infrastructure (category);

CREATE INDEX IF NOT EXISTS idx_demographics_district_id 
    ON public.demographics (district_id);

CREATE INDEX IF NOT EXISTS idx_investments_district_id 
    ON public.investments (district_id);

CREATE INDEX IF NOT EXISTS idx_ai_analyses_request_id 
    ON public.ai_analyses (request_id);
