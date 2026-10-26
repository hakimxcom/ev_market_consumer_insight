"""
merge_panel.py — assemble the state x quarter panel from the cleaned source tables.

WHAT IT DOES (grows as Stage II items are added)
  1. Starts from the Alliance outcome table (data/clean/alliance_state_quarter.csv), states + DC
     only (the U.S. reference row is set aside).
  2. Joins Census constants (data/clean/census_state.csv) on state; every row must match.
  3. Computes public charging ports per 10K residents:
         ports_per_10k = total_ports / population * 10,000
     Population = the Census July 1 estimate for the same calendar year where available
     (2025 quarters -> July 1, 2025); 2026 quarters also use July 1, 2025, the latest estimate.
     The year used is stored in pop_year so the choice is visible.
  4. Joins quarterly Google Trends measures (data/clean/trends_state_quarter.csv) on
     state + quarter; every row must match.
  5. Joins quarterly mean regular gas price (data/clean/gas_state_quarter.csv) on state + quarter.
  Joins fail loudly: any unmatched or duplicated key stops the script.

INPUTS   data/clean/alliance_state_quarter.csv, data/clean/census_state.csv,
         data/clean/trends_state_quarter.csv, data/clean/gas_state_quarter.csv
OUTPUT   data/clean/panel_state_quarter.csv  (306 rows = 51 x 6)
RUN      python stage_1_data/merge_panel.py   (after prepare_alliance.py and prepare_census.py)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = CLEAN / "panel_state_quarter.csv"


class ValidationError(Exception):
    pass


def strict_merge(left: pd.DataFrame, right: pd.DataFrame, on, label: str, validate: str) -> pd.DataFrame:
    keys = [on] if isinstance(on, str) else list(on)
    m = left.merge(right, on=keys, how="outer", validate=validate, indicator=True)
    bad = m[m._merge != "both"]
    if len(bad):
        raise ValidationError(f"{label}: {len(bad)} unmatched rows, e.g. "
                              f"{bad[keys + ['_merge']].head(5).to_dict('records')}")
    return m.drop(columns="_merge")


def add_ports_per_10k(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel.copy()
    p["pop_year"] = 2025  # latest July 1 estimate covers both 2025 and 2026 quarters
    p["population"] = p.pop_2025
    p["ports_per_10k"] = (p.total_ports / p.population * 10_000).round(3)
    return p


def main() -> int:
    alliance = pd.read_csv(CLEAN / "alliance_state_quarter.csv")
    census = pd.read_csv(CLEAN / "census_state.csv")
    states = alliance[~alliance.is_us].drop(columns="is_us")
    panel = strict_merge(states, census, on="state", label="Alliance x Census", validate="m:1")
    panel = add_ports_per_10k(panel)
    trends = pd.read_csv(CLEAN / "trends_state_quarter.csv")
    panel = strict_merge(panel, trends, on=["state", "quarter"], label="panel x Trends", validate="1:1")
    gas = pd.read_csv(CLEAN / "gas_state_quarter.csv")
    panel = strict_merge(panel, gas, on=["state", "quarter"], label="panel x gas", validate="1:1")
    if len(panel) != 306 or panel.duplicated(["state", "quarter"]).any():
        raise ValidationError(f"panel has {len(panel)} rows or duplicate keys; expected 306 unique")
    first = ["state", "state_name", "fips", "quarter"]
    panel = panel[first + [c for c in panel.columns if c not in first]].sort_values(["state", "quarter"])
    panel.to_csv(OUT, index=False)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(panel)} rows, {panel.shape[1]} columns")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
