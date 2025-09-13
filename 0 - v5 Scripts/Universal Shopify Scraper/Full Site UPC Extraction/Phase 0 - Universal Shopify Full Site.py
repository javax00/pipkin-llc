import subprocess
import sys

scripts = [
    'Phase 1 - Shopify Check.py',
    'Phase 2 - Category Urls.py',
    ]

# Auto-detect the Python interpreter path
python_path = sys.executable

# Execute each script
for script in scripts:
    subprocess.call([python_path, script])
