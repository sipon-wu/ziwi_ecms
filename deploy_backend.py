#!/usr/bin/env python3
import os
"""Upload backend/ to server and start it."""
import paramiko, os

HOST = os.environ.get("SERVER_HOST", "")
USER = 'root'
PASS = os.environ.get("SERVER_PASS", "")
LOCAL_BACKEND = r'D:\工业元\数云_新质力\ziwi_project_dna\backend'
REMOTE_BACKEND = '/var/www/demo/ecms-backend'

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

    # 1. Create remote backend dir
    ssh_cmd(ssh, f'mkdir -p {REMOTE_BACKEND}', 'Create backend dir')

    # 2. Upload backend files (skip __pycache__, .db maybe large)
    print('\n[SFTP] Uploading backend/ ...')
    skip_dirs = {'__pycache__', 'node_modules', '.git'}
    for root, dirs, files in os.walk(LOCAL_BACKEND):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fname.endswith('.pyc') or fname == '__pycache__':
                continue
            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, LOCAL_BACKEND).replace('\\', '/')
            remote_path = f'{REMOTE_BACKEND}/{rel_path}'
            remote_dir = os.path.dirname(remote_path)
            ssh_cmd(ssh, f'mkdir -p "{remote_dir}"', '')
            print(f'  -> {rel_path}')
            sftp.put(local_path, remote_path)

    # 3. Install backend deps on server
    ssh_cmd(ssh, 'python3 -m pip install fastapi uvicorn sqlite3 2>&1 | tail -5', 'Install backend deps')

    # 4. Kill existing backend on port 8088
    ssh_cmd(ssh, 'fuser -k 8088/tcp 2>/dev/null; sleep 1', 'Kill old backend')

    # 5. Start backend
    ssh_cmd(ssh,
        f'nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8088 > {REMOTE_BACKEND}/backend.log 2>&1 &',
        'Start backend'
    )
    import time; time.sleep(3)

    # 6. Verify
    ssh_cmd(ssh, 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8088/docs || echo "backend check failed"', 'Verify backend')

    sftp.close()
    ssh.close()
    print('\nDeploy complete!')

if __name__ == '__main__':
    main()
