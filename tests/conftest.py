from pathlib import Path
import sys

# Ensure project root is on sys.path so tests can import top-level packages
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
