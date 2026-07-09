import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15, allow_agent=False, key_filename=None)

cmds = [
    'curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/docs',
    'curl -s -o /dev/null -w "%{http_code}" https://ecms.ziwi.cn/ || echo " (may need DNS)"',
    'curl -s -H "Host: ecms.ziwi.cn" http://localhost/ | head -20',
    'ls /var/www/demo/ecms/ | head -10',
    'nginx -T 2>/dev/null | grep -A5 "ecms.ziwi.cn" | head -20',
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
