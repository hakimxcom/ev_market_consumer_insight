"""
prepare_trends_profiles.py — full-period Google Trends profiles (one row per state) and
national monthly search series.

WHAT IT DOES
  Period for every export: Jan 1, 2025 – Sep 30, 2026. Settings: United States; category
  Autos & Vehicles; Web Search; low-volume regions included. Within one export a state's
  values sum to 100 -> shares of search among the compared terms.

  State profiles (data/clean/trends_state_profile.csv), 51 rows:
    Group A (full period):  ev_search_ratio_full = EV / (EV + Car dealership) x 100
                            (hybrid search in this window includes the 2025 Q3–Q4 artifact,
                            so only the EV/dealership ratio is kept)
    Group B1 (full period): charging_search_share_full
    Group E:  search shares for Used car, Tesla Model 3, Tesla Model Y, Chevrolet Equinox EV,
              Ford Mustang Mach-E, Hyundai Ioniq 5 (topics). Two derived shares among the five
              EV models only: tesla_share_of_ev_models, detroit_share_of_ev_models.
              CAVEATS kept in column names: the Equinox EV and Mach-E topics also capture gas
              Equinox / Mustang searches ("model-family" interest), and Equinox EV ranges only
              1–6 -> small differences are not meaningful.
    Group L:  lease searches by brand (Toyota, Chevy, Ford, Hyundai, Tesla, Honda), shares of
              the six (lease_tesla is Tesla's share of brand-lease searches).
    Group U1: used_tesla_share (vs. "Used car" topic). "Used Electric Cars" is 0 in every state
              and month -> dropped.
    Group B2 is NOT used by state (14 states absent, 13 more show too little data).
  National monthly series (data/clean/trends_national_monthly.csv), long format:
    group, term, month, value (Google's 0–100 index within each group's own export;
    compare months within a term, not levels across groups). B2 is cut at Sep 2026.

  Related queries (data/clean/trends_related_queries.csv): Google's top related queries for 7
    seed topics (EV, Model Y, Model 3, Equinox EV, Ioniq 5, Mach-E, Vehicle leasing), period
    Jan 1, 2025 – Oct 25, 2026 (pulled Oct 25, 2026). Kept as evidence for keyword choices;
    "Breakout" growth is stored as text.

  Rules: 0 in a state file = too little data -> MISSING. Checks (stop on failure): expected
  columns; 50 states + DC once each; numeric values; state rows sum to 100 (+/-1).

INPUTS   data/raw/trends/trends_{A,B1,E,L,U1}_full_states.csv,
         data/raw/trends/trends_{B1,B2,E,L,U1}_national_monthly.csv
         data/raw/trends/related_queries/related_<seed>.csv (7)
OUTPUTS  data/clean/trends_state_profile.csv, data/clean/trends_national_monthly.csv,
         data/clean/trends_related_queries.csv
RUN      python stage_1_data/prepare_trends_profiles.py
"""
import sys
from pathlib import Path

import pandas as pd

from prepare_trends_quarterly import ValidationError, read_region_file
from states import STATES

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "trends"
CLEAN = ROOT / "data" / "clean"

E_TERMS = ["Used car", "Tesla Model 3", "Tesla Model Y", "Chevrolet Equinox EV",
           "Ford Mustang Mach-E", "Hyundai Ioniq 5"]
L_TERMS = ["Lease Toyota", "Chevy Lease", "ford lease", "hyundai lease", "tesla lease", "Honda Lease"]
U1_TERMS = ["Used car", "used tesla", "Used Electric Cars"]
A_TERMS = ["Electric vehicle", "Hybrid vehicle", "Plug-in hybrid", "Car dealership"]
B1_TERMS = ["Electric vehicle", "Charging station"]
NATIONAL = {"B1": B1_TERMS, "B2": ["Electric car charger installation", "ev charging cost",
                                   "apartment ev charging"],
            "E": E_TERMS, "L": L_TERMS, "U1": U1_TERMS}
LAST_MONTH = "2026-09-01"


def state_profiles() -> pd.DataFrame:
    a = read_region_file(RAW / "trends_A_full_states.csv", A_TERMS)
    b1 = read_region_file(RAW / "trends_B1_full_states.csv", B1_TERMS)
    e = read_region_file(RAW / "trends_E_full_states.csv", E_TERMS)
    lease = read_region_file(RAW / "trends_L_full_states.csv", L_TERMS)
    u1_raw = pd.read_csv(RAW / "trends_U1_full_states.csv")
    if (u1_raw["Used Electric Cars"] != 0).any():
        raise ValidationError("U1: 'Used Electric Cars' is no longer all zero — revisit the drop rule")
    u1 = read_region_file(RAW / "trends_U1_full_states.csv", U1_TERMS)

    out = STATES[["state"]].copy()
    out = out.merge(pd.DataFrame({
        "state": a.state,
        "ev_search_ratio_full": (a["Electric vehicle"] / (a["Electric vehicle"] + a["Car dealership"]) * 100).round(2),
    }), on="state", validate="1:1")
    out = out.merge(pd.DataFrame({"state": b1.state, "charging_search_share_full": b1["Charging station"]}),
                    on="state", validate="1:1")

    models = e[E_TERMS[1:]]
    e_out = pd.DataFrame({
        "state": e.state,
        "used_car_share_E": e["Used car"],
        "model3_share": e["Tesla Model 3"],
        "modelY_share": e["Tesla Model Y"],
        "equinox_ev_family_share": e["Chevrolet Equinox EV"],
        "mach_e_family_share": e["Ford Mustang Mach-E"],
        "ioniq5_share": e["Hyundai Ioniq 5"],
        "tesla_share_of_ev_models": ((e["Tesla Model 3"] + e["Tesla Model Y"]) / models.sum(axis=1) * 100).round(1),
        "detroit_share_of_ev_models": ((e["Chevrolet Equinox EV"] + e["Ford Mustang Mach-E"])
                                       / models.sum(axis=1) * 100).round(1),
    })
    out = out.merge(e_out, on="state", validate="1:1")

    l_out = lease.rename(columns={"Lease Toyota": "lease_toyota", "Chevy Lease": "lease_chevy",
                                  "ford lease": "lease_ford", "hyundai lease": "lease_hyundai",
                                  "tesla lease": "lease_tesla", "Honda Lease": "lease_honda"})
    out = out.merge(l_out[["state", "lease_toyota", "lease_chevy", "lease_ford", "lease_hyundai",
                           "lease_tesla", "lease_honda"]], on="state", validate="1:1")
    out = out.merge(pd.DataFrame({"state": u1.state, "used_tesla_share": u1["used tesla"]}),
                    on="state", validate="1:1")
    if len(out) != 51:
        raise ValidationError(f"profile has {len(out)} rows, expected 51")
    return out


def national_monthly() -> pd.DataFrame:
    frames = []
    for g, terms in NATIONAL.items():
        d = pd.read_csv(RAW / f"trends_{g}_national_monthly.csv")
        if d.columns[0] != "Time" or list(d.columns[1:]) != terms:
            raise ValidationError(f"{g} national: unexpected columns {list(d.columns)}")
        d = d[d.Time <= LAST_MONTH]
        if d.Time.iloc[0] != "2025-01-01" or d.Time.iloc[-1] != LAST_MONTH or len(d) != 21:
            raise ValidationError(f"{g} national: expected 21 months Jan 2025 – Sep 2026")
        long = d.melt(id_vars="Time", var_name="term", value_name="value").rename(columns={"Time": "month"})
        long.insert(0, "group", g)
        frames.append(long)
    out = pd.concat(frames, ignore_index=True)
    out = out[~((out.group == "U1") & (out.term == "Used Electric Cars"))]  # all zero
    return out


def related_queries() -> pd.DataFrame:
    frames = []
    for f in sorted((RAW / "related_queries").glob("related_*.csv")):
        d = pd.read_csv(f)
        if list(d.columns) != ["query", "search interest", "increase percent"]:
            raise ValidationError(f"{f.name}: unexpected columns {list(d.columns)}")
        d.columns = ["query", "relative_interest", "growth"]
        d.insert(0, "seed_topic", f.stem.replace("related_", "").replace("_", " "))
        frames.append(d)
    if len(frames) != 7:
        raise ValidationError(f"expected 7 related-query files, found {len(frames)}")
    return pd.concat(frames, ignore_index=True)


def main() -> int:
    prof = state_profiles()
    prof.to_csv(CLEAN / "trends_state_profile.csv", index=False)
    nat = national_monthly()
    nat.to_csv(CLEAN / "trends_national_monthly.csv", index=False)
    miss = prof.isna().sum()
    print(f"Wrote trends_state_profile.csv: {prof.shape} | missing: {miss[miss > 0].to_dict()}")
    rq = related_queries()
    rq.to_csv(CLEAN / "trends_related_queries.csv", index=False)
    print(f"Wrote trends_related_queries.csv: {len(rq)} rows from {rq.seed_topic.nunique()} seeds")
    print(f"Wrote trends_national_monthly.csv: {len(nat)} rows, {nat.term.nunique()} terms")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
