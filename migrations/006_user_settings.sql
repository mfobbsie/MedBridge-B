-- Migration 006: user_settings
-- Stores per-user profile toggle preferences for the Profile page.
-- Supports: Allow Trusted Contacts, Allow MyChart Integration, Enable Reminders

CREATE TABLE user_settings (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  allow_trusted_contacts   BOOLEAN NOT NULL DEFAULT false,
  allow_mychart_integration BOOLEAN NOT NULL DEFAULT false,
  enable_reminders         BOOLEAN NOT NULL DEFAULT true,
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)
);

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users manage own settings"
  ON user_settings FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
