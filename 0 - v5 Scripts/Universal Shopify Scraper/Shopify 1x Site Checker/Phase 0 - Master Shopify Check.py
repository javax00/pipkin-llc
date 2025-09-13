import subprocess
import sys

# Purpose - Check to see if input websites on P1 Check Links are shopify

scripts = [
    'Phase 1 - Shopify Check.py',
    'Phase 2 - UPC Check.py',
    ]

# Auto-detect the Python interpreter path
python_path = sys.executable

# Execute each script
for script in scripts:
    subprocess.call([python_path, script])
