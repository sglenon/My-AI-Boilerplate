"""conftest.py — add scripts dir to sys.path for swarm tests."""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
