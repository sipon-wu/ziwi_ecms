import paramiko, os

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASS = os.environ.get("SERVER_PASS", "")
LOCAL_DIST = r'D:\工业元\数云_新质力\ziwi_project_dna\frontend\dist'
REMOTE_DIR  = '/var/www/demo/ecms'

def ssh_cmd(ssh, cmd, desc=''):
    print(f'[SSH] {desc or cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print('  OUT:', out[:300])
    if err: print('  ERR:', err[:300])
    return out, err

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15, allow_agent=False, key_filename=None)
    sftp = ssh.open_sftp()

    # 1. Restore backup config first
    ssh_cmd(ssh, 'cp /etc/nginx/sites-enabled/ziwi.cn.bak /etc/nginx/sites-enabled/ziwi.cn 2>/dev/null; echo "restored"', 'Restore backup config')

    # 2. Upload dist/ to server
    print('\n[SFTP] Uploading dist/ ...')
    for root, dirs, files in os.walk(LOCAL_DIST):
        for fname in files:
            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, LOCAL_DIST).replace('\\', '/')
            remote_path = f'{REMOTE_DIR}/{rel_path}'
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.makedirs(remote_dir)
            except Exception:
                pass
            sftp.put(local_path, remote_path)
            print(f'  -> {rel_path}')

    # 3. Insert /demo/ecms/ location into existing config (before # BBS API)
    insert_block = """
    # ========== 知微能碳管理系统 DEMO ==========
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
    # ==================================================
"""
    python_cmd = f'''python3 -c "
import sys
with open('/etc/nginx/sites-enabled/ziwi.cn', 'r') as f:
    content = f.read()
if '/demo/ecms/' not in content:
    content = content.replace('# BBS API', '''{insert_block}# BBS API''')
    with open('/etc/nginx/sites-enabled/ziwi.cn', 'w') as f:
        f.write(content)
    print('Inserted')
else:
    print('Already exists')
"'''
    ssh_cmd(ssh, python_cmd, 'Insert /demo/ecms/ location into nginx config')

    # 4. Verify config
    ssh_cmd(ssh, 'cat /etc/nginx/sites-enabled/ziwi.cn | grep -A5 "demo/ecms"', 'Verify inserted config')

    # 5. Test nginx config
    ssh_cmd(ssh, 'nginx -t', 'Test nginx config')

    # 6. Reload nginx
    ssh_cmd(ssh, 'systemctl reload nginx', 'Reload nginx')

    # 7. Verify
    ssh_cmd(ssh, 'curl -s -o /dev/null -w "%{http_code}" https://localhost/demo/ecms/ -H "Host: ziwi.cn"', 'Verify /demo/ecms/')

    sftp.close()
    ssh.close()
    print('\n✅ Done! Visit: https://ziwi.cn/demo/ecms/')

if __name__ == '__main__':
    import os
    main()
