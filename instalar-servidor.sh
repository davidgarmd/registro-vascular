#!/bin/bash
# Instala el registro vascular en un servidor Ubuntu 24.04 recién creado.
# Uso (como root, desde la carpeta registro-vascular):   bash instalar-servidor.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
  echo "Ejecuta este script como root (o con sudo)." >&2
  exit 1
fi

echo "== 1/6 Actualizando el sistema e instalando utilidades"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get upgrade -yq
apt-get install -yq curl sqlite3 ufw unattended-upgrades fail2ban
dpkg-reconfigure -f noninteractive unattended-upgrades   # parches de seguridad automáticos

echo "== 2/6 Instalando Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

echo "== 3/6 Configurando el cortafuegos (solo SSH, HTTP y HTTPS)"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "== 4/6 Configuración"
if [ ! -f .env ]; then
  read -rp "Dominio (p. ej. registro.midominio.es): " DOMINIO
  read -rp "Tu correo (avisos del certificado HTTPS): " EMAIL_ADMIN
  read -rp "Cuenta de Gmail que enviará los recordatorios (vacío para configurarlo luego): " GMAIL
  GMAIL_PASS=""
  if [ -n "$GMAIL" ]; then
    read -rsp "Contraseña de aplicación de Gmail (16 letras, sin espacios): " GMAIL_PASS
    echo
  fi
  cat > .env <<CONF
DOMINIO=$DOMINIO
EMAIL_ADMIN=$EMAIL_ADMIN
REGISTRO_BASE_URL=https://$DOMINIO
REGISTRO_RECORDATORIO_HORA=8
TZ=Europe/Madrid
CONF
  if [ -n "$GMAIL" ]; then
    cat >> .env <<CONF
REGISTRO_MAIL_SERVER=smtp.gmail.com
REGISTRO_MAIL_PORT=587
REGISTRO_MAIL_USE_TLS=true
REGISTRO_MAIL_USERNAME=$GMAIL
REGISTRO_MAIL_PASSWORD="${GMAIL_PASS// /}"
REGISTRO_MAIL_FROM=$GMAIL
CONF
  fi
  chmod 600 .env
else
  echo "Ya existe .env; se conserva."
  DOMINIO=$(grep '^DOMINIO=' .env | cut -d= -f2)
fi
mkdir -p datos
chown 1000:1000 datos
chmod 700 datos

echo "== 5/6 Arrancando la aplicación (la primera vez tarda unos minutos)"
docker compose up -d --build
sleep 5
docker compose ps

echo "== 6/6 Programando la copia de seguridad diaria (3:00)"
echo "0 3 * * * root $(pwd)/copia-seguridad.sh >> /var/log/registro-copia.log 2>&1" > /etc/cron.d/registro-copia

echo
echo "Listo. Crea ahora tu usuario administrador:"
echo "   docker compose exec app flask --app registro crear-usuario --admin"
echo
echo "Después entra en https://$DOMINIO"
echo "(Si el navegador avisa del certificado, espera 1-2 minutos: Caddy lo está obteniendo.)"
