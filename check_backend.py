import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15, allow_agent=False, key_filename=None)

cmds = [
    'cat /var/www/demo/ecms-backend/backend.log 2>/dev/null | tail -30',
    'ls /var/www/demo/ecms-backend/',
    'python3 --version',
    'which python3',
    'cd /var/www/demo/ecms-backend && python3 -c "import fastapi; print(fastapi.__version__)"',
    'cd /var/www/demo/ecms-backend && python3 main.py 2>&1 &',
    'sleep 2 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/docs',
]

for cmd in cmds:
    print(f'=== {cmd} ===')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out.strip(): print(out.strip()[:500])
    if err.strip(): print('ERR:', err.strip()[:500])

ssh.close()
print('Done.')
