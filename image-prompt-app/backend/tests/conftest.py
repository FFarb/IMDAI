"""Test configuration ensuring the backend package is importable."""
from __future__ import annotations

import os
import sys

ROOT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(ROOT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
