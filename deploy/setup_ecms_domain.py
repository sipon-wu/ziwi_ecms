import os
"""配置 ecms.ziwi.cn 域名的 Nginx + SSL"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15)

# Read current config
sftp = ssh.open_sftp()
with sftp.open('/etc/nginx/sites-enabled/ziwi.cn', 'r') as f:
    content = f.read().decode('utf-8')

# Fix the HTTP ecms block (lines 64-67 have broken proxy_set_header)
# Also fix try_files missing $uri
old_block = '''    location / {
        try_files  / /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8088/api/;
        proxy_set_header Host ;
        proxy_set_header X-Real-IP ;
        proxy_set_header X-Forwarded-For ;
    }'''

new_block = '''    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8088/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }'''

content = content.replace(old_block, new_block)

# Remove the broken HTTPS block we added earlier
idx = content.rfind('# HTTPS server for ecms')
if idx >= 0:
    content = content[:idx].rstrip() + '\n'

# Add clean HTTPS block
https_block = '''
# HTTPS server for ecms.ziwi.cn
server {
    listen 443 ssl http2;
    server_name ecms.ziwi.cn;

    ssl_certificate /etc/nginx/ssl/ecms.ziwi.cn.crt;
    ssl_certificate_key /etc/nginx/ssl/ecms.ziwi.cn.key;

    root /var/www/demo/ecms;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8088/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
'''

content = content.rstrip() + https_block + '\n'

# Write back
with sftp.open('/etc/nginx/sites-enabled/ziwi.cn', 'w') as f:
    f.write(content.encode('utf-8'))
sftp.close()

# Test and reload
stdin, stdout, stderr = ssh.exec_command('nginx -t 2>&1 && nginx -s reload 2>&1')
print(stdout.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" https://ecms.ziwi.cn/')
print('ecms HTTPS:', stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('curl -sk https://ecms.ziwi.cn/ | head -c 100')
print('ecms content:', stdout.read().decode()[:100])

stdin, stdout, stderr = ssh.exec_command('curl -sk https://ecms.ziwi.cn/api/heartbeat')
print('ecms API:', stdout.read().decode()[:80])

# Auto-renew cert
stdin, stdout, stderr = ssh.exec_command('bash /root/.acme.sh/acme.sh --list 2>/dev/null | grep ecms')
print('cert status:', stdout.read().decode().strip())

ssh.close()
print('\nDone! https://ecms.ziwi.cn/')
