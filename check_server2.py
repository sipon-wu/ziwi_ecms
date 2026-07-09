import os
import paramiko, os

# 禁用 SSH agent 和密钥查找
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    os.environ.get("SERVER_HOST", ""),
    username='root',
    password=os.environ.get("SERVER_PASS", ""),
    timeout=15,
    allow_agent=False,
    key_filename=None,
)

cmds = [
    'cat /etc/nginx/sites-enabled/ziwi.cn',
    'ls -la /var/www/',
    'df -h',
]

for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(f'=== {cmd} ===')
    if out: print(out)
    if err: print('ERR:', err)

ssh.close()
print('Done.')
