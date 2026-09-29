-- =============================================================================
-- Migration: 003_rls_policies.sql
-- Description: Row Level Security (RLS) policies and Role-Based Access Control (RBAC)
--              for all core tables: users, citizen_requests, districts, infrastructure,
--              demographics, investments, and ai_analyses.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. HELPER FUNCTIONS & AUTH TRIGGER
-- -----------------------------------------------------------------------------

-- Helper function to fetch the role of the currently authenticated user
CREATE OR REPLACE FUNCTION public.get_current_user_role()
RETURNS text AS $$
DECLARE
    user_role text;
BEGIN
    SELECT role INTO user_role
    FROM public.users
    WHERE id = auth.uid();
    
    RETURN COALESCE(user_role, 'citizen');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Trigger function to automatically create a public.users row when a new user signs up via Supabase Auth
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    default_role text;
    user_name text;
BEGIN
    default_role := COALESCE(NEW.raw_user_meta_data->>'role', 'citizen');
    user_name := COALESCE(NEW.raw_user_meta_data->>'name', NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1));

    -- Validate role
    IF default_role NOT IN ('citizen', 'policymaker', 'admin') THEN
        default_role := 'citizen';
    END IF;

    INSERT INTO public.users (id, email, name, role)
    VALUES (NEW.id, NEW.email, user_name, default_role)
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        name = COALESCE(EXCLUDED.name, public.users.name);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to invoke handle_new_user on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- -----------------------------------------------------------------------------
-- 2. ENABLE ROW LEVEL SECURITY ON ALL TABLES
-- -----------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.citizen_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.districts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.infrastructure ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.demographics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_analyses ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 3. POLICIES: USERS TABLE
-- -----------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own profile or staff can view all" ON public.users;
CREATE POLICY "Users can view their own profile or staff can view all"
    ON public.users FOR SELECT
    TO authenticated
    USING (
        id = auth.uid() 
        OR public.get_current_user_role() IN ('policymaker', 'admin')
    );

DROP POLICY IF EXISTS "Users can update their own profile" ON public.users;
CREATE POLICY "Users can update their own profile"
    ON public.users FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (
        id = auth.uid()
        -- Prevent non-admins from changing their role
        AND (
            role = (SELECT role FROM public.users WHERE id = auth.uid())
            OR public.get_current_user_role() = 'admin'
        )
    );

DROP POLICY IF EXISTS "Admins can manage all users" ON public.users;
CREATE POLICY "Admins can manage all users"
    ON public.users FOR ALL
    TO authenticated
    USING (public.get_current_user_role() = 'admin')
    WITH CHECK (public.get_current_user_role() = 'admin');

-- -----------------------------------------------------------------------------
-- 4. POLICIES: CITIZEN REQUESTS TABLE
-- -----------------------------------------------------------------------------
DROP POLICY IF EXISTS "Citizens can view their own requests, staff can view all" ON public.citizen_requests;
CREATE POLICY "Citizens can view their own requests, staff can view all"
    ON public.citizen_requests FOR SELECT
    TO authenticated
    USING (
        user_id = auth.uid() 
        OR public.get_current_user_role() IN ('policymaker', 'admin')
    );

DROP POLICY IF EXISTS "Citizens can create their own requests" ON public.citizen_requests;
CREATE POLICY "Citizens can create their own requests"
    ON public.citizen_requests FOR INSERT
    TO authenticated
    WITH CHECK (
        user_id = auth.uid()
    );

DROP POLICY IF EXISTS "Citizens can update their own pending requests" ON public.citizen_requests;
CREATE POLICY "Citizens can update their own pending requests"
    ON public.citizen_requests FOR UPDATE
    TO authenticated
    USING (
        (user_id = auth.uid() AND status = 'submitted')
        OR public.get_current_user_role() IN ('policymaker', 'admin')
    )
    WITH CHECK (
        (user_id = auth.uid() AND status = 'submitted')
        OR public.get_current_user_role() IN ('policymaker', 'admin')
    );

DROP POLICY IF EXISTS "Citizens can delete their own submitted requests or admin can delete" ON public.citizen_requests;
CREATE POLICY "Citizens can delete their own submitted requests or admin can delete"
    ON public.citizen_requests FOR DELETE
    TO authenticated
    USING (
        (user_id = auth.uid() AND status = 'submitted')
        OR public.get_current_user_role() = 'admin'
    );

-- -----------------------------------------------------------------------------
-- 5. POLICIES: REFERENCE & PUBLIC DATASETS (districts, infrastructure, demographics, investments)
-- Read-only for citizens and public; Write restricted strictly to admins
-- -----------------------------------------------------------------------------

-- DISTRICTS
DROP POLICY IF EXISTS "Anyone can view districts" ON public.districts;
CREATE POLICY "Anyone can view districts"
    ON public.districts FOR SELECT
    TO authenticated, anon
    USING (true);

DROP POLICY IF EXISTS "Admins can manage districts" ON public.districts;
CREATE POLICY "Admins can manage districts"
    ON public.districts FOR ALL
    TO authenticated
    USING (public.get_current_user_role() = 'admin')
    WITH CHECK (public.get_current_user_role() = 'admin');

-- INFRASTRUCTURE
DROP POLICY IF EXISTS "Anyone can view infrastructure" ON public.infrastructure;
CREATE POLICY "Anyone can view infrastructure"
    ON public.infrastructure FOR SELECT
    TO authenticated, anon
    USING (true);

DROP POLICY IF EXISTS "Admins can manage infrastructure" ON public.infrastructure;
CREATE POLICY "Admins can manage infrastructure"
    ON public.infrastructure FOR ALL
    TO authenticated
    USING (public.get_current_user_role() = 'admin')
    WITH CHECK (public.get_current_user_role() = 'admin');

-- DEMOGRAPHICS
DROP POLICY IF EXISTS "Anyone can view demographics" ON public.demographics;
CREATE POLICY "Anyone can view demographics"
    ON public.demographics FOR SELECT
    TO authenticated, anon
    USING (true);

DROP POLICY IF EXISTS "Admins can manage demographics" ON public.demographics;
CREATE POLICY "Admins can manage demographics"
    ON public.demographics FOR ALL
    TO authenticated
    USING (public.get_current_user_role() = 'admin')
    WITH CHECK (public.get_current_user_role() = 'admin');

-- INVESTMENTS
DROP POLICY IF EXISTS "Anyone can view investments" ON public.investments;
CREATE POLICY "Anyone can view investments"
    ON public.investments FOR SELECT
    TO authenticated, anon
    USING (true);

DROP POLICY IF EXISTS "Admins can manage investments" ON public.investments;
CREATE POLICY "Admins can manage investments"
    ON public.investments FOR ALL
    TO authenticated
    USING (public.get_current_user_role() = 'admin')
    WITH CHECK (public.get_current_user_role() = 'admin');

-- -----------------------------------------------------------------------------
-- 6. POLICIES: AI ANALYSES TABLE
-- Citizens can view analysis for their requests; Policymakers/admins can view all.
-- Insert/Update restricted to service-role or admin.
-- -----------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users view analysis of own requests or staff view all" ON public.ai_analyses;
CREATE POLICY "Users view analysis of own requests or staff view all"
    ON public.ai_analyses FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.citizen_requests cr
            WHERE cr.id = ai_analyses.request_id
            AND cr.user_id = auth.uid()
        )
        OR public.get_current_user_role() IN ('policymaker', 'admin')
    );

DROP POLICY IF EXISTS "Admins and service-role can insert ai analyses" ON public.ai_analyses;
CREATE POLICY "Admins and service-role can insert ai analyses"
    ON public.ai_analyses FOR INSERT
    TO authenticated
    WITH CHECK (
        public.get_current_user_role() = 'admin'
    );
