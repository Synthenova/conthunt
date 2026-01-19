#!/bin/bash
# Setup script for Cloud SQL Proxy + PgBouncer for conthunt-prod
# Run this on the pgbouncer-vm

set -e

echo "=== Step 1: Install Cloud SQL Proxy if needed ==="
if ! command -v cloud-sql-proxy &> /dev/null; then
    echo "Installing cloud-sql-proxy..."
    curl -o /tmp/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.3/cloud-sql-proxy.linux.amd64
    chmod +x /tmp/cloud-sql-proxy
    sudo mv /tmp/cloud-sql-proxy /usr/local/bin/
    echo "✓ Installed cloud-sql-proxy"
else
    echo "✓ cloud-sql-proxy already installed"
fi

echo ""
echo "=== Step 2: Create systemd service for Cloud SQL Proxy (prod) ==="
sudo tee /etc/systemd/system/cloud-sql-proxy-prod.service > /dev/null <<'EOF'
[Unit]
Description=Cloud SQL Proxy for conthunt-prod
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloud-sql-proxy --port 5433 conthunt-prod:us-central1:conthunt-prod
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cloud-sql-proxy-prod
sudo systemctl start cloud-sql-proxy-prod
echo "✓ Cloud SQL Proxy service created and started (listening on localhost:5433)"

echo ""
echo "=== Step 3: Test Cloud SQL Proxy connection ==="
sleep 2
if nc -z localhost 5433; then
    echo "✓ Cloud SQL Proxy is accepting connections on port 5433"
else
    echo "✗ Cloud SQL Proxy not responding on port 5433"
    sudo systemctl status cloud-sql-proxy-prod
    exit 1
fi

echo ""
echo "=== Step 4: Update PgBouncer configuration ==="

# Backup existing config
sudo cp /etc/pgbouncer/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini.backup.$(date +%Y%m%d%H%M%S)

# Check if prod database already exists in config
if grep -q "postgres_prod" /etc/pgbouncer/pgbouncer.ini; then
    echo "✓ postgres_prod already configured in pgbouncer.ini"
else
    echo "Adding postgres_prod to pgbouncer.ini..."
    
    # Add production database entry after [databases] section
    sudo sed -i '/^\[databases\]/a postgres_prod = host=127.0.0.1 port=5433 dbname=postgres' /etc/pgbouncer/pgbouncer.ini
    
    echo "✓ Added postgres_prod database entry"
fi

echo ""
echo "=== Step 5: Add production user to userlist.txt ==="
echo "You need to add the production database user credentials."
echo ""
echo "Current userlist.txt content:"
sudo cat /etc/pgbouncer/userlist.txt
echo ""
echo "To add the prod user, run:"
echo '  echo "\"conthunt_service\" \"md5<hash>\"" | sudo tee -a /etc/pgbouncer/userlist.txt'
echo ""
echo "Or for SCRAM-SHA-256 (if using that auth), check postgres for the password hash."
echo ""

echo "=== Step 6: Restart PgBouncer ==="
sudo systemctl restart pgbouncer
echo "✓ PgBouncer restarted"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Connection info for Cloud Run (prod):"
echo "  Host: <pgbouncer-vm-internal-ip>"
echo "  Port: 6432"
echo "  Database: postgres_prod"
echo "  Schema: conthunt"
echo ""
echo "Test connection with:"
echo "  psql -h localhost -p 6432 -U conthunt_service -d postgres_prod"
echo ""
