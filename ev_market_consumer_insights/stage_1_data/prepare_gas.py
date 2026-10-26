"""
prepare_gas.py — quarterly average regular gasoline price by state, 2025 Q1 – 2026 Q2.

WHAT IT DOES
  Reads the public MasterGas.csv file (AAA daily state average prices, collected by the
  jgreathouse9/AAAGas project on GitHub; not affiliated with AAA and not redistributed here).
  For each state and quarter:
      gas_regular_mean = sum of observed daily regular prices / number of observed days
  Days with no observation are reported, never filled in or interpolated.
  Checks (stop on failure): 50 states + DC exactly; one row per state per day; every
  regular price parses as dollars between $1 and $10.

INPUTS   data/raw/gas/MasterGas.csv   (get it with:
         git clone --depth 1 https://github.com/jgreathouse9/AAAGas  ->  Prices/MasterGas.csv)
OUTPUTS  data/clean/gas_state_quarter.csv   (306 rows: state, quarter, mean, observed days)
         data/clean/audit_gas_missing_days.csv  (every calendar day missing in the window)
RUN      python stage_1_data/prepare_gas.py
"""
import sys
from pathlib import Path

import pandas as pd

from states import STATES, to_abbr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "gas" / "MasterGas.csv"
CLEAN = ROOT / "data" / "clean"
START, END = "2025-01-01", "2026-06-30"


class ValidationError(Exception):
    pass


def load(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, dtype=str)
    if not {"State", "Regular", "Date"} <= set(d.columns):
        raise ValidationError(f"unexpected columns {list(d.columns)}")
    d = d[["State", "Regular", "Date"]].copy()
    d["date"] = pd.to_datetime(d.Date, format="%Y-%m-%d", errors="coerce")
    if d.date.isna().any():
        raise ValidationError(f"{d.date.isna().sum()} unparsable dates")
    d["regular"] = pd.to_numeric(d.Regular.str.replace("$", "", regex=False), errors="coerce")
    if d.regular.isna().any() or not d.regular.between(1, 10).all():
        raise ValidationError("regular price missing or outside $1–$10")
    d["state"] = to_abbr(d.State, "MasterGas")
    if d.duplicated(["state", "date"]).any():
        raise ValidationError("more than one row for the same state and day")
    if set(d.state) != set(STATES.state):
        raise ValidationError("states present do not equal 50 states + DC")
    return d[["state", "date", "regular"]]


def quarterly(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    w = d[(d.date >= START) & (d.date <= END)].copy()
    w["quarter"] = w.date.dt.to_period("Q").astype(str)
    q = (w.groupby(["state", "quarter"])
           .agg(gas_regular_mean=("regular", "mean"), gas_days_observed=("regular", "size"))
           .reset_index())
    q["gas_regular_mean"] = q.gas_regular_mean.round(4)
    cal = pd.period_range(START, END, freq="Q")
    q["gas_days_in_quarter"] = q.quarter.map({str(p): (p.end_time.normalize() - p.start_time).days + 1 for p in cal})
    # missing-day audit
    all_days = pd.date_range(START, END, freq="D")
    grid = pd.MultiIndex.from_product([sorted(STATES.state), all_days], names=["state", "date"]).to_frame(index=False)
    miss = grid.merge(w[["state", "date"]], how="left", indicator=True)
    miss = miss[miss._merge == "left_only"].drop(columns="_merge")
    if len(q) != 306:
        raise ValidationError(f"expected 306 state-quarters, got {len(q)}")
    return q, miss


def main() -> int:
    q, miss = quarterly(load(RAW))
    q.to_csv(CLEAN / "gas_state_quarter.csv", index=False)
    miss.to_csv(CLEAN / "audit_gas_missing_days.csv", index=False)
    days = sorted(miss.date.dt.strftime("%Y-%m-%d").unique())
    print(f"Wrote gas_state_quarter.csv: {len(q)} rows | observed days per state-quarter "
          f"{q.gas_days_observed.min()}–{q.gas_days_observed.max()}")
    print(f"Missing calendar days (all states, not filled): {len(days)} -> {days}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
