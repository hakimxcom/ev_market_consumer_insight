"""
run_all.py — run the whole pipeline in order: Stage II data preparation, then (when present)
Stage III analysis. Stops at the first step that fails.

INPUTS   data/raw/... (see README for where to get each source), data/manual/...
OUTPUTS  data/clean/..., outputs/...
RUN      python run_all.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "stage_1_data/prepare_alliance.py",
    "stage_1_data/prepare_census.py",
    "stage_1_data/prepare_trends_quarterly.py",
    "stage_1_data/prepare_trends_profiles.py",
    "stage_1_data/prepare_gas.py",
    "stage_1_data/prepare_nhtsa.py",
    "stage_1_data/prepare_state_context.py",
    "stage_1_data/merge_panel.py",
    "stage_1_data/merge_state_table.py",
]
STEPS += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "stage_2_analysis").glob("[0-9]*.py"))

for step in STEPS:
    print(f"\n=== {step}")
    if subprocess.run([sys.executable, step], cwd=ROOT).returncode != 0:
        sys.exit(f"Stopped: {step} failed")
print("\nAll steps completed.")
