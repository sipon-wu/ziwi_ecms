#!/usr/bin/env python3
import os
"""
Deploy dist/ to 193.112.163.147:/var/www/demo/ecms/
Then reload nginx.
"""
import paramiko, os

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASS = os.environ.get("SERVER_PASS", "")
LOCAL_DIST = r'D:\工业元\数云_新质力\ziwi_project_dna\frontend\dist'
REMOTE_DIR = '/var/www/demo/ecms'
NGINX_CONF = r'D:\工业元\数云_新质力\ziwi_project_dna\ecms.ziwi.cn.nginx.conf'

def ssh_cmd(ssh, cmd, desc=''):
    print(f'[SSH] {desc or cmd}')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
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

    # 1. Create remote dir
    ssh_cmd(ssh, f'mkdir -p {REMOTE_DIR}', 'Create remote dir')

    # 2. Upload dist/ recursively
    print('\n[SFTP] Uploading dist/ ...')
    for root, dirs, files in os.walk(LOCAL_DIST):
        for fname in files:
            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, LOCAL_DIST).replace('\\', '/')
            remote_path = f'{REMOTE_DIR}/{rel_path}'
            remote_dir = os.path.dirname(remote_path)
            ssh_cmd(ssh, f'mkdir -p "{remote_dir}"', '')
            print(f'  -> {rel_path}')
            sftp.put(local_path, remote_path)

    # 3. Upload nginx config
    print('\n[SFTP] Uploading nginx config...')
    remote_nginx = '/etc/nginx/sites-enabled/ecms.ziwi.cn'
    sftp.put(NGINX_CONF, remote_nginx)
    ssh_cmd(ssh, f'cat {remote_nginx}', 'Verify nginx config')

    # 4. Test nginx config
    ssh_cmd(ssh, 'nginx -t', 'Test nginx config')

    # 5. Reload nginx
    ssh_cmd(ssh, 'systemctl reload nginx || nginx -s reload', 'Reload nginx')

    # 6. Check backend
    ssh_cmd(ssh, 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/api/health 2>/dev/null || echo "backend down"', 'Check backend')

    sftp.close()
    ssh.close()
    print('\n✅ Deploy complete!')

if __name__ == '__main__':
    main()
