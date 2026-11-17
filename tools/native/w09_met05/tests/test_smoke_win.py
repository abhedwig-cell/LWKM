"""Compatibility entry point: use the source-aware compiled-producer tests."""
from pathlib import Path
import subprocess
import sys
if __name__ == '__main__':
    raise SystemExit(subprocess.call([sys.executable, str(Path(__file__).with_name('test_hum_contract.py')), *sys.argv[1:]]))
