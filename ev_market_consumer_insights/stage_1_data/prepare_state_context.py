"""
prepare_state_context.py — state-level context variables for H4 (policy) and H6 (trucks),
plus a checked event calendar for dashboard annotations.

WHAT IT DOES
  1. Truck share (H6), from FHWA Highway Statistics 2023, Table MV-1 (State Motor-Vehicle
     Registrations), transcribed in data/manual/fhwa_mv1_2023_transcribed.csv:
        truck_share = trucks / (automobiles + trucks) x 100
     FHWA "trucks" include pickups, SUVs, vans and heavy trucks, and states classify vehicles
     differently, so this measures "truck/SUV share", not pickups alone.
     Check: each state's categories sum to its total, and each column sums to the U.S. total,
     within 1 vehicle (the published table itself has +/-1 rounding differences).
  2. Policy environment (H4), from data/manual/policy_state.csv (sources in policy_sources.md):
     has_ev_fee_in_window (main measure), BEV fee amounts from two sources, ACC II adoption.
  3. Event calendar: data/manual/event_calendar.csv — every event needs a valid date and at
     least one source URL.
  Checks stop the script on failure.

INPUTS   data/manual/fhwa_mv1_2023_transcribed.csv, data/manual/policy_state.csv,
         data/manual/event_calendar.csv
OUTPUTS  data/clean/state_context.csv (51 rows), data/clean/event_calendar.csv
RUN      python stage_1_data/prepare_state_context.py
"""
import sys
from pathlib import Path

import pandas as pd

from states import STATES, to_abbr

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "data" / "manual"
CLEAN = ROOT / "data" / "clean"


class ValidationError(Exception):
    pass


def truck_share(path: Path, tolerance: int = 1) -> pd.DataFrame:
    d = pd.read_csv(path)
    cols = ["automobiles", "buses", "trucks", "motorcycles"]
    total = d[d.state_name == "TOTAL"]
    st = d[d.state_name != "TOTAL"].copy()
    if len(total) != 1:
        raise ValidationError("FHWA: expected one TOTAL row")
    row_gap = (st[cols].sum(axis=1) - st.all_motor_vehicles).abs()
    if (row_gap > tolerance).any():
        raise ValidationError(f"FHWA: row totals off for {st.state_name[row_gap > tolerance].tolist()}")
    for c in cols + ["all_motor_vehicles"]:
        if abs(st[c].sum() - total[c].iloc[0]) > tolerance:
            raise ValidationError(f"FHWA: column {c} does not sum to TOTAL")
    st["state"] = to_abbr(st.state_name, "FHWA MV-1")
    st["truck_share"] = (st.trucks / (st.automobiles + st.trucks) * 100).round(2)
    if len(st) != 51 or set(st.state) != set(STATES.state):
        raise ValidationError("FHWA: expected 50 states + DC")
    return st[["state", "truck_share"]]


def policy(path: Path) -> pd.DataFrame:
    p = pd.read_csv(path)
    if len(p) != 51 or set(p.state) != set(STATES.state) or not p.state.is_unique:
        raise ValidationError("policy: expected 50 states + DC once each")
    for c in ["has_ev_fee_in_window", "acc2_adopted_2025q1"]:
        if not p[c].isin([0, 1]).all():
            raise ValidationError(f"policy: {c} must be 0/1")
    no_fee_with_amount = p[(p.has_ev_fee_in_window == 0) & p.ev_fee_bev_artba_sep2025.notna()]
    if len(no_fee_with_amount):
        raise ValidationError(f"policy: fee amount without fee flag for {no_fee_with_amount.state.tolist()}")
    return p.drop(columns="note")


def events(path: Path) -> pd.DataFrame:
    e = pd.read_csv(path)
    e["date"] = pd.to_datetime(e.date, format="%Y-%m-%d", errors="coerce")
    if e.date.isna().any() or e.source_1.isna().any() or not e.source_1.str.startswith("https://").all():
        raise ValidationError("event calendar: every event needs a valid date and an https source")
    return e.sort_values("date")


def main() -> int:
    ctx = STATES[["state"]].merge(truck_share(MANUAL / "fhwa_mv1_2023_transcribed.csv"), on="state",
                                  validate="1:1").merge(policy(MANUAL / "policy_state.csv"), on="state",
                                                        validate="1:1")
    if len(ctx) != 51:
        raise ValidationError("state context lost rows in merge")
    ctx.to_csv(CLEAN / "state_context.csv", index=False)
    ev = events(MANUAL / "event_calendar.csv")
    ev.to_csv(CLEAN / "event_calendar.csv", index=False, date_format="%Y-%m-%d")
    print(f"Wrote state_context.csv (51 rows): {int(ctx.has_ev_fee_in_window.sum())} states with EV fee, "
          f"{int(ctx.acc2_adopted_2025q1.sum())} ACC II states; truck share "
          f"{ctx.truck_share.min():.1f}–{ctx.truck_share.max():.1f}%")
    print(f"Wrote event_calendar.csv: {len(ev)} events")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
