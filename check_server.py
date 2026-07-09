import os
import paramiko, os

host = os.environ.get("SERVER_HOST", "")
user = 'root'
pwd = os.environ.get("SERVER_PASS", "")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pwd, timeout=10)

cmds = [
    'pwd',
    'ls /var/www/ 2>/dev/null || echo "NO /var/www"',
    'ls /usr/share/nginx/html/ 2>/dev/null || echo "NO nginx html"',
    'cat /etc/nginx/nginx.conf 2>/dev/null | grep -A3 "root" | head -20 || echo "no nginx.conf"',
    'find /etc/nginx/sites-enabled/ -type f 2>/dev/null | head -5',
    'ls /www/ 2>/dev/null || echo "NO /www"',
    'df -h / | tail -1',
]

for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    print(f'=== {cmd} ===')
    if out: print(out)
    if err: print('ERR:', err)

ssh.close()
