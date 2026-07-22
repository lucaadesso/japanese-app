#!/usr/bin/env bash
# enable-ssl.sh — Da eseguire UNA VOLTA dopo aver aggiunto il record DNS
# su Cloudflare per japanese.minkyos.com → 140.238.220.28 (DNS only, no proxy)
#
# Uso: sudo bash /home/ubuntu/japanese-app/systemd/enable-ssl.sh

set -e

DOMAIN="japanese.minkyos.com"
EMAIL="admin@minkyos.com"
APP_DIR="/home/ubuntu/japanese-app"

echo ">>> Verifico che il DNS sia propagato per $DOMAIN..."
RESOLVED=$(dig +short "$DOMAIN" A | head -1)
if [ -z "$RESOLVED" ]; then
  echo "ERRORE: DNS non ancora propagato per $DOMAIN."
  echo "Aggiungi prima il record A su Cloudflare:"
  echo "  Tipo: A  |  Nome: japanese  |  IP: 140.238.220.28  |  Proxy: DNS only (grigio)"
  exit 1
fi
echo ">>> DNS OK: $DOMAIN → $RESOLVED"

echo ">>> Ottengo certificato SSL con Certbot..."
certbot --nginx \
  -d "$DOMAIN" \
  --non-interactive \
  --agree-tos \
  --email "$EMAIL" \
  --redirect

echo ">>> Ricarico Nginx..."
systemctl reload nginx

echo ""
echo "✅ SSL attivo! Visita: https://$DOMAIN"
