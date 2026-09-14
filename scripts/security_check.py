import subprocess
import re
import os
import sys

SECRET_PATTERNS = [
    (r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\']([^"\']{8,})["\']', 'API Key'),
    (r'(?i)(?:client[_-]?secret|app[_-]?secret)\s*[:=]\s*["\']([^"\']{8,})["\']', 'Secret'),
    (r'(?i)(?:access[_-]?token|bearer[_-]?token)\s*[:=]\s*["\']([^"\']{8,})["\']', 'Token'),
    (r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']([^"\']{4,})["\']', 'Password'),
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', 'Private Key'),
    (r'AIza[0-9A-Za-z-_]{35}', 'Google API Key'),
    (r'gh[pousr]_[A-Za-z0-9_]{36,}', 'GitHub Personal Access Token'),
    (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API Key'),
    (r'xox[baprs]-[0-9a-zA-Z]{10,}', 'Slack Token'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
    (r'amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', 'AWS MWS Key'),
    (r'(?i)postgres(?:ql)?://[a-zA-Z0-9_]+:[^@\s]+@', 'PostgreSQL Connection URI'),
    (r'(?i)mongodb(?:\+srv)?://[a-zA-Z0-9_]+:[^@\s]+@', 'MongoDB Connection URI'),
    (r'(?i)mysql://[a-zA-Z0-9_]+:[^@\s]+@', 'MySQL Connection URI'),
    (r'C:\\Users\\', 'Hardcoded Local Windows User Path'),
]

EXCLUDED_EXTS = ('.jpg', '.png', '.xlsx', '.xls', '.ico', '.webp')

def run_scan():
    tracked = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
    print(f"Scanning {len(tracked)} tracked Git files...")
    
    findings = []
    for fpath in tracked:
        if fpath.endswith(EXCLUDED_EXTS):
            continue
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, start=1):
                    # Skip comment headers or examples in .env.example
                    if fpath == '.env.example':
                        continue
                    if fpath == 'scripts/security_check.py':
                        continue
                    for pattern, label in SECRET_PATTERNS:
                        m = re.search(pattern, line)
                        if m:
                            findings.append((fpath, line_num, label, line.strip()[:90]))
        except Exception as err:
            findings.append((fpath, 0, 'Error reading file', str(err)))

    if not findings:
        print("\n[SECURITY AUDIT PASSED] ZERO secrets, keys, credentials, or private paths found.")
        return 0
    else:
        print(f"\n[WARNING] Found {len(findings)} potential security concerns:")
        for f, line, label, preview in findings:
            print(f" - [{label}] {f}:{line} -> {preview}")
        return 1

if __name__ == '__main__':
    sys.exit(run_scan())
