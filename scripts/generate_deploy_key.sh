#!/bin/bash
# ============================================================
# GitHub Actions Deploy Anahtarı Oluşturucu
# Yerel bilgisayarınızda (veya sunucuda) çalıştırın.
# ============================================================
set -e

KEY_PATH="$HOME/.ssh/startup_deploy_key"

echo ""
echo "========================================"
echo "  GitHub Actions Deploy Anahtarı Kurulumu"
echo "========================================"
echo ""

# ---- Anahtar Oluştur ----
if [ -f "$KEY_PATH" ]; then
  echo "[INFO] Anahtar zaten mevcut: $KEY_PATH"
else
  echo "[INFO] ed25519 anahtar çifti oluşturuluyor..."
  ssh-keygen -t ed25519 -C "github-actions-deploy-startup" -f "$KEY_PATH" -N ""
  echo "[OK]   Anahtar oluşturuldu."
fi

echo ""
echo "========================================"
echo "  ADIM 1 — Public Key'i Sunucuya Ekleyin"
echo "========================================"
echo ""
echo "Aşağıdaki komutu kopyalayıp sunucuda çalıştırın:"
echo ""
echo "  ssh root@57.129.6.176 \"echo '$(cat ${KEY_PATH}.pub)' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""
echo ""

echo "========================================"
echo "  ADIM 2 — GitHub Secrets'a Ekleyin"
echo "========================================"
echo ""
echo "GitHub → Repo → Settings → Secrets → Actions → New repository secret"
echo ""
echo "Secret: VPS_HOST"
echo "Değer:  57.129.6.176"
echo ""
echo "Secret: VPS_USER"
echo "Değer:  root"
echo ""
echo "Secret: VPS_SSH_KEY"
echo "Değer (aşağıdaki TÜMÜNÜ kopyalayın — BEGIN ve END dahil):"
echo ""
cat "$KEY_PATH"
echo ""

echo "========================================"
echo "  ADIM 3 — Bağlantıyı Test Edin"
echo "========================================"
echo ""
echo "  ssh -i $KEY_PATH root@57.129.6.176 'echo Bağlantı başarılı!'"
echo ""
