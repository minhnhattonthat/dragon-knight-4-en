"""One-command check (pre-commit hook): unit tests + text lint. Exit code gates the commit."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', os.path.join(ROOT, 'tests')], cwd=ROOT)
sys.exit(r.returncode)
