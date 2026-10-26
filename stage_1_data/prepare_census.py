"""
prepare_census.py — build one row per state (50 + DC) of Census constants.

WHAT IT DOES
  Reads three Census downloads and keeps only what the study uses:
    - Population (Vintage 2025 estimates): July 1, 2024 and July 1, 2025 resident population.
    - Median household income, 2024 ACS 1-year (B19013), with its margin of error.
    - Housing, 2024 ACS 1-year (DP04): % renter-occupied households (with margin of error),
      % of housing units in buildings with 2+ units and with 5+ units, % single-family
      (1-unit detached + attached), % mobile homes.
  Puerto Rico and regional/national rows are dropped. Checks (stop on failure):
    - exactly 50 states + DC in every source, no duplicates, no blank values
    - state populations sum exactly to the U.S. row (population file)
    - owner % + renter % = 100 and housing-type categories sum to 100 (+/-0.3) in every state
    - renter % recomputed from counts matches the printed % (+/-0.1)

INPUTS   data/raw/census/NST-EST2025-ALLDATA.csv   (census.gov, state population estimates)
         data/raw/census/ACSDT1Y2024.B19013.csv     (data.census.gov, geography = all states)
         data/raw/census/ACSDP1Y2024.DP04.csv       (data.census.gov, geography = all states)
OUTPUT   data/clean/census_state.csv  (51 rows)
RUN      python stage_1_data/prepare_census.py
"""
import sys
from pathlib import Path

import pandas as pd

from states import STATES, to_abbr

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "census"
OUT = ROOT / "data" / "clean" / "census_state.csv"


class ValidationError(Exception):
    pass


def _num(x) -> float:
    s = str(x).replace(",", "").replace("±", "").replace("%", "").strip()
    return float(s)


def _check_51(df: pd.DataFrame, label: str) -> None:
    if len(df) != 51 or not df.state.is_unique or set(df.state) != set(STATES.state):
        raise ValidationError(f"{label}: expected 50 states + DC once each, got {len(df)} rows")
    if df.isna().any().any():
        raise ValidationError(f"{label}: blank values in {df.columns[df.isna().any()].tolist()}")


def load_population(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, encoding="latin-1")
    us = d[d.SUMLEV == 10].iloc[0]
    st = d[(d.SUMLEV == 40) & (d.NAME != "Puerto Rico")]
    for y in (2024, 2025):
        if st[f"POPESTIMATE{y}"].sum() != us[f"POPESTIMATE{y}"]:
            raise ValidationError(f"population {y}: states do not sum to the U.S. row")
    out = pd.DataFrame({"state": to_abbr(st.NAME, "population"),
                        "pop_2024": st.POPESTIMATE2024.astype(int).values,
                        "pop_2025": st.POPESTIMATE2025.astype(int).values})
    _check_51(out, "population")
    return out


def _wide_profile(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """data.census.gov 'all states' CSVs are wide: one row per line item, columns 'State!!Measure'."""
    d = pd.read_csv(path, dtype=str)
    d.iloc[:, 0] = d.iloc[:, 0].str.strip()
    names = sorted({c.split("!!")[0] for c in d.columns[1:]} - {"Puerto Rico"})
    return d, names


def load_income(path: Path) -> pd.DataFrame:
    d, names = _wide_profile(path)
    row = d.iloc[0]
    if "Median household income" not in row.iloc[0]:
        raise ValidationError("B19013: first row is not median household income")
    out = pd.DataFrame({"state_name": names,
                        "median_hh_income": [_num(row[f"{n}!!Estimate"]) for n in names],
                        "median_hh_income_moe": [_num(row[f"{n}!!Margin of Error"]) for n in names]})
    out.insert(0, "state", to_abbr(out.state_name, "B19013"))
    out = out.drop(columns="state_name")
    _check_51(out, "B19013")
    return out


def load_housing(path: Path) -> pd.DataFrame:
    d, names = _wide_profile(path)
    labels = d.iloc[:, 0].tolist()

    def row_after(section: str, label: str) -> int:
        start = labels.index(section)
        return start + 1 + labels[start + 1:].index(label)

    r = {k: row_after(sec, lab) for k, sec, lab in [
        ("occ", "HOUSING TENURE", "Occupied housing units"),
        ("owner", "HOUSING TENURE", "Owner-occupied"),
        ("renter", "HOUSING TENURE", "Renter-occupied"),
        ("u1d", "UNITS IN STRUCTURE", "1-unit, detached"),
        ("u1a", "UNITS IN STRUCTURE", "1-unit, attached"),
        ("u2", "UNITS IN STRUCTURE", "2 units"),
        ("u34", "UNITS IN STRUCTURE", "3 or 4 units"),
        ("u59", "UNITS IN STRUCTURE", "5 to 9 units"),
        ("u1019", "UNITS IN STRUCTURE", "10 to 19 units"),
        ("u20", "UNITS IN STRUCTURE", "20 or more units"),
        ("mobile", "UNITS IN STRUCTURE", "Mobile home"),
        ("boat", "UNITS IN STRUCTURE", "Boat, RV, van, etc."),
    ]}
    recs = []
    for n in names:
        pct = {k: _num(d.loc[i, f"{n}!!Percent"]) for k, i in r.items() if k != "occ"}
        renter_n, occ_n = _num(d.loc[r["renter"], f"{n}!!Estimate"]), _num(d.loc[r["occ"], f"{n}!!Estimate"])
        if abs(pct["owner"] + pct["renter"] - 100) > 0.11:
            raise ValidationError(f"DP04 {n}: owner + renter = {pct['owner'] + pct['renter']}")
        units = sum(pct[k] for k in ["u1d", "u1a", "u2", "u34", "u59", "u1019", "u20", "mobile", "boat"])
        if abs(units - 100) > 0.3:
            raise ValidationError(f"DP04 {n}: housing-type categories sum to {units}")
        if abs(renter_n / occ_n * 100 - pct["renter"]) > 0.1:
            raise ValidationError(f"DP04 {n}: renter % does not match counts")
        recs.append({"state_name": n,
                     "pct_renter": pct["renter"],
                     "pct_renter_moe": _num(d.loc[r["renter"], f"{n}!!Percent Margin of Error"]),
                     "pct_multiunit_2plus": round(sum(pct[k] for k in ["u2", "u34", "u59", "u1019", "u20"]), 1),
                     "pct_multiunit_5plus": round(sum(pct[k] for k in ["u59", "u1019", "u20"]), 1),
                     "pct_single_family": round(pct["u1d"] + pct["u1a"], 1),
                     "pct_mobile_home": pct["mobile"]})
    out = pd.DataFrame(recs)
    out.insert(0, "state", to_abbr(out.state_name, "DP04"))
    out = out.drop(columns="state_name")
    _check_51(out, "DP04")
    return out


def main() -> int:
    pop = load_population(RAW / "NST-EST2025-ALLDATA.csv")
    inc = load_income(RAW / "ACSDT1Y2024.B19013.csv")
    hou = load_housing(RAW / "ACSDP1Y2024.DP04.csv")
    out = STATES.copy()
    for part, label in [(pop, "population"), (inc, "income"), (hou, "housing")]:
        out = out.merge(part, on="state", how="left", validate="1:1")
        if out.isna().any().any():
            raise ValidationError(f"join with {label} left blanks")
    _check_51(out, "census_state")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(out)} rows, {out.shape[1]} columns")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
