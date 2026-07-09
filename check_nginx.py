import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=10)

cmds = [
    'cat /etc/nginx/sites-enabled/ziwi.cn',
    'ls /var/www/html/',
    'cat /etc/nginx/nginx.conf | head -50',
]

for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(f'=== {cmd} ===')
    if out: print(out)
    if err: print('ERR:', err)

ssh.close()
