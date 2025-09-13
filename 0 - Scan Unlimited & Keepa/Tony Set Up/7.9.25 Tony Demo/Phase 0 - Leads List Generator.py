import subprocess
import sys

scripts = [
    'Phase 1 - SU Clean Up.py',
    'Phase 2 - Wait.py',
    'Phase 3 - Keepa Clean Up.py',
    'Phase 4 - Finalize.py',
    'Phase 5 - Clean Up.py',
    ]

# Auto-detect the Python interpreter path
python_path = sys.executable

# Execute each script
for script in scripts:
    subprocess.call([python_path, script])
