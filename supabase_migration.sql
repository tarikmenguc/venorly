-- ============================================================
-- Venorly — Supabase Güvenlik Migration
-- Çalıştırma: Supabase Dashboard > SQL Editor > New Query
-- ============================================================


-- ── 1. credits negatife düşemez constraint ──────────────────
-- Mevcut negatif değerleri önce 0'a çek (varsa)
UPDATE users SET credits = 0 WHERE credits < 0;

-- Constraint ekle
ALTER TABLE users
  ADD CONSTRAINT credits_non_negative
  CHECK (credits >= 0);

-- ── 2. consume_credit atomic fonksiyonu ─────────────────────
-- Race condition'ı önler: check + decrement tek transaction'da
-- Returns: TRUE = kredi düşüldü, FALSE = yetersiz kredi
CREATE OR REPLACE FUNCTION consume_credit(
    p_clerk_id TEXT,
    p_cost     INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER   -- Fonksiyon sahibinin yetkisiyle çalışır
AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    UPDATE users
    SET    credits = credits - p_cost
    WHERE  clerk_id = p_clerk_id
      AND  credits  >= p_cost;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected > 0;
END;
$$;

-- Sadece authenticated kullanıcılar çağırabilsin
REVOKE ALL ON FUNCTION consume_credit FROM PUBLIC;
GRANT EXECUTE ON FUNCTION consume_credit TO authenticated;
GRANT EXECUTE ON FUNCTION consume_credit TO service_role;


-- ── 3. scans tablosuna user_id kolonu ───────────────────────
-- IDOR fix için gerekli: hangi scan kime ait?
-- Kolon yoksa ekle (varsa hata vermez)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE  table_name  = 'scans'
          AND  column_name = 'user_id'
    ) THEN
        ALTER TABLE scans ADD COLUMN user_id TEXT;
        COMMENT ON COLUMN scans.user_id IS 'Clerk sub / Supabase user id — ownership için';
    END IF;
END $$;

-- Index ekle (ownership sorguları için)
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);


-- ── 4. Doğrulama sorguları ───────────────────────────────────
-- Migration'ı çalıştırdıktan sonra bu 3 sorguyu AYRI AYRI çalıştırıp
-- sonuçları kontrol edin (hepsini birden çalıştırmayın):

-- a) Constraint var mı? (PostgreSQL 12+ uyumlu)
SELECT conname,
       pg_get_constraintdef(oid) AS constraint_def
FROM   pg_constraint
WHERE  conrelid = 'users'::regclass
  AND  conname  = 'credits_non_negative';
-- Beklenen: 1 satır, constraint_def = "CHECK ((credits >= 0))"

-- b) Fonksiyon var mı?
SELECT proname,
       prosecdef,
       pg_get_functiondef(oid) AS func_def
FROM   pg_proc
WHERE  proname = 'consume_credit';
-- Beklenen: 1 satır, prosecdef = true

-- c) user_id kolonu var mı?
SELECT column_name, data_type, is_nullable
FROM   information_schema.columns
WHERE  table_name  = 'scans'
  AND  column_name = 'user_id';
-- Beklenen: 1 satır, data_type = 'text'


-- ── 5. Mevcut scan'lere user_id backfill ────────────────────
-- Eğer Supabase Auth kullanıyorsanız ve usage_logs'ta eşleşme
-- varsa aşağıdaki query ile backfill yapabilirsiniz:
-- (Opsiyonel — yeni scan'ler zaten user_id ile kaydedilecek)

-- UPDATE scans s
-- SET    user_id = ul.ip_address  -- ip_address clerk_id olarak kullanılıyorsa
-- FROM   usage_logs ul
-- WHERE  ul.action_type = s.mode
--   AND  s.user_id IS NULL
--   AND  ul.created_at::date = s.created_at::date;
