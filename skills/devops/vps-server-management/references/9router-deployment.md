# 9Router Deployment on VPS

## Docker Container Setup
```bash
# Pull image
docker pull decolua/9router:latest

# Run with custom API key secret and persistent data
docker run -d --name 9router --restart unless-stopped \
  -p 20128:20128 \
  -e INITIAL_PASSWORD=your_password \
  -e API_KEY_SECRET=your_custom_secret \
  -v /root/9router-data:/app/data \
  decolua/9router:latest
```

## Default Login Credentials
**Default password is `123456`** (found in source code `/app/.next/server/app/login/page.js`).

Login page shows hint: "Default password is `123456`" and "Forgot password? Open `9router` CLI on the host → `Settings` → `Reset Password to Default`."

**If password changed and forgotten:**
- **API endpoint** (local only, requires CLI token): `POST /api/auth/reset-password`
- Returns 403 "Local only: CLI token required" from external access
- Must run `9router settings reset-password` on host (CLI not in container PATH)

## API Key Generation (Critical)
9Router stores keys in SQLite (`/root/9router-data/db/data.sqlite`). Dashboard API returns truncated keys. Get full key:
```bash
# 1. Login and create key via API
curl -c cookies.txt -X POST http://localhost:20128/api/auth/login \
  -H 'Content-Type: application/json' -d '{"password":"your_password"}'
curl -b cookies.txt -X POST http://localhost:20128/api/keys \
  -H 'Content-Type: application/json' -d '{"name":"hermes"}'

# 2. Full key only visible ONCE in response - copy immediately
# 3. Or query DB directly:
sqlite3 /root/9router-data/db/data.sqlite 'SELECT key FROM apiKeys WHERE name="hermes"'
```

## Connect Free Providers (Dashboard → Providers)
- **Kiro AI**: ~50 credits/month (Claude 4.5, GLM-5, MiniMax)
- **OpenCode Free**: No auth required
- **Vertex AI**: $300 free credits (Gemini models)

## OpenLiteSpeed Reverse Proxy (aaPanel uses OpenLiteSpeed, NOT nginx)
```bash
# 1. Create extprocessor for 9Router
mkdir -p /www/server/panel/vhost/openlitespeed/proxy/9router.smartmillionaire.co.id
cat > /www/server/panel/vhost/openlitespeed/proxy/9router.smartmillionaire.co.id/9router_proxy.conf << 'EOF'
extprocessor 9router_proxy {
  type                    proxy
  address                 http://127.0.0.1:20128
  maxConns                1000
  pcKeepAliveTimeout      600
  initTimeout             600
  retryTimeout            0
  respBuffer              0
}
EOF

# 2. Create rewrite rule
mkdir -p /www/server/panel/vhost/openlitespeed/proxy/9router.smartmillionaire.co.id/urlrewrite
cat > /www/server/panel/vhost/openlitespeed/proxy/9router.smartmillionaire.co.id/urlrewrite/9router_rewrite.conf << 'EOF'
RewriteRule ^/(.*)$ http://9router_proxy/$1 [P,E=Proxy-Host:$host]
EOF

# 3. Restart OpenLiteSpeed
/usr/local/lsws/bin/lswsctrl restart
```

## SSL via Cloudflare DNS Validation (acme.sh)
HTTP validation fails on OpenLiteSpeed (403). Use DNS validation:
```bash
# Install acme.sh
curl https://get.acme.sh | sh -s email=your@email.com

# Set Cloudflare credentials (Zone:DNS:Edit token + Zone ID)
export CF_Token="your_cf_token"
export CF_Zone_ID="your_zone_id"

# Issue cert via DNS validation
~/.acme.sh/acme.sh --issue -d 9router.smartmillionaire.co.id --dns dns_cf --force --server letsencrypt

# Install to aaPanel cert path
~/.acme.sh/acme.sh --install-cert -d 9router.smartmillionaire.co.id --ecc \
  --cert-file /www/server/panel/vhost/cert/9router.smartmillionaire.co.id/fullchain.pem \
  --key-file /www/server/panel/vhost/cert/9router.smartmillionaire.co.id/privkey.pem \
  --fullchain-file /www/server/panel/vhost/cert/9router.smartmillionaire.co.id/fullchain.pem \
  --reloadcmd "/www/server/panel/webserver/sbin/webserver -s reload -c /www/server/panel/webserver/conf/webserver.conf"
```

## aaPanel Site Settings (for proxy-only sites)
- **Database:** None
- **PHP:** Static / None
- **Root:** `/www/wwwroot/9router.smartmillionaire.co.id`

## Connect Free Providers (Dashboard → Providers)
- **Kiro AI**: ~50 credits/month (Claude 4.5, GLM-5, MiniMax)
- **OpenCode Free**: No auth required
- **Vertex AI**: $300 free credits (Gemini models)

## Hermes Config for 9Router
```bash
hermes config set model.base_url "https://9router.smartmillionaire.co.id/v1"
hermes config set model.api_key "sk-xxx...full_key"
hermes config set model.default "kr/claude-sonnet-4.5"
hermes gateway restart
```