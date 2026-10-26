"""
merge_state_table.py — one row per state (50 + DC) combining every state-level input, plus a
missing-data audit for all clean tables.

WHAT IT DOES
  Joins, on the two-letter state code (every join must match all 51 states):
    - Census constants (population, income, housing)            census_state.csv
    - truck share, EV fee, ACC II adoption                       state_context.csv
    - full-period Google Trends profiles                         trends_state_profile.csv
    - NHTSA complaint counts (all vehicles, EVs)                 nhtsa_state_complaints.csv
    - summaries of the quarterly panel                           panel_state_quarter.csv
  Derived columns (formulas):
    ev_share_mean        mean EV share of new registrations over the 6 quarters (pct)
    ev_share_2026q2      EV share in 2026 Q2 (pct)
    ev_share_change_yoy  2026 Q2 minus 2025 Q2 (percentage points)
    ports_per_10k_2026q2 public charging ports per 10K residents, 2026 Q2
    evs_per_10k_start/end EVs in operation per 10K residents, 2025 Q1 and 2026 Q2
    ev_stock_growth_per_10k = end - start  (used-EV signal input; compared in Stage III with
                              EV share of new registrations — a signal, not a count)
    ev_stock_mean        mean EVs in operation over the 6 quarters
                         = mean(evs_per_10k_res) x pop_2025 / 10,000
    ev_complaints_per_10k_evs = EV complaints (Jan 2025 – Jun 2026) / ev_stock_mean x 10,000
  Electricity price (H2a) is not included yet: the EIA file is still to be added.
  Also writes data/clean/audit_missing.csv: number of missing values per column per clean table.

INPUTS   data/clean/{census_state, state_context, trends_state_profile, nhtsa_state_complaints,
         panel_state_quarter}.csv
OUTPUTS  data/clean/state_table.csv (51 rows), data/clean/audit_missing.csv
RUN      python stage_1_data/merge_state_table.py   (after all prepare_*.py and merge_panel.py)
"""
import sys
from pathlib import Path

import pandas as pd

from merge_panel import ValidationError, strict_merge

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"


def panel_summaries(panel: pd.DataFrame, pop: pd.Series) -> pd.DataFrame:
    p = panel.pivot(index="state", columns="quarter")
    out = pd.DataFrame(index=p.index)
    out["ev_share_mean"] = p["ev_share"].mean(axis=1).round(3)
    out["ev_share_2026q2"] = p["ev_share"]["2026Q2"]
    out["ev_share_change_yoy"] = (p["ev_share"]["2026Q2"] - p["ev_share"]["2025Q2"]).round(2)
    out["ports_per_10k_2026q2"] = p["ports_per_10k"]["2026Q2"]
    out["evs_per_10k_start"] = p["evs_per_10k_res"]["2025Q1"]
    out["evs_per_10k_end"] = p["evs_per_10k_res"]["2026Q2"]
    out["ev_stock_growth_per_10k"] = (out.evs_per_10k_end - out.evs_per_10k_start).round(2)
    out["ev_search_ratio_mean"] = p["ev_search_ratio"].mean(axis=1).round(3)
    out["gas_regular_mean"] = p["gas_regular_mean"].mean(axis=1).round(4)
    out["ev_stock_mean"] = (p["evs_per_10k_res"].mean(axis=1) * pop.reindex(p.index) / 10_000).round(0)
    return out.reset_index()


def main() -> int:
    t = {n: pd.read_csv(CLEAN / f"{n}.csv") for n in
         ["census_state", "state_context", "trends_state_profile", "nhtsa_state_complaints",
          "panel_state_quarter", "trends_state_quarter", "alliance_state_quarter", "gas_state_quarter"]}
    s = t["census_state"]
    for name in ["state_context", "trends_state_profile", "nhtsa_state_complaints"]:
        s = strict_merge(s, t[name], on="state", label=f"state x {name}", validate="1:1")
    s = strict_merge(s, panel_summaries(t["panel_state_quarter"], s.set_index("state").pop_2025),
                     on="state", label="state x panel summaries", validate="1:1")
    s["ev_complaints_per_10k_evs"] = (s.complaints_ev / s.ev_stock_mean * 10_000).round(2)
    if len(s) != 51 or not s.state.is_unique:
        raise ValidationError("state table must have 51 unique states")
    s.to_csv(CLEAN / "state_table.csv", index=False)

    audit = []
    for name, df in t.items():
        for c in df.columns:
            audit.append({"table": name, "column": c, "rows": len(df), "missing": int(df[c].isna().sum())})
    for c in s.columns:
        audit.append({"table": "state_table", "column": c, "rows": len(s), "missing": int(s[c].isna().sum())})
    a = pd.DataFrame(audit)
    a.to_csv(CLEAN / "audit_missing.csv", index=False)
    print(f"Wrote state_table.csv: {s.shape}")
    print("Missing values (non-zero only):")
    print(a[a.missing > 0].to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
