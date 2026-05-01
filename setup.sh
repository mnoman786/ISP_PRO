#!/bin/bash
# NetCRM — Full Setup Script
# Run as root on Ubuntu/Debian after git clone/pull

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/env"

echo ""
echo "========================================"
echo "       NetCRM Setup Script"
echo "========================================"
echo ""

# ── 1. System packages ───────────────────────────────────────────
echo "→ Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl \
    mariadb-client libmariadb-dev pkg-config > /dev/null
ok "System packages installed"

# ── 2. Virtual environment ────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    ok "Virtual environment created"
else
    ok "Virtual environment already exists"
fi

source "$VENV_DIR/bin/activate"

# ── 3. Python dependencies ────────────────────────────────────────
echo "→ Installing Python packages..."
pip install -q -r "$PROJECT_DIR/requirements.txt"
ok "Python packages installed"

# ── 4. Create .env ────────────────────────────────────────────────
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "→ Setting up .env configuration..."
    echo ""

    read -p "  Server IP / Domain (e.g. 162.217.248.75): " SERVER_IP
    read -p "  FreeRADIUS DB host [127.0.0.1]: " RADIUS_HOST
    RADIUS_HOST=${RADIUS_HOST:-127.0.0.1}
    read -p "  FreeRADIUS DB name [radius]: " RADIUS_DB
    RADIUS_DB=${RADIUS_DB:-radius}
    read -p "  FreeRADIUS DB user [radius]: " RADIUS_USER
    RADIUS_USER=${RADIUS_USER:-radius}
    read -s -p "  FreeRADIUS DB password: " RADIUS_PASS
    echo ""
    read -p "  FreeRADIUS NAS secret [testing123]: " RADIUS_SECRET
    RADIUS_SECRET=${RADIUS_SECRET:-testing123}
    read -p "  Enable RADIUS? (yes/no) [yes]: " RADIUS_ENABLED
    RADIUS_ENABLED=${RADIUS_ENABLED:-yes}
    [ "$RADIUS_ENABLED" = "yes" ] && RADIUS_ENABLED=True || RADIUS_ENABLED=False

    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

    cat > "$ENV_FILE" <<EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP

# FreeRADIUS
RADIUS_ENABLED=$RADIUS_ENABLED
RADIUS_CLIENTS_CONF=/etc/freeradius/3.0/clients.conf
RADIUS_DEFAULT_SECRET=$RADIUS_SECRET
RADIUS_DB_HOST=$RADIUS_HOST
RADIUS_DB_PORT=3306
RADIUS_DB_NAME=$RADIUS_DB
RADIUS_DB_USER=$RADIUS_USER
RADIUS_DB_PASSWORD=$RADIUS_PASS
EOF
    ok ".env created"
else
    ok ".env already exists — skipping"
fi

# ── 5. Migrations ─────────────────────────────────────────────────
echo "→ Running database migrations..."
cd "$PROJECT_DIR"
python manage.py migrate --run-syncdb > /dev/null
ok "Migrations applied"

# ── 6. Static files ───────────────────────────────────────────────
echo "→ Collecting static files..."
python manage.py collectstatic --noinput > /dev/null
ok "Static files collected"

# ── 7. Superuser ──────────────────────────────────────────────────
echo ""
read -p "→ Create superuser? (yes/no) [yes]: " CREATE_SU
CREATE_SU=${CREATE_SU:-yes}
if [ "$CREATE_SU" = "yes" ]; then
    python manage.py shell -c "
from accounts.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@netcrm.local', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"
fi

# ── 8. Cron — expire connections ──────────────────────────────────
CRON_CMD="0 0 * * * cd $PROJECT_DIR && $VENV_DIR/bin/python manage.py expire_connections >> $PROJECT_DIR/logs/expiry.log 2>&1"
( crontab -l 2>/dev/null | grep -v "expire_connections"; echo "$CRON_CMD" ) | crontab -
ok "Cron job set (expire_connections daily at midnight)"

# ── 9. Gunicorn systemd service ───────────────────────────────────
SERVICE_FILE="/etc/systemd/system/netcrm.service"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=NetCRM Gunicorn
After=network.target

[Service]
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=$VENV_DIR/bin/gunicorn isp_crm.wsgi:application --bind 0.0.0.0:8000 --workers 3
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

pip install -q gunicorn
systemctl daemon-reload
systemctl enable netcrm > /dev/null
systemctl restart netcrm
ok "Gunicorn service started (port 8000)"

# ── 10. FreeRADIUS permissions ────────────────────────────────────
if [ -f "/etc/freeradius/3.0/clients.conf" ]; then
    chmod 664 /etc/freeradius/3.0/clients.conf
    ok "FreeRADIUS clients.conf permissions set"
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo "========================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "========================================"
echo ""
echo "  CRM running at: http://$SERVER_IP:8000"
echo "  Login: admin / admin123"
echo ""
echo "  Change the admin password after first login!"
echo ""
