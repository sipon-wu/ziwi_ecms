import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15, allow_agent=False, key_filename=None)

cmds = [
    # 检查 SSL 证书是否覆盖 ecms.ziwi.cn
    'openssl x509 -in /etc/nginx/ssl/ziwi.cn.crt -noout -text 2>/dev/null | grep -A5 "Subject Alternative Name" || echo "no SAN found"',
    'openssl x509 -in /etc/nginx/ssl/ziwi.cn.crt -noout -subject -issuer 2>/dev/null',
    # 检查 DNS 解析
    'nslookup ecms.ziwi.cn 8.8.8.8 2>/dev/null || host ecms.ziwi.cn 2>/dev/null || echo "DNS not configured"',
    'dig ecms.ziwi.cn +short 2>/dev/null || echo "dig not available"',
    # 检查 nginx 是否真的监听 443 且配置加载
    'nginx -T 2>/dev/null | grep -c "ecms.ziwi.cn"',
    'netstat -tlnp | grep :443 || ss -tlnp | grep :443',
    # 尝试本地访问 HTTPS
    'curl -sk -o /dev/null -w "%{http_code}" https://localhost/ -H "Host: ecms.ziwi.cn" 2>/dev/null || echo "curl failed"',
]

for cmd in cmds:
    print(f'=== {cmd} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out[:400])
    if err: print('ERR:', err[:200])

ssh.close()
print('Done.')
