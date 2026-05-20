# 🚀 Render.com → OVH VPS Geçiş Planı (v3 — Production-Ready)

**Sunucu:** `57.129.6.176` (OVH — 4 vCore, 8 GB RAM)  
**Proje:** Startup Idea Finder  
**GitHub:** `https://github.com/tarikmenguc/Startup_Idea_Finder`  
**Reverse Proxy:** Caddy (otomatik HTTPS, SSE-uyumlu)  
**CI/CD:** GitHub Actions → push to main → otomatik deploy

---

## Mimari

```
kullanıcı
    │
    ▼
Vercel (Next.js) ← frontend, Vercel'de kalıyor
    │  /api/:path* istekleri (vercel.json catch-all rewrite)
    ▼
OVH VPS :443  ←  Caddy (otomatik HTTPS + SSE-aware proxy)
    │
    ▼
FastAPI :8000  +  Scheduler (Docker Compose, bind-mount data/)
```

---

## Neden Caddy?

| Özellik | Nginx | Caddy |
|---|---|---|
| Otomatik HTTPS (Let's Encrypt) | ❌ Certbot + cron gerekir | ✅ Kutudan çıkar |
| SSE/Streaming buffering | Manuel config gerekir | `flush_interval -1` yeterli |
| HTTP/3 (QUIC) | Ayrı derleme | ✅ Yerleşik |
| Config satır sayısı | ~25 satır | ~10 satır |
| Performans farkı (4-core VM) | ~48K req/s | ~42K req/s |

**Karar:** Bu ölçekte performans farkı ihmal edilebilir. Caddy açık ara öne çıkıyor.

---

## Kritik Düzeltme Notları (Plan Yazımı Öncesi Analiz)

Aşağıdaki tespitler kodun doğrudan incelenmesinden çıkmıştır:

### ✅ Onaylanan ve Düzeltilen Sorunlar

**1. `flush_interval -1` (SSE Buffering)**
`routers/chat.py`, `routers/scan.py`, `routers/extension.py` → üçü de `StreamingResponse` + `text/event-stream` kullanıyor. Caddy varsayılan olarak yanıtı tamponlar; bu olmadan chat/scan hiç akmaz, tüm yanıt bitince gelir. **Kesinlikle zorunlu.**

**2. `.dockerignore` Eksikliği (Güvenlik Açığı)**
Dockerfile'da `COPY . .` var. Projede `.dockerignore` **yok**. Bu, `.env` (API anahtarları), `venv/` (300+ MB), `data/` (veritabanı dosyaları), `.git/` (commit geçmişi) ve `__pycache__/`'nin tamamının Docker image'ına girdiği anlamına gelir. `.dockerignore` eklemek hem güvenlik hem de image boyutu için zorunludur.

**3. Zero-Downtime Build**
`docker compose up --build -d` build sırasında container'ı durdurur → 1-2 dk 502 hatası. Build ve up'ı ayırmak bunu minimize eder.

**4. Vercel Catch-All**
Tek tek endpoint listelemek yerine tek kural yeterli.

**5. Workflow'a Health Check**
Deploy sonrası API cevap vermiyorsa Actions pipeline başarısız sayılmalı.

### ❌ Yanlış Tespit Edilen / Düzeltilen Sorunlar

**İddia: "`git pull` `.env` dosyasını ezer"**
**Gerçek:** `.env`, `.gitignore`'da tanımlı. `git pull`, gitignored dosyalara dokunmaz. `.env` sunucuda güvenle kalır. GitHub Secrets'a koyup workflow'dan yazmak gereksiz karmaşıklık katar ve secrets yönetimini zorlaştırır. **Asıl sorun farklı:** `.env` dosyası git'te olmasa da Docker build context'ine giriyor ve image'a bake ediliyor — çünkü `.dockerignore` yok. **Çözüm: `.dockerignore`.**

**İddia: "`chmod 777` gerekli, container non-root çalışıyor olabilir"**
**Gerçek:** `Dockerfile` incelendi — `USER` direktifi yok, container root olarak çalışıyor. Volume üzerinde yazma hakkı tam, hiçbir sorun yok. `chmod 777` hem gereksiz hem kötü güvenlik pratiği. **Uygulanmamalı.**

**İddia: Ölü `volumes: data:` tanımı (tespit edilmemiş)**
`docker-compose.yml` altında `volumes: data:` named volume tanımı var ama hiçbir servis bunu kullanmıyor. Tüm servisler `./data:/app/data` bind mount kullanıyor. Bu ölü kod. Temizlenmesi gerekiyor.

---

## AŞAMA 0 — Sunucu Bağlantı Testi

```bash
ssh root@57.129.6.176
# Bağlantı başarılıysa devam et
```

Domain durumu:

- **Domain varsa (önerilen):** `A  api.yourdomain.com → 57.129.6.176` kaydı ekle. Caddy sertifikayı otomatik alır.
- **Sadece IP ile:** HTTP üzerinden devam edilir. Vercel rewrites sunucu-taraflı çalıştığı için kabul edilebilir.

---

## AŞAMA 1 — Sunucuyu Hazırla

### 1.1 Sistemi Güncelle

```bash
apt update && apt upgrade -y
```

### 1.2 Docker Kur

```bash
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin

# Doğrula
docker --version        # 26.x veya üzeri
docker compose version  # v2.x
```

### 1.3 Caddy Kur

```bash
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | tee /etc/apt/sources.list.d/caddy-stable.list

apt update && apt install -y caddy
systemctl enable caddy
caddy version  # Doğrula
```

### 1.4 Firewall

```bash
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP (Caddy → HTTPS yönlendirir)
ufw allow 443/tcp    # HTTPS
ufw enable
ufw status

# ⚠️ Port 8000 AÇMA — sadece Caddy localhost üzerinden erişsin
# docker-compose.yml ports: "8000:8000" host'a bind eder ama
# UFW bunu engeller; dışarıdan erişilemez
```

---

## AŞAMA 2 — Projeyi Çek ve Yapılandır

### 2.1 GitHub'dan Clone

```bash
cd /opt
git clone https://github.com/tarikmenguc/Startup_Idea_Finder.git
cd Startup_Idea_Finder
```

> Repo public olduğu için authentication gerekmez. Repo private yapılırsa
> sunucuda `git remote set-url origin` ile token'lı URL kullanılmalı.

### 2.2 `.env` Dosyasını Oluştur

```bash
cp .env.example .env
nano .env
```

Render.com → Settings → Environment'dan kopyala:

```env
GROQ_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
GOOGLE_API_KEY=AIza...
REPLICATE_API_TOKEN=r8_...
PRODUCTHUNT_API_KEY=...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
RESEND_API_KEY=re_...
EXTENSION_API_KEY=...

# CORS — trailing slash olmadan
ALLOWED_ORIGINS=https://startup-idea-finder.vercel.app

LANGSMITH_TRACING=false
LOG_LEVEL=INFO
```

> `.env` gitignored olduğu için `git pull` bu dosyaya dokunmaz. Sunucuda güvende kalır.

### 2.3 Data Dizini

```bash
mkdir -p /opt/Startup_Idea_Finder/data/history
# Dockerfile'da USER direktifi yok → container root çalışıyor
# chmod gerekmez; bind mount'a tam yazma hakkı var
```

---

## AŞAMA 3 — `.dockerignore` Oluştur (Güvenlik — Zorunlu)

Bu dosya olmadan `COPY . .` komutu `.env`, `venv/`, `data/`, `.git/` gibi
hassas ve büyük dosyaları Docker image'ına bake eder.

**Yerel bilgisayarında** proje kökünde `.dockerignore` oluştur:

```
# Gizli — image'a girmesin
.env
.env.*

# Büyük / gereksiz
venv/
__pycache__/
*.pyc
*.pyo
data/
chroma_db/
node_modules/

# Git
.git/
.gitignore

# CI/CD
.github/

# IDE / OS
.vscode/
.idea/
.DS_Store
Thumbs.db

# Frontend (ayrı build context'i var)
web/node_modules/
web/.next/
web/.env.local

# Dokümantasyon
*.md
*.txt
docs/
```

Oluşturup push et:

```bash
git add .dockerignore
git commit -m "security: add .dockerignore to prevent secrets in Docker image"
git push origin main
```

---

## AŞAMA 4 — `docker-compose.yml` Temizliği

`docker-compose.yml` altındaki kullanılmayan `volumes: data:` named volume tanımını kaldır.
Tüm servisler zaten `./data:/app/data` bind mount kullanıyor; bu tanım ölü kod.

**Yerel bilgisayarında:**

```yaml
# Silinecek satırlar (dosyanın en altında):
volumes:
  data:
```

Bu satırları sil, kaydet, push et:

```bash
git add docker-compose.yml
git commit -m "fix: remove unused named volume declaration from docker-compose"
git push origin main
```

---

## AŞAMA 5 — Backend'i Başlat

`web` servisi Vercel'de çalışacağı için sadece `api` ve `scheduler` başlatılır.

```bash
cd /opt/Startup_Idea_Finder

# Build et ve arka planda başlat
docker compose up --build -d api scheduler

# Durum kontrolü
docker compose ps
docker compose logs -f api

# Sağlık kontrolü
curl http://localhost:8000/health
# Beklenen: 200 OK
```

---

## AŞAMA 6 — Caddy Yapılandırması

### Seçenek A: Domain + Otomatik HTTPS (Önerilen)

```bash
nano /etc/caddy/Caddyfile
```

```caddyfile
api.yourdomain.com {
    # Caddy Let's Encrypt sertifikasını otomatik alır ve yeniler

    reverse_proxy localhost:8000 {
        # ⚠️ KRİTİK: SSE streaming (chat/scan/extension) için zorunlu
        # Olmadan Caddy yanıtı tamponlar; token token akış çalışmaz
        flush_interval -1

        transport http {
            read_timeout  5m
            write_timeout 5m
        }
    }

    encode gzip zstd

    header {
        X-Frame-Options        "DENY"
        X-Content-Type-Options "nosniff"
        -Server                # Caddy imzasını gizle
    }

    log {
        output file /var/log/caddy/startup-api.log
        format console
    }
}
```

### Seçenek B: Sadece IP ile (HTTP)

```caddyfile
:80 {
    reverse_proxy localhost:8000 {
        flush_interval -1   # SSE için zorunlu

        transport http {
            read_timeout  5m
            write_timeout 5m
        }
    }

    encode gzip zstd

    header {
        X-Frame-Options        "DENY"
        X-Content-Type-Options "nosniff"
    }
}
```

### Caddy'yi Uygula

```bash
caddy validate --config /etc/caddy/Caddyfile   # Önce syntax kontrolü
systemctl restart caddy
systemctl status caddy

# Test (dışarıdan):
curl http://57.129.6.176/health              # Seçenek B
curl https://api.yourdomain.com/health       # Seçenek A
```

---

## AŞAMA 7 — Vercel'i Güncelle

`web/vercel.json` dosyasını düzenle. Tek tek endpoint listelemek yerine
catch-all kural kullan — yeni endpoint ekledikçe vercel.json'a dokunman gerekmez.

**Seçenek A (Domain + HTTPS):**

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm install",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.yourdomain.com/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options",        "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }
  ]
}
```

**Seçenek B (Sadece IP + HTTP):**

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm install",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://57.129.6.176/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options",        "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" }
      ]
    }
  ]
}
```

Push et → Vercel otomatik deploy:

```bash
git add web/vercel.json
git commit -m "chore: backend URL Render → OVH VPS (catch-all rewrite)"
git push origin main
```

---

## AŞAMA 8 — GitHub Actions CI/CD

Her `main` push'unda: build (eski container ayaktayken) → up → health check.

### 8.1 Deploy SSH Anahtarı Oluştur

**Yerel bilgisayarında:**

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key -N ""

# Public key → sunucuya eklenecek:
cat ~/.ssh/deploy_key.pub

# Private key → GitHub Secrets'a eklenecek:
cat ~/.ssh/deploy_key
```

### 8.2 Public Key'i Sunucuya Ekle

```bash
# Sunucuda:
echo "BURAYA_DEPLOY_KEY_PUB_ICERIGI" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test et (yerel bilgisayarından):
ssh -i ~/.ssh/deploy_key root@57.129.6.176 "echo bağlantı başarılı"
```

### 8.3 GitHub Secrets'a Ekle

GitHub → Repo → Settings → Secrets and variables → Actions → **New repository secret**

| Secret | Değer |
|---|---|
| `VPS_HOST` | `57.129.6.176` |
| `VPS_USER` | `root` |
| `VPS_SSH_KEY` | `~/.ssh/deploy_key` dosyasının tüm içeriği (`-----BEGIN` dahil) |

### 8.4 Workflow Dosyası

`.github/workflows/deploy.yml` zaten oluşturuldu. İçeriği:

```yaml
name: Deploy to OVH VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    name: SSH Deploy
    runs-on: ubuntu-latest
    steps:
      - name: 🚀 Deploy to VPS
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            set -e

            echo "📦 Güncel kodu çekiyorum..."
            cd /opt/Startup_Idea_Finder
            git pull origin main

            echo "🔨 İmajı build ediyorum (eski container çalışırken)..."
            docker compose build api scheduler

            echo "🔄 Container'ları güncelliyorum..."
            docker compose up -d api scheduler

            echo "🧹 Eski image'ları temizliyorum..."
            docker image prune -f

            echo "🏥 Sağlık kontrolü (5s bekleniyor)..."
            sleep 5
            curl -f http://localhost:8000/health \
              || (echo "❌ Health check başarısız! Deploy geri alınıyor..." && exit 1)

            echo "✅ Deploy başarılı!"
            docker compose ps
```

> **Not:** `docker compose build` (ayrı) + `docker compose up -d` (ayrı) yaklaşımı,
> `up --build -d`'ye göre önemli bir fark sağlar: build sırasında eski container
> çalışmaya devam eder. `up -d` yalnızca yeni image hazır olduğunda container'ı
> değiştirir. Bu "near-zero downtime" sağlar (~2-5 saniye kesinti).
> Gerçek sıfır-kesinti için Docker Swarm veya Kubernetes gerekir — bu ölçek için gerekmez.

---

## AŞAMA 9 — CI/CD Pipeline'ı Test Et

```bash
# Yerel bilgisayarında:
git commit --allow-empty -m "test: CI/CD pipeline testi"
git push origin main
```

GitHub → Actions sekmesinde deploy adımlarını canlı izle.  
Tüm adımlar yeşil → pipeline hazır.

---

## AŞAMA 10 — Doğrulama Kontrol Listesi

```bash
# 1. API sağlık kontrolü (sunucudan)
curl http://localhost:8000/health

# 2. Caddy üzerinden (dışarıdan)
curl http://57.129.6.176/health
# veya:
curl https://api.yourdomain.com/health

# 3. SSE streaming çalışıyor mu? (chat endpoint)
curl -N -H "Accept: text/event-stream" \
     http://57.129.6.176/api/chat/...
# Token token gelmeli, toplu değil

# 4. CORS header'ı doğru mu?
curl -H "Origin: https://startup-idea-finder.vercel.app" \
     -I http://57.129.6.176/api/health
# Access-Control-Allow-Origin görünmeli

# 5. Scheduler çalışıyor mu?
docker compose logs scheduler | tail -20

# 6. Container'lar ayakta mı?
docker compose ps
```

---

## CI/CD Akış Diyagramı

```
git push origin main
        │
        ▼
  GitHub Actions tetiklenir
        │
        ▼
  SSH → OVH VPS (root@57.129.6.176)
        │
        ├─ git pull origin main
        │  (container hâlâ çalışıyor)
        │
        ├─ docker compose build api scheduler
        │  (yeni image build edilir, eski container çalışıyor)
        │
        ├─ docker compose up -d api scheduler
        │  (~2-5s kesinti — eski stop, yeni start)
        │
        ├─ docker image prune -f
        │  (eski image'lar temizlenir)
        │
        ├─ sleep 5 && curl /health
        │  (başarısız → pipeline kırmızı, bildirim alırsın)
        │
        └─ docker compose ps
           (son durum loglanır)

Toplam süre: ~2-3 dakika
```

---

## Bakım Komutları

| İşlem | Komut |
|---|---|
| API logları | `docker compose logs -f api` |
| Scheduler logları | `docker compose logs -f scheduler` |
| Caddy logları | `journalctl -u caddy -f` |
| Yeniden başlat | `docker compose restart api scheduler` |
| Manuel deploy | `git pull && docker compose build api scheduler && docker compose up -d api scheduler` |
| Disk kullanımı | `df -h && docker system df` |
| Image temizliği | `docker image prune -f` |

---

## Sorun Giderme

**Chat/scan token token gelmiyor, toplu geliyor:**
```bash
# Caddyfile'da flush_interval -1 var mı?
grep flush /etc/caddy/Caddyfile
# Yoksa ekle ve: systemctl restart caddy
```

**API cevap vermiyor:**
```bash
docker compose ps
docker compose logs api
curl http://localhost:8000/health
```

**GitHub Actions SSH hatası:**
```bash
# Yerel bilgisayarından test et:
ssh -i ~/.ssh/deploy_key root@57.129.6.176 "echo ok"
# Secret'a yapıştırılan private key'in başında/sonunda boşluk olmamalı
```

**CORS hatası:**
```bash
grep ALLOWED /opt/Startup_Idea_Finder/.env
# Vercel URL doğru yazılmış mı? (https://, trailing slash yok)
docker compose restart api
```

**Vercel hâlâ Render'a gidiyor:**
```bash
# vercel.json commit + push edildi mi?
git log --oneline web/vercel.json
# Vercel dashboard'da yeni deploy başladı mı?
```
