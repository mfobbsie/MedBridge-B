-- ============================================================
-- MedBridge — Missing schema (app feature tables + OCR columns)
-- Run once after 001–007 in Supabase SQL Editor
-- ============================================================

-- health_records: OCR columns used by document_service.py
ALTER TABLE health_records
  ADD COLUMN IF NOT EXISTS extraction_method TEXT,
  ADD COLUMN IF NOT EXISTS ocr_confidence NUMERIC(5,2);

-- user_profiles: created on POST /auth/register
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id             UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name           TEXT,
  preferred_language  TEXT NOT NULL DEFAULT 'en',
  explanation_level   TEXT NOT NULL DEFAULT 'plain'
    CHECK (explanation_level IN ('plain', 'detailed')),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own profile"
  ON user_profiles FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- document_chunks: Q&A context for chat
CREATE TABLE IF NOT EXISTS document_chunks (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES health_records(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  chunk_index   INTEGER NOT NULL,
  chunk_text    TEXT NOT NULL,
  token_count   INTEGER,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own chunks"
  ON document_chunks FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- appointment_prep: provider conversation questions
CREATE TABLE IF NOT EXISTS appointment_prep (
  prep_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES health_records(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  questions     JSONB NOT NULL DEFAULT '[]',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE appointment_prep ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own prep"
  ON appointment_prep FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- reminders
CREATE TABLE IF NOT EXISTS reminders (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  health_record_id  UUID REFERENCES health_records(id) ON DELETE SET NULL,
  reminder_type     TEXT NOT NULL,
  title             TEXT NOT NULL,
  body              TEXT,
  remind_at         TIMESTAMPTZ NOT NULL,
  repeat_interval   TEXT,
  completed         BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own reminders"
  ON reminders FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- trusted_contacts
CREATE TABLE IF NOT EXISTS trusted_contacts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  contact_email  TEXT NOT NULL,
  contact_name   TEXT NOT NULL,
  access_level   TEXT NOT NULL DEFAULT 'read'
    CHECK (access_level IN ('read', 'full')),
  status         TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'accepted', 'revoked')),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE trusted_contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own contacts"
  ON trusted_contacts FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- providers
CREATE TABLE IF NOT EXISTS providers (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  specialty         TEXT,
  phone             TEXT,
  address           TEXT,
  fhir_provider_id  TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own providers"
  ON providers FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- resources (shared curated content, no user FK)
CREATE TABLE IF NOT EXISTS resources (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  description     TEXT,
  url             TEXT,
  resource_type   TEXT,
  tags            JSONB DEFAULT '[]',
  condition_codes JSONB DEFAULT '[]',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE resources ENABLE ROW LEVEL SECURITY;

-- Authenticated users can read shared resources
CREATE POLICY "authenticated users read resources"
  ON resources FOR SELECT
  TO authenticated
  USING (true);

-- health_scores
CREATE TABLE IF NOT EXISTS health_scores (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  health_record_id  UUID REFERENCES health_records(id) ON DELETE SET NULL,
  score             NUMERIC(5,2) NOT NULL,
  score_label       TEXT,
  rationale         TEXT,
  scored_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE health_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own health scores"
  ON health_scores FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
