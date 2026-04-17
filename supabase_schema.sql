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

-- ============================================================
-- GALLERY (Discover Gallery — V8)
-- Mevcut scans tablosuna gallery kolonları eklenir.
-- Supabase SQL Editöründe çalıştır.
-- ============================================================

ALTER TABLE scans ADD COLUMN IF NOT EXISTS is_gallery    BOOLEAN DEFAULT false;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS gallery_title TEXT;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS gallery_summary TEXT;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS gallery_tags  TEXT[];
ALTER TABLE scans ADD COLUMN IF NOT EXISTS gallery_score INT    DEFAULT 0;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS gallery_emoji TEXT   DEFAULT '💡';
-- "2025-W15" formatı — aynı kategori + hafta için dedup
ALTER TABLE scans ADD COLUMN IF NOT EXISTS gallery_week  TEXT;

-- Duplikasyon önleme: aynı kategori + aynı hafta sadece 1 galeri kaydı
CREATE UNIQUE INDEX IF NOT EXISTS idx_gallery_category_week
    ON scans (category, gallery_week)
    WHERE is_gallery = true;

-- Galeri listeleme sorguları için bileşik index
CREATE INDEX IF NOT EXISTS idx_gallery_listing
    ON scans (is_gallery, gallery_score DESC, created_at DESC)
    WHERE is_gallery = true;

-- ============================================================
-- ALERTS (Niş Alarm Sistemi — V8)
-- ============================================================

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword TEXT NOT NULL,
    email TEXT NOT NULL,
    channels TEXT[] DEFAULT '{"reddit","github","huggingface"}',
    frequency TEXT DEFAULT 'daily',  -- 'daily' | 'weekly'
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users"   ON alerts FOR SELECT USING (true);
CREATE POLICY "Enable insert access for all users" ON alerts FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update access for all users" ON alerts FOR UPDATE USING (true);
CREATE POLICY "Enable delete access for all users" ON alerts FOR DELETE USING (true);

CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (is_active, frequency) WHERE is_active = true;
