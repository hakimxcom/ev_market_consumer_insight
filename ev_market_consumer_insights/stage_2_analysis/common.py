"""
common.py — shared paths and loaders for the Stage III analysis scripts (not run on its own).

Every analysis script reads only the cleaned files in data/clean/ and writes to outputs/.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
SITE = ROOT / "outputs" / "site_data"
for _d in (TABLES, FIGURES, SITE):
    _d.mkdir(parents=True, exist_ok=True)

QUARTERS = ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]


def panel() -> pd.DataFrame:
    return pd.read_csv(CLEAN / "panel_state_quarter.csv")


def state_table() -> pd.DataFrame:
    return pd.read_csv(CLEAN / "state_table.csv")


def alliance() -> pd.DataFrame:
    return pd.read_csv(CLEAN / "alliance_state_quarter.csv")


def write_json(name: str, obj) -> None:
    """Site data: every number on the dashboard comes from these files."""
    with open(SITE / f"{name}.json", "w") as f:
        json.dump(obj, f, indent=1, default=float)
