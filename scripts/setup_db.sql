-- MedBridge Backend — Schema additions for MVP
-- Run these migrations in Supabase SQL editor or via CLI
-- These ADD columns and tables not already in the existing schema.
-- Do NOT re-run if columns already exist — check first.

-- ─────────────────────────────────────────────────────────────────────────────
-- health_records: add extraction and storage columns
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE health_records
  ADD COLUMN IF NOT EXISTS file_path TEXT,
  ADD COLUMN IF NOT EXISTS mime_type TEXT,
  ADD COLUMN IF NOT EXISTS file_size_bytes INTEGER,
  ADD COLUMN IF NOT EXISTS extracted_text TEXT,
  ADD COLUMN IF NOT EXISTS extraction_method TEXT,
  ADD COLUMN IF NOT EXISTS ocr_confidence NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS extraction_warnings JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS error_message TEXT,
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'uploaded'
    CHECK (status IN ('uploaded','processing','extracted','summarized','failed'));

-- ─────────────────────────────────────────────────────────────────────────────
-- document_chunks: for Q&A context retrieval
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_chunks (
  chunk_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id     UUID NOT NULL REFERENCES health_records(record_id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  chunk_index     INTEGER NOT NULL,
  chunk_text      TEXT NOT NULL,
  token_count     INTEGER,
  created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);

ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Users can access own chunks"
  ON document_chunks FOR ALL
  USING (auth.uid() = user_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- chat_messages: add feedback_rating column
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE chat_messages
  ADD COLUMN IF NOT EXISTS feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
  ADD COLUMN IF NOT EXISTS parent_message_id UUID REFERENCES chat_messages(message_id),
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
    CHECK (role IN ('user', 'assistant'));

-- ─────────────────────────────────────────────────────────────────────────────
-- user_profiles: add accessibility preference columns
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE user_profiles
  ADD COLUMN IF NOT EXISTS preferred_language TEXT DEFAULT 'en',
  ADD COLUMN IF NOT EXISTS explanation_level TEXT DEFAULT 'plain'
    CHECK (explanation_level IN ('plain', 'detailed'));

-- ─────────────────────────────────────────────────────────────────────────────
-- KPI views
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW kpi_upload_outcomes AS
SELECT
  status,
  mime_type,
  error_message,
  COUNT(*) AS count,
  DATE_TRUNC('day', uploaded_at) AS day
FROM health_records
GROUP BY status, mime_type, error_message, DATE_TRUNC('day', uploaded_at)
ORDER BY day DESC;

CREATE OR REPLACE VIEW kpi_summary_engagement AS
SELECT
  hr.record_id AS document_id,
  hr.user_id,
  hr.uploaded_at,
  s.created_at AS summary_created_at,
  EXTRACT(EPOCH FROM (s.created_at - hr.uploaded_at)) AS seconds_to_summary,
  MIN(cm.created_at) AS first_question_at,
  EXTRACT(EPOCH FROM (MIN(cm.created_at) - s.created_at)) AS seconds_upload_to_first_question
FROM health_records hr
LEFT JOIN summaries s ON s.document_id = hr.record_id
LEFT JOIN chat_messages cm ON cm.document_id = hr.record_id AND cm.role = 'user'
GROUP BY hr.record_id, hr.user_id, hr.uploaded_at, s.created_at;

CREATE OR REPLACE VIEW kpi_chatbot_usage AS
SELECT
  user_id,
  document_id,
  COUNT(*) FILTER (WHERE role = 'user') AS questions_asked,
  AVG(feedback_rating) FILTER (WHERE feedback_rating IS NOT NULL) AS avg_rating,
  COUNT(feedback_rating) AS rated_responses
FROM chat_messages
GROUP BY user_id, document_id;

-- ─────────────────────────────────────────────────────────────────────────────
-- summary_feedback: patient understanding ratings
-- ─────────────────────────────────────────────────────────────────────────────
-- Shown after summary: "Did this explanation help you understand your document?"
-- Options: 'yes' | 'somewhat' | 'no'
CREATE TABLE IF NOT EXISTS summary_feedback (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  summary_id      UUID NOT NULL REFERENCES summaries(summary_id) ON DELETE CASCADE,
  understanding_rating TEXT NOT NULL CHECK (understanding_rating IN ('yes','somewhat','no')),
  created_at      TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE summary_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Users can manage own feedback"
  ON summary_feedback FOR ALL
  USING (auth.uid() = user_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- kpi_understanding: patient understanding KPI view
-- This is likely the most important product KPI.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW kpi_understanding AS
SELECT
  understanding_rating,
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
  DATE_TRUNC('day', created_at) AS day
FROM summary_feedback
GROUP BY understanding_rating, DATE_TRUNC('day', created_at)
ORDER BY day DESC, understanding_rating;

-- ─────────────────────────────────────────────────────────────────────────────
-- summaries: add quality tracking columns
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE summaries
  ADD COLUMN IF NOT EXISTS reading_level_score NUMERIC(4,2),
  ADD COLUMN IF NOT EXISTS quality_passed BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS quality_issues JSONB DEFAULT '[]';

-- ─────────────────────────────────────────────────────────────────────────────
-- appointment_prep: questions generated for provider conversations
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointment_prep (
  prep_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id   UUID NOT NULL REFERENCES health_records(record_id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  questions     JSONB NOT NULL DEFAULT '[]',
  created_at    TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE appointment_prep ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "Users can access own prep"
  ON appointment_prep FOR ALL
  USING (auth.uid() = user_id);
