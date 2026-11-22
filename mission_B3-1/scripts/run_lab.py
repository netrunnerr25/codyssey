#!/usr/bin/env python3
"""Deploy, collect real evidence, recover a controlled outage, always cleanup."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
state = ROOT / '.local/state.json'
if state.exists():
    raise SystemExit('Existing lab state found. Run lab.py cleanup first; archive .local before a new lab.')
if '--free-tier-checked' not in sys.argv[1:]:
    raise SystemExit('Confirm Free Tier eligibility/remaining credits first, then add --free-tier-checked.')
# run_lab.py takes the same options as lab.py deploy, with --profile before other options.
args = sys.argv[1:]
profile = []
if '--profile' in args:
    i = args.index('--profile')
    profile = args[i:i+2]
    del args[i:i+2]
base = [sys.executable, str(ROOT / 'scripts/lab.py')] + profile
try:
    subprocess.run(base + ['deploy'] + args, check=True)
    subprocess.run(base + ['verify'], check=True)
    subprocess.run(base + ['troubleshoot'], check=True)
finally:
    if state.exists():
        subprocess.run(base + ['cleanup'], check=True)
