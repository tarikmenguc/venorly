-- Scans (Taramalar)
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT DEFAULT 'completed',
    report_preview TEXT,
    leads_count INT DEFAULT 0,
    angles_count INT DEFAULT 0,
    full_report JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Leads (Müşteri Adayları)
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    description TEXT,
    score INT DEFAULT 0,
    status TEXT DEFAULT 'new',
    dm_template TEXT,
    scan_category TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Waitlists (Bekleme Listeleri)
CREATE TABLE waitlists (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    target_audience TEXT,
    emails TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Allow public access for now since we don't have auth yet
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON scans FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON scans FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON scans FOR UPDATE USING (true);

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON leads FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON leads FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON leads FOR UPDATE USING (true);

ALTER TABLE waitlists ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON waitlists FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON waitlists FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON waitlists FOR UPDATE USING (true);

-- Chat Messages (AI Fikir Danışmanı Sohbet Geçmişi)
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON chat_messages FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON chat_messages FOR INSERT WITH CHECK (true);
