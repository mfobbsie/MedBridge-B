-- Migration 006: app_events table
-- Tracks all user interactions for analytics and KPI reporting

CREATE TABLE IF NOT EXISTS app_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    health_record_id UUID REFERENCES health_records(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_events_user_id ON app_events(user_id);
CREATE INDEX IF NOT EXISTS idx_app_events_event_type ON app_events(event_type);
CREATE INDEX IF NOT EXISTS idx_app_events_event_category ON app_events(event_category);
CREATE INDEX IF NOT EXISTS idx_app_events_created_at ON app_events(created_at);
CREATE INDEX IF NOT EXISTS idx_app_events_session_id ON app_events(session_id);

ALTER TABLE app_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert their own events"
    ON app_events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own events"
    ON app_events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role has full access"
    ON app_events FOR ALL
    USING (auth.role() = 'service_role');
