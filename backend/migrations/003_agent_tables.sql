-- Agent processed emails tracking
CREATE TABLE IF NOT EXISTS agent_processed_emails (
    email_id TEXT PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_type TEXT,  -- 'candidate', 'position', 'other'
    action_taken TEXT,
    draft_id TEXT,
    metadata JSONB  -- Store additional context like sender, subject, etc.
);

CREATE INDEX idx_processed_emails_type ON agent_processed_emails(email_type);
CREATE INDEX idx_processed_emails_processed_at ON agent_processed_emails(processed_at);

-- Agent notifications for human-in-the-loop
CREATE TABLE IF NOT EXISTS agent_notifications (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT,  -- 'candidate_received', 'position_received', 'clarification_needed', etc.
    summary TEXT,
    action_url TEXT,
    is_read BOOLEAN DEFAULT false,
    status TEXT DEFAULT 'pending',  -- 'pending', 'reviewed', 'dismissed'
    related_email_id TEXT REFERENCES agent_processed_emails(email_id),
    metadata JSONB  -- Store draft content, recommendations, etc.
);

CREATE INDEX idx_notifications_is_read ON agent_notifications(is_read);
CREATE INDEX idx_notifications_status ON agent_notifications(status);
CREATE INDEX idx_notifications_created_at ON agent_notifications(created_at);
CREATE INDEX idx_notifications_type ON agent_notifications(type);
