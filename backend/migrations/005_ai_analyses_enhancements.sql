-- =============================================================================
-- Migration: 005_ai_analyses_enhancements.sql
-- Description: Phase 4 schema enhancements for ai_analyses:
--              prompt_version, sub_category, category, urgency, summary, keywords,
--              transcript, image_analysis, processing_status, and error_message.
-- =============================================================================

ALTER TABLE public.ai_analyses
    ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(50) DEFAULT 'v1.0',
    ADD COLUMN IF NOT EXISTS category VARCHAR(100),
    ADD COLUMN IF NOT EXISTS sub_category VARCHAR(150),
    ADD COLUMN IF NOT EXISTS urgency VARCHAR(50),
    ADD COLUMN IF NOT EXISTS summary TEXT,
    ADD COLUMN IF NOT EXISTS keywords JSONB DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS transcript TEXT,
    ADD COLUMN IF NOT EXISTS image_analysis JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    ADD COLUMN IF NOT EXISTS error_message TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now());

-- Index for processing lifecycle lookups
CREATE INDEX IF NOT EXISTS idx_ai_analyses_processing_status
    ON public.ai_analyses (processing_status);

CREATE INDEX IF NOT EXISTS idx_ai_analyses_category
    ON public.ai_analyses (category);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS trigger_ai_analyses_updated_at ON public.ai_analyses;
CREATE TRIGGER trigger_ai_analyses_updated_at
    BEFORE UPDATE ON public.ai_analyses
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
