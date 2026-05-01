#!/bin/bash
# NetCRM — Full Setup Script
# Run as root on Ubuntu/Debian: sudo bash setup.sh

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}!${NC} $1"; }
err()   { echo -e "${RED}✗ ERROR:${NC} $1"; exit 1; }
info()  { echo -e "${CYAN}→${NC} $1"; }

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/env"

echo ""
echo -e "${CYAN}========================================"
echo "       NetCRM — Full Setup"
echo -e "========================================${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────
# 1. COLLECT CONFIG
# ─────────────────────────────────────────────────────────────────
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    info "Collecting configuration..."
    echo ""

    read -p "  Server public IP (e.g. 162.217.248.75): " SERVER_IP
    [ -z "$SERVER_IP" ] && err "Server IP is required"

    read -s -p "  MySQL root password (for creating radius DB): " MYSQL_ROOT_PASS
    echo ""

    read -p "  FreeRADIUS DB name   [radius]:    " RADIUS_DB;    RADIUS_DB=${RADIUS_DB:-radius}
    read -p "  FreeRADIUS DB user   [radius]:    " RADIUS_USER;  RADIUS_USER=${RADIUS_USER:-radius}
    read -s -p "  FreeRADIUS DB password:           " RADIUS_PASS;  echo ""
    [ -z "$RADIUS_PASS" ] && err "RADIUS DB password is required"
    read -p "  FreeRADIUS NAS secret [NetCRM@ISP]: " RADIUS_SECRET
    RADIUS_SECRET=${RADIUS_SECRET:-NetCRM@ISP}

    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

    cat > "$ENV_FILE" <<ENVEOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP

# FreeRADIUS
RADIUS_ENABLED=True
RADIUS_CLIENTS_CONF=/etc/freeradius/3.0/clients.conf
RADIUS_DEFAULT_SECRET=$RADIUS_SECRET
RADIUS_DB_HOST=127.0.0.1
RADIUS_DB_PORT=3306
RADIUS_DB_NAME=$RADIUS_DB
RADIUS_DB_USER=$RADIUS_USER
RADIUS_DB_PASSWORD=$RADIUS_PASS
ENVEOF
    ok ".env created"
else
    ok ".env already exists — loading values"
    source <(grep -v '^#' "$ENV_FILE" | sed 's/^/export /')
    SERVER_IP=$(echo "$ALLOWED_HOSTS" | tr ',' '\n' | grep -v localhost | grep -v '127.0.0.1' | head -1)
    RADIUS_DB=${RADIUS_DB_NAME:-radius}
    RADIUS_USER=${RADIUS_DB_USER:-radius}
    RADIUS_PASS=${RADIUS_DB_PASSWORD:-}
    RADIUS_SECRET=${RADIUS_DEFAULT_SECRET:-NetCRM@ISP}
fi

# ─────────────────────────────────────────────────────────────────
# 2. SYSTEM PACKAGES
# ─────────────────────────────────────────────────────────────────
info "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv git curl \
    mariadb-server mariadb-client libmariadb-dev pkg-config \
    freeradius freeradius-mysql > /dev/null
ok "System packages installed"

# ─────────────────────────────────────────────────────────────────
# 3. MARIADB — create radius database & user
# ─────────────────────────────────────────────────────────────────
info "Setting up FreeRADIUS MySQL database..."
systemctl start mariadb

mysql -u root ${MYSQL_ROOT_PASS:+-p"$MYSQL_ROOT_PASS"} <<SQL 2>/dev/null || true
CREATE DATABASE IF NOT EXISTS \`$RADIUS_DB\`;
CREATE USER IF NOT EXISTS '$RADIUS_USER'@'localhost' IDENTIFIED BY '$RADIUS_PASS';
CREATE USER IF NOT EXISTS '$RADIUS_USER'@'127.0.0.1' IDENTIFIED BY '$RADIUS_PASS';
GRANT ALL PRIVILEGES ON \`$RADIUS_DB\`.* TO '$RADIUS_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$RADIUS_DB\`.* TO '$RADIUS_USER'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

# Import schema (only if radcheck table doesn't exist)
TABLE_EXISTS=$(mysql -u "$RADIUS_USER" -p"$RADIUS_PASS" "$RADIUS_DB" -sse \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$RADIUS_DB' AND table_name='radcheck';" 2>/dev/null || echo "0")
if [ "$TABLE_EXISTS" = "0" ]; then
    mysql -u "$RADIUS_USER" -p"$RADIUS_PASS" "$RADIUS_DB" \
        < /etc/freeradius/3.0/mods-config/sql/main/mysql/schema.sql
    ok "FreeRADIUS schema imported"
else
    ok "FreeRADIUS schema already exists"
fi

# ─────────────────────────────────────────────────────────────────
# 4. FREERADIUS — configure SQL module
# ─────────────────────────────────────────────────────────────────
info "Configuring FreeRADIUS SQL module..."
SQL_MOD="/etc/freeradius/3.0/mods-available/sql"

# Set dialect and DB credentials
sed -i "s/dialect = .*/dialect = \"mysql\"/" "$SQL_MOD"
sed -i "s/driver = .*/driver = \"rlm_sql_mysql\"/" "$SQL_MOD"
sed -i "s/.*login = .*/        login = \"$RADIUS_USER\"/" "$SQL_MOD"
sed -i "s/.*password = .*/        password = \"$RADIUS_PASS\"/" "$SQL_MOD"
sed -i "s/.*radius_db = .*/        radius_db = \"$RADIUS_DB\"/" "$SQL_MOD"

# Enable SQL module if not already
[ ! -L /etc/freeradius/3.0/mods-enabled/sql ] && \
    ln -s ../mods-available/sql /etc/freeradius/3.0/mods-enabled/sql
ok "SQL module configured"

# ─────────────────────────────────────────────────────────────────
# 5. FREERADIUS — fix queries.conf (nasipaddress column issue)
# ─────────────────────────────────────────────────────────────────
info "Fixing FreeRADIUS queries.conf..."
QUERIES="/etc/freeradius/3.0/mods-config/sql/main/mysql/queries.conf"
python3 << PYEOF
f = '$QUERIES'
lines = open(f).readlines()

# Fix the broken inner post-auth block (incomplete query with empty lines)
# Find pattern: post-auth block followed by empty lines then 'start {'
i = 0
while i < len(lines):
    if 'post-auth {' in lines[i] and i+3 < len(lines):
        # Check if next few lines are incomplete (no VALUES, just column list)
        chunk = ''.join(lines[i:i+6])
        if 'nasipaddress' in chunk and 'VALUES' not in chunk:
            # Find end of this broken block
            j = i + 1
            while j < len(lines) and lines[j].strip() not in ['', 'start {', '\t\tstart {']:
                j += 1
            lines[i:j+2] = ['\t\tpost-auth {\n', '\t\t}\n', '\n']
            break
    i += 1

# Fix the main post-auth query at the bottom
new_lines = []
skip = False
for idx, line in enumerate(lines):
    if 'INSERT INTO \${..postauth_table}' in line and 'nasipaddress' in ''.join(lines[max(0,idx-1):idx+5]):
        # Find the start of this query block (go back to find 'query = "')
        start = idx
        while start > 0 and 'query = "' not in lines[start]:
            start -= 1
        # Find the end (closing ')')
        end = idx
        while end < len(lines) and not lines[end].strip().endswith(')"'):
            end += 1
        new_lines = lines[:start]
        new_lines.append('        query = "\\\\\\n')
        new_lines.append('                INSERT INTO \${..postauth_table} \\\\\\n')
        new_lines.append('                        (username, pass, reply, authdate) \\\\\\n')
        new_lines.append('                VALUES ( \\\\\\n')
        new_lines.append("                        '%{SQL-User-Name}', \\\\\\n")
        new_lines.append("                        '%{%{User-Password}:-%{Chap-Password}}', \\\\\\n")
        new_lines.append("                        '%{reply:Packet-Type}', \\\\\\n")
        new_lines.append("                        '%S.%M')\"\\n")
        new_lines += lines[end+1:]
        break

if new_lines:
    open(f, 'w').writelines(new_lines)

# Ensure file ends with newline
content = open(f).read()
if not content.endswith('\\n'):
    open(f, 'a').write('\\n')

print('queries.conf fixed')
PYEOF
ok "queries.conf fixed"

# ─────────────────────────────────────────────────────────────────
# 6. FREERADIUS — default virtual server
# ─────────────────────────────────────────────────────────────────
info "Configuring FreeRADIUS default site..."
cat > /etc/freeradius/3.0/sites-available/default <<'SITEEOF'
listen {
    type = auth
    ipaddr = *
    port = 1812
}

listen {
    type = acct
    ipaddr = *
    port = 1813
}

server default {

authorize {
    preprocess
    chap
    mschap
    suffix
    eap {
        ok = return
    }
    files
    sql
    pap
}

authenticate {
    Auth-Type PAP {
        pap
    }
    Auth-Type CHAP {
        chap
    }
    Auth-Type MS-CHAP {
        mschap
    }
    eap
}

post-auth {
    sql
    Post-Auth-Type REJECT {
        attr_filter.access_reject
    }
}

accounting {
    detail
    sql
}

}
SITEEOF
ok "Default site configured"

# ─────────────────────────────────────────────────────────────────
# 7. FREERADIUS — clients.conf (add localhost)
# ─────────────────────────────────────────────────────────────────
info "Configuring FreeRADIUS clients..."
CLIENTS="/etc/freeradius/3.0/clients.conf"
# Ensure localhost client exists with correct secret
if ! grep -q "client localhost" "$CLIENTS"; then
cat >> "$CLIENTS" <<CLIENTEOF

client localhost {
    ipaddr  = 127.0.0.1
    secret  = $RADIUS_SECRET
    nastype = other
}
CLIENTEOF
fi
# Set permissions so CRM can write to it
chmod 664 "$CLIENTS"
chown freerad:root "$CLIENTS" 2>/dev/null || true
ok "clients.conf configured"

# ─────────────────────────────────────────────────────────────────
# 8. START FREERADIUS
# ─────────────────────────────────────────────────────────────────
info "Starting FreeRADIUS..."
pkill freeradius 2>/dev/null || true
sleep 1
systemctl enable freeradius > /dev/null
systemctl start freeradius
sleep 2
systemctl is-active --quiet freeradius && ok "FreeRADIUS running" || warn "FreeRADIUS may have failed — run: freeradius -X"

# ─────────────────────────────────────────────────────────────────
# 9. PYTHON VIRTUALENV + DEPS
# ─────────────────────────────────────────────────────────────────
info "Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install -q -r "$PROJECT_DIR/requirements.txt"
pip install -q gunicorn
ok "Python packages installed"

# ─────────────────────────────────────────────────────────────────
# 10. DJANGO — migrations + static files
# ─────────────────────────────────────────────────────────────────
info "Running Django migrations..."
cd "$PROJECT_DIR"
python manage.py migrate --run-syncdb > /dev/null
ok "Migrations applied"

info "Collecting static files..."
python manage.py collectstatic --noinput > /dev/null
ok "Static files collected"

# ─────────────────────────────────────────────────────────────────
# 11. SUPERUSER
# ─────────────────────────────────────────────────────────────────
echo ""
read -p "→ Create admin superuser? (yes/no) [yes]: " CREATE_SU
CREATE_SU=${CREATE_SU:-yes}
if [ "$CREATE_SU" = "yes" ]; then
    python manage.py shell -c "
from accounts.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@netcrm.local', 'admin123')
    print('  Superuser created: admin / admin123')
else:
    print('  Superuser already exists')
"
fi

# ─────────────────────────────────────────────────────────────────
# 12. CRON — expire connections at midnight
# ─────────────────────────────────────────────────────────────────
CRON_CMD="0 0 * * * cd $PROJECT_DIR && $VENV_DIR/bin/python manage.py expire_connections >> $PROJECT_DIR/logs/expiry.log 2>&1"
( crontab -l 2>/dev/null | grep -v "expire_connections"; echo "$CRON_CMD" ) | crontab -
ok "Cron job set (expire at midnight)"

# ─────────────────────────────────────────────────────────────────
# 13. GUNICORN systemd service
# ─────────────────────────────────────────────────────────────────
info "Setting up NetCRM systemd service..."
cat > /etc/systemd/system/netcrm.service <<SVCEOF
[Unit]
Description=NetCRM Gunicorn
After=network.target mariadb.service

[Service]
User=root
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/gunicorn isp_crm.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable netcrm > /dev/null
systemctl restart netcrm
sleep 2
systemctl is-active --quiet netcrm && ok "NetCRM service running on port 8000" || warn "NetCRM service may have failed — check: journalctl -u netcrm"

# ─────────────────────────────────────────────────────────────────
# 14. FIREWALL
# ─────────────────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
    ufw allow 8000/tcp > /dev/null 2>&1 || true
    ufw allow 1812/udp > /dev/null 2>&1 || true
    ufw allow 1813/udp > /dev/null 2>&1 || true
    ok "Firewall rules added (8000, 1812, 1813)"
fi

# ─────────────────────────────────────────────────────────────────
# DONE
# ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}========================================"
echo "       Setup Complete!"
echo -e "========================================${NC}"
echo ""
echo -e "  CRM URL   : ${CYAN}http://$SERVER_IP:8000${NC}"
echo "  Login     : admin / admin123"
echo ""
echo -e "  RADIUS    : ${CYAN}$SERVER_IP:1812${NC}"
echo "  NAS Secret: $RADIUS_SECRET"
echo ""
echo -e "${YELLOW}  → Change admin password after first login!"
echo -e "  → Add your MikroTik routers in Network → Devices${NC}"
echo ""
