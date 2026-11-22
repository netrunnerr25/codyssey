#!/bin/bash
set -euxo pipefail
dnf install -y nginx
cat > /etc/nginx/conf.d/mission.conf <<'NGINX'
server {
    listen 80 default_server;
    server_name _;
    root /usr/share/nginx/html;
    location / { try_files $uri $uri/ =404; }
    location = /health {
        default_type text/plain;
        return 200 "OK\n";
    }
}
NGINX
# Amazon Linux's packaged default server also listens as default_server.
python3 - <<'PY'
from pathlib import Path
p = Path('/etc/nginx/nginx.conf')
s = p.read_text()
start = s.index('    server {')
depth = 0
for i in range(start, len(s)):
    if s[i] == '{': depth += 1
    elif s[i] == '}':
        depth -= 1
        if depth == 0:
            p.write_text(s[:start] + s[i+1:])
            break
else:
    raise RuntimeError('Cannot locate packaged default server block')
PY
nginx -t
systemctl enable --now nginx
