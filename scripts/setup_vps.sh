#!/bin/bash
# ============================================================
# Venor AI — OVH VPS Kurulum Scripti
# Kullanım: bash setup_vps.sh
# ubuntu kullanıcısıyla çalıştırın (sudo yetkisi olmalı)
# ============================================================
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
error()   { echo -e "${RED}[ERR]${NC}  $1"; exit 1; }

PROJECT_DIR="/home/ubuntu/venor-ai"
REPO_URL="https://github.com/tarikmenguc/Startup_Idea_Finder.git"
CADDYFILE="/home/ubuntu/chat-bot/Caddyfile"
CADDY_CONTAINER="chat-bot-caddy-1"
VERCEL_ORIGIN="https://startup-idea-finder-fast.vercel.app"

echo ""
echo "=============================================="
echo "  Venor AI — VPS Kurulumu"
echo "=============================================="
echo ""

# ---- 1. Docker kontrolü ----
command -v docker &>/dev/null || error "Docker bulunamadı. Önce Docker kurun."
docker compose version &>/dev/null || error "Docker Compose bulunamadı."
success "Docker ve Compose mevcut."

# ---- 2. DNS kontrolü ----
info "api.venorly.digital DNS kaydı kontrol ediliyor..."
RESOLVED=$(dig +short api.venorly.digital 2>/dev/null || host api.venorly.digital 2>/dev/null | awk '/has address/ {print $4}')
SERVER_IP=$(curl -sf https://api.ipify.org || echo "")

if [ "$RESOLVED" = "$SERVER_IP" ]; then
  success "DNS doğru: api.venorly.digital → $SERVER_IP"
else
  warn "DNS henüz bu sunucuya gelmiyor (çözümlenen: '${RESOLVED}', sunucu: '${SERVER_IP}')"
  warn "Caddy sertifika alamaz. DNS yayılımını bekleyin veya devam etmek için Enter'a basın."
  read -r
fi

# ---- 3. Repo klonla / güncelle ----
if [ -d "$PROJECT_DIR/.git" ]; then
  info "Repo mevcut, güncelleniyor..."
  cd "$PROJECT_DIR" && git pull origin main
  success "Repo güncellendi."
else
  info "Repo klonlanıyor..."
  git clone "$REPO_URL" "$PROJECT_DIR"
  success "Repo hazır: $PROJECT_DIR"
fi

# ---- 4. Data dizini ----
mkdir -p "$PROJECT_DIR/data/history"
success "Data dizini hazır."

# ---- 5. .env kontrolü ----
if [ ! -f "$PROJECT_DIR/.env" ]; then
  cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
  echo ""
  echo -e "${YELLOW}=================================================="
  echo "  .env dosyasını doldurun, sonra scripti tekrar çalıştırın:"
  echo "  nano $PROJECT_DIR/.env"
  echo -e "==================================================${NC}"
  echo ""
  exit 0
fi

# ALLOWED_ORIGINS güncelle (içinde yoksa ekle)
if ! grep -q "ALLOWED_ORIGINS" "$PROJECT_DIR/.env"; then
  echo "ALLOWED_ORIGINS=$VERCEL_ORIGIN" >> "$PROJECT_DIR/.env"
  success "ALLOWED_ORIGINS eklendi."
else
  success ".env mevcut."
fi

# ---- 6. Mevcut Caddy'e venorly.digital bloğunu ekle ----
info "Mevcut Caddyfile kontrol ediliyor: $CADDYFILE"

if grep -q "venorly.digital" "$CADDYFILE"; then
  success "Caddyfile'da api.venorly.digital bloğu zaten mevcut."
else
  info "api.venorly.digital bloğu ekleniyor..."
  cat >> "$CADDYFILE" <<'CADDY_BLOCK'

api.venorly.digital {
    reverse_proxy localhost:8001 {
        # SSE streaming (chat/scan/extension) için zorunlu
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
        -Server
    }

    log {
        output file /var/log/caddy/venor-api.log
        format console
    }
}
CADDY_BLOCK
  success "Caddyfile güncellendi."
fi

# ---- 7. Caddy config'i doğrula ve yeniden yükle ----
info "Caddy config doğrulanıyor..."
docker exec "$CADDY_CONTAINER" caddy validate --config /etc/caddy/Caddyfile
info "Caddy yeniden yükleniyor (mevcut proje kesintisiz devam eder)..."
docker exec "$CADDY_CONTAINER" caddy reload --config /etc/caddy/Caddyfile
success "Caddy yeniden yüklendi. chat-bot etkilenmedi."

# ---- 8. Backend container'ları başlat ----
info "Venor AI servisleri başlatılıyor..."
cd "$PROJECT_DIR"
docker compose build api scheduler
docker compose up -d api scheduler
success "Servisler başlatıldı."

# ---- 9. Sağlık kontrolü ----
info "Sağlık kontrolü (10s bekleniyor)..."
sleep 10
if curl -sf http://localhost:8001/health > /dev/null; then
  success "API localhost:8001 üzerinde sağlıklı çalışıyor."
else
  error "API cevap vermiyor. Log: docker compose -f $PROJECT_DIR/docker-compose.yml logs api"
fi

# ---- Özet ----
echo ""
echo "=============================================="
echo -e "${GREEN}  Kurulum Tamamlandı!${NC}"
echo "=============================================="
echo ""
echo "  API endpoint:  https://api.venorly.digital/api/health"
echo "  Log takibi:    docker compose -f $PROJECT_DIR/docker-compose.yml logs -f api"
echo ""
echo "  Sıradaki adım: GitHub Secrets ekleyin (DEPLOYMENT_PLAN.md Aşama 8)"
echo ""
docker compose -f "$PROJECT_DIR/docker-compose.yml" ps
