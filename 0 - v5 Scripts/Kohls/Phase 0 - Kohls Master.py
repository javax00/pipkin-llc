import subprocess
import sys

scripts = [
    'Phase 1 - Pagination Urls.py',
    'Phase 2 - Category Urls.py',
    'Phase 2.5 - Blacklist.py',
    'Phase 3 - UPC Extraction.py',
    'Phase 4 - Add to Cart.py',
    'Phase 5 - Merge Script.py',
    ]

# Auto-detect the Python interpreter path
python_path = sys.executable

# Execute each script
for script in scripts:
    subprocess.call([python_path, script])
