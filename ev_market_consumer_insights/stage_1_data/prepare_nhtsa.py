"""
prepare_nhtsa.py — prepare NHTSA owner complaints for the EV-vs-gas comparison (H1) and for
state EV complaint rates. Privacy first: personal fields are never loaded.

WHAT IT DOES
  1. Reads COMPLAINTS_RECEIVED_2025-2026.zip (NHTSA ODI flat file, layout CMPL.txt, tab-separated,
     no header). Only these fields are loaded: complaint ID, ODI number, make, model, model year,
     component, consumer state, received date, product type, narrative. City, VIN, and dealer
     name/phone/city/state/zip are NEVER read. Narratives are used only to compute yes/no keyword
     flags in memory; no narrative text is written to any output.
  2. Keeps vehicles (product type V), received Jan 1, 2025 – Jun 30, 2026 (same window as the
     panel), consumer state in the 50 states + DC (territories are counted and dropped).
     One complaint (ODI number) can list several components; components are pooled per complaint.
  3. Classifies each make/model as BEV, PHEV or not-EV with an explicit, documented rule
     (model-name patterns + exclusions; the file has no usable fuel-type field). The full list of
     matched models is written out so the rule can be audited.
  4. Matched twins (same maker, similar size, gas vs. EV), restricted to model years where both
     exist in the data:
        Chevrolet Equinox EV  vs  Equinox      (MY 2024–2026)
        Hyundai Ioniq 5 (+ 5 N) vs Tucson      (MY 2022–2026)
        Ford Mustang Mach-E   vs  Escape       (MY 2021–2026)
     "TUCSON" and "ESCAPE" are the plain model names; hybrid/plug-in versions filed under their own
     names are excluded, but a hybrid filed under the plain name cannot be told apart (no VIN used).
  5. Themes per complaint:
       component themes from NHTSA's own component codes (objective; no text coding), and
       keyword flags from the narrative (transparent regex; NOT validated yet — Stage III draws a
       random sample for hand-checking).

INPUTS   data/raw/nhtsa/COMPLAINTS_RECEIVED_2025-2026.zip
OUTPUTS  data/clean/nhtsa_ev_model_list.csv        make/model -> BEV/PHEV, complaint counts
         data/clean/nhtsa_twin_theme_counts.csv    per twin model: complaints, theme counts
         data/clean/nhtsa_state_complaints.csv     per state: EV complaints, all complaints
         data/interim/nhtsa_complaints_slim.csv    per complaint, NO narrative/personal fields
                                                   (kept out of the repository; aggregates only
                                                   are published)
RUN      python stage_1_data/prepare_nhtsa.py
"""
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

from states import STATES

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "data" / "raw" / "nhtsa" / "COMPLAINTS_RECEIVED_2025-2026.zip"
CLEAN = ROOT / "data" / "clean"
INTERIM = ROOT / "data" / "interim"
START, END = "20250101", "20260630"

# CMPL.txt field positions (1-based) -> names. Personal fields (13 CITY, 15 VIN, 41–45 dealer)
# are deliberately absent so pandas never reads them.
FIELDS = {1: "cmplid", 2: "odino", 4: "make", 5: "model", 6: "year", 12: "compdesc",
          14: "state", 17: "ldate", 20: "cdescr", 46: "prod_type"}
N_FIELDS = 51

# ---------------------------------------------------------------- EV classification
PHEV_PAT = re.compile(r"PLUG-IN|PHEV|\bPRIME\b|4XE|ENERGI|\bVOLT\b|PACIFICA HYBRID")
BEV_PAT = re.compile(
    r"\bEV\b|ELECTRIC|BEV\b|LIGHTNING|MACH E|IONIQ [569]|IONIQ 5 N|BOLT|\bLEAF\b|ARIYA|ID\.4|ID\. BUZZ|"
    r"BZ4X|^BZ$|SOLTERRA|PROLOGUE|ZDX|LYRIQ|OPTIQ|VISTIQ|ESCALADE IQ|HUMMER EV|E-TRON|TAYCAN|"
    r"^I[3457]\b|^IX\b|^EQ[BES]|^AMG EQ|EX30|EX90|POLESTAR|^R1[ST]$|CYBERTRUCK|^MODEL [3SXY]$|"
    r"\bEV[369]\b|CHARGER EV|^AIR$|^GRAVITY$|^OCEAN$|^VF [89]$|C40BEV|XC40BEV|G 580 EV")
EXCLUDE = {  # matched a pattern but are not light-duty EVs, or are ambiguous gas/EV names
    ("HYUNDAI", "IONIQ HYBRID"), ("HYUNDAI", "IONIQ"), ("VOLVO", "XC40"), ("LINCOLN", "CORSAIR"),
    ("FREIGHTLINER", "CASCADIA"), ("RIVIAN", "EDV"), ("GREENPOWER", "EV STAR BUS"),
    ("FLEETWOOD", "FLAIR"), ("MERCEDES-BENZ", "C400"),
}
EXCLUDE_MAKES = {"INDIAN"}  # motorcycles


def classify(make: str, model: str) -> str:
    model = re.sub(r"^REDUNDANT\s+", "", str(model).upper()).strip()
    make = str(make).upper().strip()
    if make in EXCLUDE_MAKES or (make, model) in EXCLUDE:
        return "not_ev"
    if PHEV_PAT.search(model):
        return "PHEV"
    if make in {"TESLA", "RIVIAN", "LUCID", "POLESTAR", "FISKER", "VINFAST"} or BEV_PAT.search(model):
        return "BEV"
    return "not_ev"


TWINS = [  # pair, EV models, gas models, model years
    ("Equinox", ("CHEVROLET", ["EQUINOX EV"]), ("CHEVROLET", ["EQUINOX"]), range(2024, 2027)),
    ("Ioniq 5 / Tucson", ("HYUNDAI", ["IONIQ 5", "IONIQ 5 N"]), ("HYUNDAI", ["TUCSON"]), range(2022, 2027)),
    ("Mach-E / Escape", ("FORD", ["MUSTANG MACH E"]), ("FORD", ["ESCAPE", "ESCAPE 21"]), range(2021, 2027)),
]

# ---------------------------------------------------------------- themes
COMPONENT_THEMES = {
    "electrical": r"^ELECTRICAL SYSTEM",
    "powertrain_propulsion": r"^(?:POWER TRAIN|FUEL/PROPULSION|ENGINE|HYBRID PROPULSION|FUEL SYSTEM)",
    "driver_assistance": r"^(?:FORWARD COLLISION|LANE DEPARTURE|BACK OVER|VEHICLE SPEED CONTROL)",
    "brakes": r"^(?:SERVICE BRAKES|PARKING BRAKE)",
    "steering_suspension_wheels": r"^(?:STEERING|SUSPENSION|WHEELS|TIRES)",
    "visibility_lighting": r"^(?:VISIBILITY|EXTERIOR LIGHTING)",
    "body_safety_equipment": r"^(?:STRUCTURE|LATCHES|SEATS|SEAT BELTS|AIR BAGS|EQUIPMENT|CHILD SEAT)",
    "unknown_other": r"^UNKNOWN OR OTHER",
}
KEYWORD_FLAGS = {  # narrative keyword flags (?:case-insensitive); not yet hand-validated
    "kw_dealer": r"\bDEALER(?:SHIP)?S?\b",
    "kw_cost": r"\$\s?\d|\bCOSTS?\b|\bEXPENSIVE\b|OUT OF POCKET",
    "kw_mechanic": r"\bMECHANIC|REPAIR SHOP|INDEPENDENT (?:SHOP|GARAGE|REPAIR)",
    "kw_parts_wait": r"BACK.?ORDER|\bPARTS?\b.{0,40}\b(?:WAIT|UNAVAILABLE|NOT AVAILABLE|DELAY)",
    "kw_loss_of_power": r"LOSS OF (?:MOTIVE )?POWER|LOST (?:ALL )?POWER|SHUT ?(?:S )?DOWN|\bSTALL",
    "kw_12v_battery": r"\b12 ?V(?:OLT)?\b",
    "kw_charging": r"\bCHARG(?:E|ER|ERS|ING)\b",
    "kw_cold_weather": r"\bCOLD\b|WINTER|FREEZ|BELOW ZERO|\bSNOW",
}


class ValidationError(Exception):
    pass


def load(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        if len(names) != 1:
            raise ValidationError(f"expected one file in zip, found {names}")
        with z.open(names[0]) as f:
            first = f.readline().decode("utf-8").rstrip("\n").split("\t")
        if len(first) != N_FIELDS:
            raise ValidationError(f"expected {N_FIELDS} tab-separated fields, found {len(first)}")
        d = pd.read_csv(z.open(names[0]), sep="\t", header=None, usecols=[k - 1 for k in FIELDS],
                        dtype=str, quoting=3, encoding="utf-8")
    d.columns = [FIELDS[c + 1] for c in d.columns]
    if d.cmplid.duplicated().any():
        raise ValidationError("duplicate complaint-component IDs")
    return d


def to_complaints(rows: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Filter and collapse component rows to one row per complaint (ODI number)."""
    info = {"rows_loaded": len(rows)}
    r = rows[(rows.prod_type == "V") & (rows.ldate >= START) & (rows.ldate <= END)].copy()
    info["vehicle_rows_in_window"] = len(r)
    if r.groupby("odino")[["make", "model", "year", "state", "ldate"]].nunique().gt(1).any().any():
        raise ValidationError("a complaint has conflicting vehicle/state/date across its rows")
    for theme, pat in COMPONENT_THEMES.items():
        r[theme] = r.compdesc.fillna("").str.contains(pat, regex=True)
    text = r.cdescr.fillna("").str.upper()
    for flag, pat in KEYWORD_FLAGS.items():
        r[flag] = text.str.contains(pat, regex=True)
    agg = {c: "first" for c in ["make", "model", "year", "state", "ldate"]}
    agg.update({c: "max" for c in list(COMPONENT_THEMES) + list(KEYWORD_FLAGS)})
    c = r.groupby("odino").agg(agg).reset_index()
    info["complaints_in_window"] = len(c)
    terr = ~c.state.isin(STATES.state)
    info["complaints_outside_50_states_dc_dropped"] = int(terr.sum())
    c = c[~terr].copy()
    c["model"] = c.model.str.replace(r"^redundant\s+", "", regex=True, case=False).str.upper().str.strip()
    c["powertrain"] = [classify(mk, md) for mk, md in zip(c.make, c.model)]
    c["quarter"] = pd.to_datetime(c.ldate, format="%Y%m%d").dt.to_period("Q").astype(str)
    c["twin_pair"], c["twin_side"] = None, None
    for pair, (ev_make, ev_models), (gas_make, gas_models), years in TWINS:
        yrs = {str(y) for y in years}
        ev = (c.make == ev_make) & c.model.isin(ev_models) & c.year.isin(yrs)
        gas = (c.make == gas_make) & c.model.isin(gas_models) & c.year.isin(yrs)
        c.loc[ev, ["twin_pair", "twin_side"]] = [pair, "EV"]
        c.loc[gas, ["twin_pair", "twin_side"]] = [pair, "gas"]
    return c, info


def main() -> int:
    INTERIM.mkdir(parents=True, exist_ok=True)
    c, info = to_complaints(load(ZIP))
    theme_cols = list(COMPONENT_THEMES) + list(KEYWORD_FLAGS)

    models = (c[c.powertrain != "not_ev"].groupby(["make", "model", "powertrain"]).size()
              .rename("complaints").reset_index().sort_values("complaints", ascending=False))
    models.to_csv(CLEAN / "nhtsa_ev_model_list.csv", index=False)

    tw = c[c.twin_pair.notna()]
    twins = (tw.groupby(["twin_pair", "twin_side"])
               .agg(complaints=("odino", "size"), **{t: (t, "sum") for t in theme_cols})
               .reset_index())
    twins.to_csv(CLEAN / "nhtsa_twin_theme_counts.csv", index=False)

    st = (c.assign(is_ev=c.powertrain != "not_ev")
            .groupby("state").agg(complaints_all=("odino", "size"), complaints_ev=("is_ev", "sum"))
            .reindex(STATES.state, fill_value=0).reset_index())
    st.to_csv(CLEAN / "nhtsa_state_complaints.csv", index=False)

    c.drop(columns=["ldate"]).to_csv(INTERIM / "nhtsa_complaints_slim.csv", index=False)

    print(" | ".join(f"{k}: {v:,}" for k, v in info.items()))
    print(f"EV complaints: {(c.powertrain != 'not_ev').sum():,} "
          f"(BEV {(c.powertrain == 'BEV').sum():,}, PHEV {(c.powertrain == 'PHEV').sum():,}) "
          f"from {len(models)} make/models")
    print(twins[["twin_pair", "twin_side", "complaints"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
