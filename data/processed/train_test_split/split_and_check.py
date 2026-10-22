"""Base-compatible entry point for the Week 2 split and leakage check.

Run from the repository root:
    python data/processed/train_test_split/split_and_check.py
"""

from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT / "scripts" / "export_splits.py"), run_name="__main__")
