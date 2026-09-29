-- =============================================================================
-- Migration: 002_storage_setup.sql
-- Description: Provision private Supabase Storage buckets (citizen-images, citizen-audio)
--              and configure row-level security for file uploads/downloads.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. PROVISION PRIVATE STORAGE BUCKETS
-- -----------------------------------------------------------------------------
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES 
    (
        'citizen-images', 
        'citizen-images', 
        false, 
        10485760, -- 10 MB limit
        ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
    ),
    (
        'citizen-audio', 
        'citizen-audio', 
        false, 
        26214400, -- 25 MB limit
        ARRAY['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/webm', 'audio/x-m4a']
    )
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- -----------------------------------------------------------------------------
-- 2. STORAGE RLS POLICIES ON storage.objects
-- Path convention: {user_id}/{request_id}/{filename}
-- -----------------------------------------------------------------------------

-- Drop existing storage policies if they exist to ensure idempotency
DROP POLICY IF EXISTS "Citizens can upload own files" ON storage.objects;
DROP POLICY IF EXISTS "Citizens can view own files" ON storage.objects;
DROP POLICY IF EXISTS "Citizens can update own files" ON storage.objects;
DROP POLICY IF EXISTS "Citizens can delete own files" ON storage.objects;
DROP POLICY IF EXISTS "Staff can view all citizen files" ON storage.objects;

-- Policy 1: Authenticated citizens can upload to their own user directory
CREATE POLICY "Citizens can upload own files"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id IN ('citizen-images', 'citizen-audio')
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Policy 2: Citizens can view/download their own uploaded files
CREATE POLICY "Citizens can view own files"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id IN ('citizen-images', 'citizen-audio')
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Policy 3: Citizens can update their own uploaded files
CREATE POLICY "Citizens can update own files"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING (
        bucket_id IN ('citizen-images', 'citizen-audio')
        AND (storage.foldername(name))[1] = auth.uid()::text
    )
    WITH CHECK (
        bucket_id IN ('citizen-images', 'citizen-audio')
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Policy 4: Citizens can delete their own uploaded files
CREATE POLICY "Citizens can delete own files"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (
        bucket_id IN ('citizen-images', 'citizen-audio')
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Policy 5: Policymakers and Admins can view all citizen uploads
CREATE POLICY "Staff can view all citizen files"
    ON storage.objects FOR SELECT
    TO authenticated
    USING (
        bucket_id IN ('citizen-images', 'citizen-audio')
        AND EXISTS (
            SELECT 1 FROM public.users
            WHERE users.id = auth.uid()
            AND users.role IN ('policymaker', 'admin')
        )
    );
