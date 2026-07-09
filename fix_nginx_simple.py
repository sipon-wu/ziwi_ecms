import os
import paramiko

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASS = os.environ.get("SERVER_PASS", "")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15, allow_agent=False, key_filename=None)
sftp = ssh.open_sftp()

# 1. 恢复备份
stdin, stdout, stderr = ssh.exec_command('cp /etc/nginx/sites-enabled/ziwi.cn.bak /etc/nginx/sites-enabled/ziwi.cn 2>/dev/null; echo OK')
print('Restore backup:', stdout.read().decode().strip())

# 2. 读取现有配置
with sftp.open('/etc/nginx/sites-enabled/ziwi.cn', 'r') as f:
    conf = f.read().decode('utf-8').decode('utf-8')

# 3. 在 '# BBS API' 前插入 /demo/ecms/ location
insert_block = """
    # ===== 知微能碳管理系统 DEMO =====
    location /demo/ecms/ {
        alias /var/www/demo/ecms/;
        index index.html;
        try_files $uri $uri/ /demo/ecms/index.html;
    }
    location /demo/ecms/api/ {
        proxy_pass http://127.0.0.1:8088/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    # ==================================="""

if '/demo/ecms/' not in conf:
    new_conf = conf.replace('# BBS API', insert_block + '\n    # BBS API')
    with sftp.open('/etc/nginx/sites-enabled/ziwi.cn', 'w') as f:
        f.write(new_conf)
    print('Inserted /demo/ecms/ location.')
else:
    print('/demo/ecms/ location already exists.')

# 4. 验证配置
stdin, stdout, stderr = ssh.exec_command('nginx -t 2>&1')
out = stdout.read().decode()
err = stderr.read().decode()
print('nginx -t:', out, err)

# 5. 重新加载 nginx
if 'syntax is ok' in out or 'successful' in err:
    ssh.exec_command('systemctl reload nginx')
    print('nginx reloaded.')
else:
    print('SKIP reload - config test failed!')

# 6. 验证访问
stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/')
code = stdout.read().decode().strip()
print(f'https://ziwi.cn/demo/ecms/ -> HTTP {code}')

sftp.close()
ssh.close()
print('Done.')
