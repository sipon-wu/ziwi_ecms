import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get("SERVER_HOST", ""), username='root', password=os.environ.get("SERVER_PASS", ""), timeout=15, allow_agent=False, key_filename=None)
sftp = ssh.open_sftp()

# 把修复脚本写到服务器上
script = """#!/usr/bin/env python3
import sys

with open('/etc/nginx/sites-enabled/ziwi.cn', 'r') as f:
    conf = f.read()

if '/demo/ecms/' in conf:
    print('ALREADY_EXISTS')
    sys.exit(0)

insert_block = '''
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
    # ==================================='''

new_conf = conf.replace('    # BBS API', insert_block + '\\n    # BBS API')
with open('/etc/nginx/sites-enabled/ziwi.cn', 'w') as f:
    f.write(new_conf)
print('INSERTED')
"""

with sftp.open('/tmp/fix_nginx.py', 'w') as f:
    f.write(script)

sftp.close()

# 执行修复脚本
stdin, stdout, stderr = ssh.exec_command('python3 /tmp/fix_nginx.py')
out = stdout.read().decode('utf-8', errors='replace').strip()
err = stderr.read().decode('utf-8', errors='replace').strip()
print('OUT:', out)
print('ERR:', err)

# 测试 nginx 配置
stdin, stdout, stderr = ssh.exec_command('nginx -t 2>&1')
out2 = stdout.read().decode('utf-8', errors='replace').strip()
err2 = stderr.read().decode('utf-8', errors='replace').strip()
print('\\nnginx -t OUT:', out2)
print('nginx -t ERR:', err2)

# 如果测试通过就 reload
if 'syntax is ok' in out2 or 'successful' in err2:
    ssh.exec_command('systemctl reload nginx')
    print('\\nnginx reloaded!')
else:
    # 回滚
    ssh.exec_command('cp /etc/nginx/sites-enabled/ziwi.cn.bak /etc/nginx/sites-enabled/ziwi.cn')
    print('\\nCONFIG TEST FAILED - ROLLED BACK')

# 验证访问
stdin, stdout, stderr = ssh.exec_command('curl -sk -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/')
code = stdout.read().decode().strip()
print('HTTP status for /demo/ecms/:', code)

ssh.close()
print('Done.')
