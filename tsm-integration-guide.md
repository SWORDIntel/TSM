# TSM COMPLETE INTEGRATION GUIDE

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Prerequisites & Requirements](#prerequisites--requirements)
3. [Phase 1: Core Desktop Setup](#phase-1-core-desktop-setup)
4. [Phase 2: YubiKey Integration](#phase-2-yubikey-integration)
5. [Phase 3: Mobile App Deployment](#phase-3-mobile-app-deployment)
6. [Phase 4: Backend Services](#phase-4-backend-services)
7. [Phase 5: Security Hardening](#phase-5-security-hardening)
8. [Testing & Validation](#testing--validation)
9. [Production Deployment](#production-deployment)
10. [Maintenance & Updates](#maintenance--updates)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TSM ECOSYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   Desktop    │     │   Mobile     │     │   YubiKey    │   │
│  │   Client     │◄────┤   Apps       │────►│   Hardware   │   │
│  │  (Python)    │     │ (iOS/Android)│     │   Security   │   │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘   │
│         │                     │                     │            │
│         ▼                     ▼                     ▼            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    gRPC API Server                        │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │   │
│  │  │ Auth   │  │Session │  │Crypto  │  │Backup  │        │   │
│  │  │Service │  │Manager │  │Module  │  │Service │        │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘        │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                     │                     │            │
│         ▼                     ▼                     ▼            │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │   SQLite     │     │  Encrypted   │     │    Audit     │   │
│  │   Database   │     │   Storage    │     │     Logs     │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites & Requirements

### Hardware Requirements
- **Desktop**: 4GB+ RAM, 10GB storage, USB-A/USB-C ports
- **Mobile**: Android 8.0+ or iOS 14+, NFC capability
- **YubiKey**: YubiKey 5 Series (5C, 5Ci, or 5 NFC recommended)

### Software Requirements
```bash
# Desktop
- Python 3.9+
- Git
- OpenSSL 1.1.1+

# Development Tools
- Docker & Docker Compose
- Android Studio (for Android app)
- Xcode 14+ (for iOS app)
- Protocol Buffers compiler (protoc)
```

### Network Requirements
- Local network for P2P sync
- Optional: Static IP or dynamic DNS for remote access
- Firewall rules for gRPC (port 50051)

---

## Phase 1: Core Desktop Setup

### 1.1 Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-org/tsm-advanced.git
cd tsm-advanced

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 1.2 Initial Configuration

Create `config/tsm.yaml`:

```yaml
# TSM Configuration
general:
  backup_root: "~/telegram_backups"
  tdata_dir: "~/.local/share/TelegramDesktop/tdata"
  max_backups: 10
  backup_age_days: 30

security:
  encryption_enabled: true
  require_yubikey: false  # Enable after YubiKey setup
  auto_lock_minutes: 15
  audit_log_enabled: true

mobile:
  enabled: false  # Enable after mobile setup
  listen_address: "0.0.0.0:50051"
  tls_cert: "certs/server.crt"
  tls_key: "certs/server.key"

performance:
  thread_workers: 4
  compression_level: 6
  verify_after_copy: true
```

### 1.3 Generate Certificates

```bash
# Create certificates directory
mkdir -p certs

# Generate CA certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout certs/ca.key -out certs/ca.crt \
  -days 3650 -subj "/CN=TSM Root CA"

# Generate server certificate
openssl req -newkey rsa:4096 -nodes \
  -keyout certs/server.key -out certs/server.csr \
  -subj "/CN=tsm.local"

openssl x509 -req -in certs/server.csr -CA certs/ca.crt \
  -CAkey certs/ca.key -CAcreateserial -out certs/server.crt \
  -days 365 -extensions SAN \
  -extfile <(echo "[SAN]\nsubjectAltName=DNS:tsm.local,DNS:*.tsm.local,IP:127.0.0.1")

# Generate client certificates for mobile
./scripts/generate_mobile_certs.sh
```

### 1.4 Database Initialization

```bash
# Initialize database
python -m tsm.database.init

# Run migrations
alembic upgrade head

# Verify database
python -m tsm.database.verify
```

### 1.5 Test Basic Operations

```python
# test_basic.py
from tsm_enhanced import TelegramSessionManager, load_config

# Load configuration
config = load_config("config/tsm.yaml")
tsm = TelegramSessionManager(config)

# List sessions
sessions = tsm.find_sessions()
print(f"Found {len(sessions)} sessions")

# Create test backup
if tsm.tdata_dir.exists():
    backup = tsm.backup_active_session(notes="Test backup")
    print(f"Created backup: {backup.name}")
```

---

## Phase 2: YubiKey Integration

### 2.1 Install YubiKey Dependencies

```bash
# Desktop dependencies
pip install yubikey-manager fido2 cryptography

# System dependencies (Ubuntu/Debian)
sudo apt-get install pcscd libpcsclite-dev swig

# macOS
brew install libusb swig

# Windows: Install YubiKey Manager from Yubico website
```

### 2.2 Configure YubiKey Access

Create `config/yubikey.yaml`:

```yaml
yubikey:
  require_presence: true
  require_touch: true
  modes:
    - fido2_resident
    - piv_encryption
    - oath_totp
  
  piv:
    slot: SIGNATURE
    key_type: RSA2048
    pin_retries: 3
    touch_policy: DEFAULT
  
  fido2:
    rp_id: "tsm.local"
    user_verification: required
    resident_key: true
  
  oath:
    issuer: "TSM"
    hash_algorithm: SHA256
    digits: 6
    period: 30
```

### 2.3 Initialize YubiKey

```python
# yubikey_setup.py
import asyncio
from tsm_yubikey import TSMYubiKeyIntegration, YubiKeyConfig, YubiKeyMode

async def setup_yubikey():
    # Create configuration
    config = YubiKeyConfig(
        mode=YubiKeyMode.PIV_ENCRYPTION,
        require_pin=True,
        require_touch=True
    )
    
    # Initialize integration
    integration = TSMYubiKeyIntegration(tsm, config)
    
    # Setup YubiKey
    result = await integration.setup_yubikey_auth("your_username")
    print(f"Setup complete: {result}")
    
    # Test authentication
    authenticated = await integration.require_authentication("test_operation")
    print(f"Authentication: {'Success' if authenticated else 'Failed'}")

asyncio.run(setup_yubikey())
```

### 2.4 Enable YubiKey Protection

Update `config/tsm.yaml`:

```yaml
security:
  require_yubikey: true
  yubikey_config: "config/yubikey.yaml"
```

---

## Phase 3: Mobile App Deployment

### 3.1 Build Android App

```bash
cd mobile/android

# Configure signing keys
cat > keystore.properties << EOF
storeFile=release.keystore
storePassword=$KEYSTORE_PASSWORD
keyAlias=tsm
keyPassword=$KEY_PASSWORD
EOF

# Generate keystore
keytool -genkey -v -keystore release.keystore -alias tsm \
  -keyalg RSA -keysize 2048 -validity 10000

# Build release APK
./gradlew assembleRelease

# Or build App Bundle for Play Store
./gradlew bundleRelease
```

### 3.2 Build iOS App

```bash
cd mobile/ios

# Install dependencies
pod install

# Open in Xcode
open TSM.xcworkspace

# Configure signing in Xcode:
# 1. Select your team
# 2. Set bundle identifier
# 3. Configure capabilities (NFC, Keychain)

# Build archive
xcodebuild -workspace TSM.xcworkspace \
  -scheme TSM -configuration Release \
  -archivePath build/TSM.xcarchive archive

# Export IPA
xcodebuild -exportArchive \
  -archivePath build/TSM.xcarchive \
  -exportPath build/TSM.ipa \
  -exportOptionsPlist ExportOptions.plist
```

### 3.3 Deploy Mobile Server

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tsm-server:
    build: .
    ports:
      - "50051:50051"
    volumes:
      - ./data:/app/data
      - ./certs:/app/certs
      - ./config:/app/config
    environment:
      - TSM_ENV=production
      - TSM_MOBILE_ENABLED=true
    restart: always
    networks:
      - tsm-network

  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data
    networks:
      - tsm-network

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - tsm-network

volumes:
  redis-data:
  prometheus-data:

networks:
  tsm-network:
    driver: bridge
```

Deploy:

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f tsm-server

# Verify gRPC endpoint
grpcurl -plaintext localhost:50051 list
```

---

## Phase 4: Backend Services

### 4.1 Setup Systemd Service (Linux)

Create `/etc/systemd/system/tsm.service`:

```ini
[Unit]
Description=Telegram Session Manager
After=network.target

[Service]
Type=simple
User=tsm
Group=tsm
WorkingDirectory=/opt/tsm
Environment="PATH=/opt/tsm/venv/bin"
ExecStart=/opt/tsm/venv/bin/python -m tsm.server
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/tsm/data

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tsm
sudo systemctl start tsm
sudo systemctl status tsm
```

### 4.2 Setup Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/tsm
server {
    listen 443 ssl http2;
    server_name tsm.local;

    ssl_certificate /opt/tsm/certs/server.crt;
    ssl_certificate_key /opt/tsm/certs/server.key;
    ssl_client_certificate /opt/tsm/certs/ca.crt;
    ssl_verify_client on;

    location / {
        grpc_pass grpc://localhost:50051;
        grpc_set_header X-Real-IP $remote_addr;
        
        # Security headers
        add_header X-Frame-Options "DENY";
        add_header X-Content-Type-Options "nosniff";
        add_header X-XSS-Protection "1; mode=block";
    }
}
```

### 4.3 Setup Monitoring

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'tsm-server'
    static_configs:
      - targets: ['tsm-server:8080']
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

Create Grafana dashboard:

```bash
# Import dashboard
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/tsm-dashboard.json
```

---

## Phase 5: Security Hardening

### 5.1 Network Security

```bash
# UFW firewall rules
sudo ufw allow 22/tcp          # SSH
sudo ufw allow 443/tcp         # HTTPS/gRPC
sudo ufw allow from 192.168.1.0/24 to any port 50051  # Local gRPC
sudo ufw enable

# Fail2ban for brute force protection
sudo apt-get install fail2ban
sudo cp config/fail2ban/tsm.conf /etc/fail2ban/filter.d/
sudo systemctl restart fail2ban
```

### 5.2 Application Security

Create `security/hardening.sh`:

```bash
#!/bin/bash

# Set secure permissions
chmod 700 /opt/tsm/data
chmod 600 /opt/tsm/config/*
chmod 400 /opt/tsm/certs/*.key

# Enable SELinux/AppArmor profile
sudo aa-enforce /etc/apparmor.d/tsm

# Configure audit logging
auditctl -w /opt/tsm/data -p wa -k tsm_data_access
auditctl -w /opt/tsm/config -p r -k tsm_config_read

# Secure sysctl settings
cat >> /etc/sysctl.conf << EOF
# TSM Security Settings
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
EOF

sysctl -p
```

### 5.3 YubiKey Policies

```python
# security/policies.py
from enum import Enum
from typing import List

class SecurityPolicy:
    """Security policies for TSM operations"""
    
    OPERATIONS_REQUIRING_YUBIKEY = [
        "switch_session",
        "decrypt_backup",
        "emergency_wipe",
        "export_session",
        "modify_security_settings"
    ]
    
    OPERATIONS_REQUIRING_TOUCH = [
        "emergency_wipe",
        "export_session"
    ]
    
    OPERATIONS_REQUIRING_TOTP = [
        "emergency_wipe",
        "disable_yubikey"
    ]
    
    @classmethod
    def verify_operation(cls, operation: str, auth_methods: List[str]) -> bool:
        """Verify if operation is allowed with given auth methods"""
        if operation in cls.OPERATIONS_REQUIRING_YUBIKEY:
            if "yubikey" not in auth_methods:
                return False
                
        if operation in cls.OPERATIONS_REQUIRING_TOUCH:
            if "yubikey_touch" not in auth_methods:
                return False
                
        if operation in cls.OPERATIONS_REQUIRING_TOTP:
            if "totp" not in auth_methods:
                return False
                
        return True
```

---

## Testing & Validation

### 6.1 Unit Tests

```bash
# Run all tests
pytest tests/ -v --cov=tsm --cov-report=html

# Run specific test categories
pytest tests/test_security.py -v
pytest tests/test_yubikey.py -v
pytest tests/test_mobile.py -v
```

### 6.2 Integration Tests

```python
# tests/integration/test_full_flow.py
import asyncio
import pytest
from tsm_enhanced import TelegramSessionManager
from tsm_yubikey import TSMYubiKeyIntegration
from tsm_mobile import MobileIntegrationServer

@pytest.mark.asyncio
async def test_full_authentication_flow():
    """Test complete authentication flow with YubiKey"""
    # Setup
    tsm = TelegramSessionManager(test_config)
    yubikey = TSMYubiKeyIntegration(tsm, yubikey_config)
    
    # Test YubiKey authentication
    assert await yubikey.require_authentication("test_operation")
    
    # Test session switch with YubiKey
    assert await yubikey.yubikey_protected_switch("test_session")
    
    # Test mobile authentication
    mobile_server = MobileIntegrationServer(tsm, mobile_config)
    auth_result = await mobile_server.authenticate_mobile_client("test_device")
    assert auth_result.success
```

### 6.3 Security Tests

```bash
# Run security scanner
python -m security.scanner --target localhost:50051

# Check for vulnerabilities
safety check
bandit -r tsm/

# Test YubiKey policies
python -m tests.security.test_yubikey_policies
```

### 6.4 Load Testing

```python
# tests/load/test_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test_grpc(num_clients=100, requests_per_client=10):
    """Load test gRPC endpoints"""
    async def client_task(client_id):
        client = TSMNetworkClient()
        await client.connect("localhost", 50051)
        
        for i in range(requests_per_client):
            sessions = await client.list_sessions()
            assert len(sessions) >= 0
            
        await client.disconnect()
    
    start = time.time()
    tasks = [client_task(i) for i in range(num_clients)]
    await asyncio.gather(*tasks)
    duration = time.time() - start
    
    print(f"Processed {num_clients * requests_per_client} requests in {duration:.2f}s")
    print(f"RPS: {(num_clients * requests_per_client) / duration:.2f}")

asyncio.run(load_test_grpc())
```

---

## Production Deployment

### 7.1 Pre-deployment Checklist

```markdown
## Pre-deployment Checklist

### Security
- [ ] All certificates generated with proper CN/SAN
- [ ] YubiKey policies configured and tested
- [ ] Firewall rules configured
- [ ] SELinux/AppArmor profiles enabled
- [ ] Audit logging enabled
- [ ] Backup encryption keys secured

### Configuration
- [ ] Production config reviewed
- [ ] Environment variables set
- [ ] Database migrations completed
- [ ] Mobile server endpoints configured

### Testing
- [ ] All unit tests passing
- [ ] Integration tests completed
- [ ] Security scan clean
- [ ] Load testing acceptable
- [ ] Mobile apps tested on real devices

### Documentation
- [ ] User guide updated
- [ ] Admin procedures documented
- [ ] Recovery procedures tested
- [ ] YubiKey enrollment guide ready
```

### 7.2 Deployment Script

Create `deploy/deploy.sh`:

```bash
#!/bin/bash
set -e

# Configuration
DEPLOY_ENV=${1:-production}
DEPLOY_DIR="/opt/tsm"
BACKUP_DIR="/opt/tsm-backups"

echo "Deploying TSM to $DEPLOY_ENV..."

# Backup current deployment
if [ -d "$DEPLOY_DIR" ]; then
    echo "Backing up current deployment..."
    tar -czf "$BACKUP_DIR/tsm-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$DEPLOY_DIR" .
fi

# Stop services
sudo systemctl stop tsm tsm-mobile || true

# Deploy new version
echo "Deploying new version..."
rsync -av --delete \
    --exclude='data/' \
    --exclude='logs/' \
    --exclude='venv/' \
    . "$DEPLOY_DIR/"

# Update dependencies
cd "$DEPLOY_DIR"
source venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Update permissions
sudo chown -R tsm:tsm "$DEPLOY_DIR"
chmod 700 "$DEPLOY_DIR/data"

# Start services
sudo systemctl start tsm tsm-mobile

# Health check
sleep 5
if systemctl is-active --quiet tsm; then
    echo "Deployment successful!"
else
    echo "Deployment failed! Check logs."
    exit 1
fi
```

### 7.3 Mobile App Distribution

**Android**:
```bash
# Sign APK
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
    -keystore release.keystore app-release-unsigned.apk tsm

# Align APK
zipalign -v 4 app-release-unsigned.apk TSM.apk

# Verify
apksigner verify TSM.apk

# Upload to Play Store or distribute via MDM
```

**iOS**:
```bash
# Upload to App Store Connect
xcrun altool --upload-app \
    --type ios \
    --file TSM.ipa \
    --username "$APPLE_ID" \
    --password "$APP_PASSWORD"

# Or distribute via TestFlight/Enterprise
```

---

## Maintenance & Updates

### 8.1 Regular Maintenance Tasks

Create `maintenance/weekly.sh`:

```bash
#!/bin/bash

# Weekly maintenance script
echo "Starting weekly maintenance..."

# Cleanup old logs
find /opt/tsm/logs -name "*.log" -mtime +30 -delete

# Vacuum database
sqlite3 /opt/tsm/data/sessions.db "VACUUM;"

# Check certificate expiry
openssl x509 -checkend 2592000 -noout -in /opt/tsm/certs/server.crt
if [ $? -eq 1 ]; then
    echo "WARNING: Certificate expires within 30 days!"
fi

# Update YubiKey credential cache
python -m tsm.yubikey.maintenance --cleanup-expired

# Generate report
python -m tsm.reports.weekly > /opt/tsm/reports/weekly-$(date +%Y%m%d).html

echo "Maintenance complete!"
```

### 8.2 Update Procedures

```python
# update/update_manager.py
import subprocess
import sys
from pathlib import Path

class UpdateManager:
    """Manage TSM updates safely"""
    
    def check_updates(self):
        """Check for available updates"""
        # Check GitHub releases
        latest = self.get_latest_release()
        current = self.get_current_version()
        
        if latest > current:
            return {
                "update_available": True,
                "current": current,
                "latest": latest,
                "changelog": self.get_changelog(current, latest)
            }
        return {"update_available": False}
    
    def perform_update(self, version):
        """Perform update with rollback capability"""
        # Create backup
        self.backup_current()
        
        try:
            # Download update
            self.download_update(version)
            
            # Stop services
            subprocess.run(["sudo", "systemctl", "stop", "tsm"])
            
            # Apply update
            self.apply_update(version)
            
            # Run migrations
            self.run_migrations()
            
            # Start services
            subprocess.run(["sudo", "systemctl", "start", "tsm"])
            
            # Verify
            if self.verify_update():
                self.cleanup_backup()
                return True
            else:
                self.rollback()
                return False
                
        except Exception as e:
            print(f"Update failed: {e}")
            self.rollback()
            return False
```

### 8.3 Monitoring & Alerts

Create `monitoring/alerts.yaml`:

```yaml
# Prometheus alert rules
groups:
  - name: tsm_alerts
    rules:
      - alert: TSMServerDown
        expr: up{job="tsm-server"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "TSM Server is down"
          
      - alert: HighErrorRate
        expr: rate(tsm_errors_total[5m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          
      - alert: YubiKeyAuthFailures
        expr: rate(tsm_yubikey_auth_failures_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High YubiKey authentication failure rate"
          
      - alert: DiskSpaceLow
        expr: disk_free_percent{mountpoint="/opt/tsm/data"} < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on TSM data volume"
```

---

## Complete Integration Example

Here's a complete example showing all components working together:

```python
# example/full_integration.py
import asyncio
from pathlib import Path

async def demonstrate_full_integration():
    """Demonstrate complete TSM integration"""
    
    # 1. Initialize core TSM
    from tsm_enhanced import TelegramSessionManager, load_config
    config = load_config("config/tsm.yaml")
    tsm = TelegramSessionManager(config)
    
    # 2. Setup YubiKey integration
    from tsm_yubikey import TSMYubiKeyIntegration, YubiKeyConfig
    yk_config = YubiKeyConfig.from_file("config/yubikey.yaml")
    yubikey = TSMYubiKeyIntegration(tsm, yk_config)
    
    # 3. Start mobile server
    from tsm_mobile import MobileIntegrationServer
    mobile_server = MobileIntegrationServer(tsm, config)
    mobile_task = asyncio.create_task(mobile_server.start())
    
    # 4. Demonstrate YubiKey-protected operation
    print("=== YubiKey Protected Session Switch ===")
    if await yubikey.require_authentication("switch_session"):
        success = await yubikey.yubikey_protected_switch("telegram_work")
        print(f"Switch result: {'Success' if success else 'Failed'}")
    
    # 5. Create encrypted backup
    print("\n=== Creating Encrypted Backup ===")
    pin = input("Enter YubiKey PIN: ")
    session_path = tsm.backup_root / "telegram_work"
    backup_path = tsm.backup_root / "telegram_work_secure.enc"
    yubikey.encrypt_session_backup(session_path, backup_path, pin)
    
    # 6. Mobile client connection simulation
    print("\n=== Mobile Client Test ===")
    from tsm_mobile_client import TSMobileClient
    mobile_client = TSMobileClient()
    await mobile_client.connect("localhost", 50051)
    
    # Authenticate mobile client
    if await mobile_client.authenticate_with_yubikey():
        sessions = await mobile_client.list_sessions()
        print(f"Mobile client sees {len(sessions)} sessions")
    
    # 7. Generate TOTP for verification
    print("\n=== TOTP Verification ===")
    totp_code = yubikey.generate_session_otp(pin)
    print(f"Current TOTP: {totp_code}")
    
    # Cleanup
    mobile_task.cancel()
    await mobile_client.disconnect()

if __name__ == "__main__":
    asyncio.run(demonstrate_full_integration())
```

---

## Troubleshooting Guide

### Common Issues and Solutions

1. **YubiKey Not Detected**
   ```bash
   # Check USB permissions
   sudo usermod -a -G plugdev $USER
   # Restart udev
   sudo udevadm control --reload-rules
   ```

2. **Mobile App Can't Connect**
   ```bash
   # Check firewall
   sudo ufw status
   # Test gRPC endpoint
   grpcurl -plaintext localhost:50051 list
   ```

3. **Certificate Errors**
   ```bash
   # Verify certificate chain
   openssl verify -CAfile certs/ca.crt certs/server.crt
   # Check certificate dates
   openssl x509 -noout -dates -in certs/server.crt
   ```

4. **Database Lock Errors**
   ```bash
   # Check database integrity
   sqlite3 data/sessions.db "PRAGMA integrity_check;"
   # Fix locks
   fuser -k data/sessions.db
   ```

---

## Conclusion

This integration guide provides a complete path from basic TSM installation to a fully integrated, YubiKey-secured, mobile-enabled system. Key points:

1. **Phased Approach**: Build incrementally, test thoroughly
2. **Security First**: YubiKey integration provides hardware-backed security
3. **Mobile Ready**: Full mobile support with secure remote access
4. **Production Grade**: Monitoring, logging, and maintenance procedures
5. **Scalable**: Architecture supports future enhancements

Remember to customize configurations for your specific environment and security requirements.

For support and updates, check:
- Documentation: `/docs`
- Issues: GitHub Issues
- Security: `security@tsm.local`