"""
prepare_alliance.py — build the outcome table (state x quarter) from the Alliance for
Automotive Innovation "Get Connected" EV Quarterly Reports, 2025 Q1 – 2026 Q2.

WHAT IT DOES
  For each quarterly report it reads two state tables:
    1. "New Light-Duty Vehicle Registrations By Powertrain" (quarter, not year-to-date):
       PHEV, BEV, FCEV and EV-total share of new registrations, in percent.
    2. "Vehicles in Operation and Charging (Infrastructure) by State": public charging
       ports (Level 2, DC fast, hydrogen stations, total), EVs as % of all registered
       light-duty vehicles, state share of U.S. EVs, EVs per charger, EVs per 10K residents.
  2025 Q1 prints both tables as images, so those come from hand-transcribed CSVs in
  data/manual/ (see the README there). All other quarters are parsed from the PDF text.

  It stops with an error (never drops or fixes rows silently) if any check fails:
    - exactly the 50 states + DC + U.S. in every table, no duplicates
    - PHEV + BEV + FCEV = EV total (within 0.02 pts, printed rounding)
    - Level 2 + DC fast + H2 = total ports, and state ports sum exactly to the U.S. row
    - state shares of U.S. EVs sum to 100 (within 0.05)
    - 2025 Q1 transcription = 2026 Q1 value minus printed YoY change (within 0.02 pts)
    - 2025 Q2 parsed values = 2026 Q2 value minus printed YoY change (within 0.02 pts)

  Not included on purpose: hybrid share (Alliance reports it nationally only), and raw EV
  counts by state (not printed; evs_per_10k_res is the precise per-state measure).

INPUTS   data/raw/alliance/Get_Connected_EV_Quarterly_Report_<YYYY>_Q<n>.pdf  (6 files)
         data/manual/alliance_2025Q1_registrations_transcribed.csv
         data/manual/alliance_2025Q1_vio_charging_transcribed.csv
OUTPUT   data/clean/alliance_state_quarter.csv  (312 rows: 52 geographies x 6 quarters;
         the U.S. row is kept for reference and flagged with is_us = True)
REQUIRES pdftotext (poppler-utils) on the PATH; pandas.
RUN      python stage_1_data/prepare_alliance.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "alliance"
MANUAL = ROOT / "data" / "manual"
OUT = ROOT / "data" / "clean" / "alliance_state_quarter.csv"

QUARTERS = ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"]
STATES = (
    "AK AL AR AZ CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC "
    "ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY"
).split()
EXPECTED = set(STATES) | {"U.S."}

REG_COLS = ["phev", "bev", "fcev", "ev_total", "d_phev", "d_bev", "d_fcev", "d_ev_total"]
VIO_COLS = ["l2_ports", "dcfc_ports", "h2_stations", "total_ports", "ev_pct_of_vio",
            "share_of_us_evs", "evs_per_charger", "evs_per_10k_res"]


class ValidationError(Exception):
    """Raised when a source table fails a check. The pipeline must stop."""


# ---------------------------------------------------------------- PDF text helpers
def pdf_path(quarter: str) -> Path:
    return RAW / f"Get_Connected_EV_Quarterly_Report_{quarter[:4]}_{quarter[4:]}.pdf"


def page_text(pdf: Path, page: int) -> str:
    return subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
                          capture_output=True, text=True, check=True).stdout


def n_pages(pdf: Path) -> int:
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def find_page(pdf: Path, title_regex: str) -> int:
    """Return the first page whose text matches title_regex (case-insensitive)."""
    for p in range(1, n_pages(pdf) + 1):
        if re.search(title_regex, page_text(pdf, p), flags=re.I):
            return p
    raise ValidationError(f"{pdf.name}: no page matches /{title_regex}/")


# ---------------------------------------------------------------- parsers (pure functions)
_NUM = r"(-?\d+\.\d+)"
_REG_ROW = re.compile(r"^\s*(U\.S\.|[A-Z]{2})\*?\s+" + r"\s+".join([_NUM + "%"] * 4)
                      + r"\s+" + r"\s+".join([_NUM + "%?"] * 4))
_INT = r"(\d[\d,]*)"
_VIO_ROW = re.compile(r"^\s*(U\.S\.|[A-Z]{2})\*?\s+" + _INT + r"\s+" + _INT + r"\s+(?:" + _INT + r"\s+)?"
                      + _INT + r"\s+(\d+\.\d+)%\s+(\d+\.\d+)%\s+" + _INT + r"\s+(\d+(?:\.\d+)?)")


def parse_registrations(text: str) -> pd.DataFrame:
    """Parse the FIRST state table on the page (quarterly); stop at the first repeated state,
    which marks the start of a second (year-to-date) table on the same page."""
    rows, seen = [], set()
    for line in text.replace(" %", "%").splitlines():
        m = _REG_ROW.match(line)
        if not m:
            continue
        if m.group(1) in seen:
            break
        seen.add(m.group(1))
        rows.append([m.group(1)] + [float(x) for x in m.groups()[1:]])
    return pd.DataFrame(rows, columns=["state"] + REG_COLS)


def parse_vio(text: str) -> pd.DataFrame:
    def i(x):
        return 0 if x is None else int(x.replace(",", ""))
    rows, seen = [], set()
    for line in text.splitlines():
        m = _VIO_ROW.match(line)
        if not m or m.group(1) in seen:
            continue
        g = m.groups()
        seen.add(g[0])
        rows.append([g[0], i(g[1]), i(g[2]), i(g[3]), i(g[4]), float(g[5]), float(g[6]), i(g[7]), float(g[8])])
    return pd.DataFrame(rows, columns=["state"] + VIO_COLS)


# ---------------------------------------------------------------- checks
def check_registrations(df: pd.DataFrame, label: str) -> None:
    _check_keys(df, label)
    gap = (df.phev + df.bev + df.fcev - df.ev_total).abs()
    if (gap > 0.02).any():
        raise ValidationError(f"{label}: PHEV+BEV+FCEV != EV total for {df.state[gap > 0.02].tolist()}")


def check_vio(df: pd.DataFrame, label: str) -> None:
    _check_keys(df, label)
    bad = df.state[df.l2_ports + df.dcfc_ports + df.h2_stations != df.total_ports].tolist()
    if bad:
        raise ValidationError(f"{label}: L2+DC+H2 != total ports for {bad}")
    states, us = df[df.state != "U.S."], df[df.state == "U.S."].iloc[0]
    for c in ["l2_ports", "dcfc_ports", "h2_stations", "total_ports"]:
        if states[c].sum() != us[c]:
            raise ValidationError(f"{label}: state {c} sum {states[c].sum()} != U.S. row {us[c]}")
    if abs(states.share_of_us_evs.sum() - 100) > 0.05:
        raise ValidationError(f"{label}: state shares of U.S. EVs sum to {states.share_of_us_evs.sum():.2f}")


def _check_keys(df: pd.DataFrame, label: str) -> None:
    got = set(df.state)
    if df.state.duplicated().any() or got != EXPECTED:
        raise ValidationError(f"{label}: missing {sorted(EXPECTED - got)}, extra {sorted(got - EXPECTED)}, "
                              f"duplicates {df.state[df.state.duplicated()].tolist()}")


def check_yoy(earlier: pd.DataFrame, later: pd.DataFrame, label: str, tol: float = 0.02) -> None:
    """earlier quarter value must equal later value minus the later report's printed YoY change."""
    e, l = earlier.set_index("state"), later.set_index("state")
    for c in ["phev", "bev", "ev_total"]:
        gap = (l[c] - l["d_" + c] - e[c]).abs()
        if (gap > tol).any():
            raise ValidationError(f"{label}: {c} disagrees with next year's YoY change for "
                                  f"{gap[gap > tol].round(2).to_dict()}")


# ---------------------------------------------------------------- load one quarter
def load_quarter(q: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if q == "2025Q1":
        reg = pd.read_csv(MANUAL / "alliance_2025Q1_registrations_transcribed.csv")
        vio = pd.read_csv(MANUAL / "alliance_2025Q1_vio_charging_transcribed.csv")
    else:
        pdf = pdf_path(q)
        reg = parse_registrations(page_text(pdf, find_page(pdf, r"Quarter 20\d\d, New Light-Duty Vehicle")))
        vio = parse_vio(page_text(pdf, find_page(pdf, r"Public Charging Outlets And Regist")))
    check_registrations(reg, f"{q} registrations")
    check_vio(vio, f"{q} charging/VIO")
    return reg, vio


def main() -> int:
    regs, frames = {}, []
    for q in QUARTERS:
        reg, vio = load_quarter(q)
        regs[q] = reg
        m = reg[["state", "phev", "bev", "fcev", "ev_total"]].merge(vio, on="state", how="outer",
                                                                    validate="1:1", indicator=True)
        if not (m._merge == "both").all():
            raise ValidationError(f"{q}: registration and VIO tables do not match on state")
        frames.append(m.drop(columns="_merge").assign(quarter=q))
        print(f"{q}: 50 states + DC + U.S. OK ({len(m)} rows incl. U.S.)")

    check_yoy(regs["2025Q1"], regs["2026Q1"], "2025Q1 transcription vs 2026Q1 report")
    check_yoy(regs["2025Q2"], regs["2026Q2"], "2025Q2 parse vs 2026Q2 report")
    print("Year-over-year cross-checks: OK")

    out = (pd.concat(frames, ignore_index=True)
           .rename(columns={"phev": "phev_share", "bev": "bev_share", "fcev": "fcev_share",
                            "ev_total": "ev_share"}))
    out.insert(0, "is_us", out.state.eq("U.S."))
    out = out[["state", "quarter", "is_us", "ev_share", "bev_share", "phev_share", "fcev_share",
               "l2_ports", "dcfc_ports", "h2_stations", "total_ports",
               "ev_pct_of_vio", "share_of_us_evs", "evs_per_charger", "evs_per_10k_res"]]
    if out.duplicated(["state", "quarter"]).any():
        raise ValidationError("duplicate state/quarter keys in output")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.sort_values(["state", "quarter"]).to_csv(OUT, index=False)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(out)} rows")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
