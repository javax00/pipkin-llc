import subprocess
import sys

scripts = [
    'Phase 1 - Pagination Urls.py',
    'Phase 2 - UPC Extraction.py',
    ]

# Auto-detect the Python interpreter path
python_path = sys.executable

# Execute each script
for script in scripts:
    subprocess.call([python_path, script])
