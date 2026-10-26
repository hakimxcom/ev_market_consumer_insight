"""
prepare_trends_quarterly.py — quarterly Google Trends search-interest measures by state.

WHAT IT DOES
  Reads Google Trends "compare by region" exports, one per quarter (2025 Q1 – 2026 Q2).
  Settings for every export: United States; category Autos & Vehicles; Web Search;
  low-volume regions included. In each export a state's values across the compared terms
  sum to 100, so they are SHARES of search among those terms (comparable across states).

  Group A terms: Electric vehicle, Hybrid vehicle, Plug-in hybrid (Automotive class topics),
                 Car dealership (topic).
  Group B1 terms: Electric vehicle (Automotive class), Charging station (topic).

  Measures written (all 0–100):
    ev_search_ratio      = EV / (EV + Car dealership) x 100            <- main measure
                           "EV interest per unit of general car-shopping interest". Ratios
                           between two terms are unaffected when a third term (hybrid) shifts.
    ev_search_share4     = EV share of all four Group A terms           <- robustness check
    hybrid_search_share  = Hybrid share of the four terms; set to MISSING in 2025 Q3 and
                           2025 Q4, when it collapses in every state at once (mean 27.5 -> 11.1
                           -> 10.7 -> 25.3) — treated as a Google measurement artifact.
    phev_search_share    = Plug-in hybrid share of the four terms
    charging_search_share= Charging station share in Group B1 (charging interest relative to EV)
  Search is labeled "interest", never "demand".

  Rules: a value of 0 means Google had too little data -> MISSING, never zero.
  Checks (stop on failure): 50 states + DC exactly once per file; all values numeric;
  each state's terms sum to 100 (+/-1, Google rounding).

INPUTS   data/raw/trends/trends_A_<YYYYQn>_states.csv, trends_B1_<YYYYQn>_states.csv (6 + 6)
OUTPUT   data/clean/trends_state_quarter.csv  (306 rows)
RUN      python stage_1_data/prepare_trends_quarterly.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from states import STATES, to_abbr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "trends"
OUT = ROOT / "data" / "clean" / "trends_state_quarter.csv"
QUARTERS = ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
HYBRID_ARTIFACT_QUARTERS = {"2025Q3", "2025Q4"}
TERMS_A = ["Electric vehicle", "Hybrid vehicle", "Plug-in hybrid", "Car dealership"]
TERMS_B1 = ["Electric vehicle", "Charging station"]


class ValidationError(Exception):
    pass


def read_region_file(path: Path, terms: list[str]) -> pd.DataFrame:
    """Read one Trends region export, check it, return state code + terms (0 -> NaN)."""
    d = pd.read_csv(path)
    if d.columns[0] != "Region" or list(d.columns[1:]) != terms:
        raise ValidationError(f"{path.name}: expected columns Region + {terms}, got {list(d.columns)}")
    vals = d[terms].apply(pd.to_numeric, errors="coerce")
    if vals.isna().any().any():
        raise ValidationError(f"{path.name}: non-numeric values (e.g. '<1')")
    sums = vals.sum(axis=1)
    if ((sums - 100).abs() > 1).any():
        raise ValidationError(f"{path.name}: rows not summing to 100: {d.Region[(sums - 100).abs() > 1].tolist()}")
    out = vals.replace(0, np.nan)
    out.insert(0, "state", to_abbr(d.Region, path.name).values)
    if len(out) != 51 or not out.state.is_unique or set(out.state) != set(STATES.state):
        raise ValidationError(f"{path.name}: expected 50 states + DC once each, got {len(out)} rows")
    return out


def measures(a: pd.DataFrame, b1: pd.DataFrame, quarter: str) -> pd.DataFrame:
    m = a.merge(b1[["state", "Charging station"]], on="state", how="inner", validate="1:1")
    if len(m) != 51:
        raise ValidationError(f"{quarter}: A and B1 do not cover the same states")
    out = pd.DataFrame({
        "state": m.state,
        "quarter": quarter,
        "ev_search_ratio": (m["Electric vehicle"] / (m["Electric vehicle"] + m["Car dealership"]) * 100).round(2),
        "ev_search_share4": m["Electric vehicle"],
        "hybrid_search_share": np.nan if quarter in HYBRID_ARTIFACT_QUARTERS else m["Hybrid vehicle"],
        "phev_search_share": m["Plug-in hybrid"],
        "charging_search_share": m["Charging station"],
    })
    return out


def main() -> int:
    frames = []
    for q in QUARTERS:
        a = read_region_file(RAW / f"trends_A_{q}_states.csv", TERMS_A)
        b1 = read_region_file(RAW / f"trends_B1_{q}_states.csv", TERMS_B1)
        frames.append(measures(a, b1, q))
        print(f"{q}: A and B1 OK")
    out = pd.concat(frames, ignore_index=True).sort_values(["state", "quarter"])
    if out.duplicated(["state", "quarter"]).any() or len(out) != 306:
        raise ValidationError("output keys not unique or row count != 306")
    out.to_csv(OUT, index=False)
    n_missing = out.drop(columns=["state", "quarter"]).isna().sum()
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(out)} rows | missing by column: {n_missing[n_missing > 0].to_dict()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
