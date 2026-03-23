-- Usage Logs (API Rate Limiting)
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address TEXT NOT NULL,
    action_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Hızlı IP tabanlı sorgular için index
CREATE INDEX idx_usage_logs_ip_date ON usage_logs(ip_address, created_at);
