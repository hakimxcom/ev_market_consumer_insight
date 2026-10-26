"""
08_build_site_bundle.py — gather the published results into one file for the website.

WHAT IT DOES
  Reads the result tables written by steps 01–06 and the cleaned data, and writes a single
  JavaScript file that sets window.F_Y002 = {...}. The website page only draws charts and tables
  from this object; it does no calculations of its own. Only results that have passed their checks
  are included: complaint results use the safety agency's own part categories, and the keyword-based
  complaint flags are left out until the hand check (07_validate_keywords.py) is done.

INPUTS   outputs/tables/*.csv, data/clean/*.csv
OUTPUT   outputs/site_data/ev_insights_data.js   (copy to the website's public/ folder)
RUN      python stage_2_analysis/08_build_site_bundle.py
"""
import json
import sys
from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import CLEAN, QUARTERS, ROOT, SITE, TABLES

sys.path.insert(0, str(ROOT / "stage_1_data"))
from states import STATES  # noqa: E402

REPO = "https://github.com/hakimxcom/ev_market_consumer_insights"


def r(x, n=2):
    return None if pd.isna(x) else round(float(x), n)


def main() -> None:
    p = pd.read_csv(CLEAN / "panel_state_quarter.csv")
    st = pd.read_csv(CLEAN / "state_table.csv").set_index("state")
    nat = pd.read_csv(TABLES / "national_quarterly.csv").set_index("quarter")
    drop = pd.read_csv(TABLES / "credit_end_drop.csv").set_index("state")
    gap = pd.read_csv(TABLES / "interest_gap.csv").set_index("state")
    used = pd.read_csv(TABLES / "used_ev_signal.csv").set_index("state")
    seg = pd.read_csv(TABLES / "segments.csv").set_index("state")
    prof = pd.read_csv(TABLES / "segment_profiles.csv").set_index("segment")
    pp = pd.read_csv(TABLES / "state_model_residuals_pre_post.csv").set_index("state")
    models = pd.read_csv(TABLES / "state_models.csv")
    panel_fe = pd.read_csv(TABLES / "panel_fe.csv")
    themes = pd.read_csv(TABLES / "nhtsa_twin_themes.csv")
    trends_nat = pd.read_csv(CLEAN / "trends_national_monthly.csv")
    events = pd.read_csv(CLEAN / "event_calendar.csv")

    w = p.pivot(index="state", columns="quarter", values="ev_share")
    q2 = p[p.quarter == "2026Q2"].set_index("state")
    seg_names = {"S1": "Urban cores", "S2": "Electric-ready", "S3": "Truck-first"}

    states = {}
    for code, name in zip(STATES.state, STATES.state_name):
        s = st.loc[code]
        states[code] = {
            "name": name,
            "ev": [r(w.loc[code, q]) for q in QUARTERS],
            "yoy": r(s.ev_share_change_yoy),
            "drop": r(drop.loc[code, "drop_pct"], 1),
            "ports": r(s.ports_per_10k_2026q2, 1),
            "income": int(s.median_hh_income),
            "truck": r(s.truck_share, 1),
            "renter": r(s.pct_renter, 1),
            "apt": r(s.pct_multiunit_5plus, 1),
            "fee": int(s.has_ev_fee_in_window),
            "zev": int(s.acc2_adopted_2025q1),
            "gas": r(q2.loc[code, "gas_regular_mean"], 2),
            "search": r(q2.loc[code, "ev_search_ratio"], 1),
            "rankAdopt": int(gap.loc[code, "rank_adoption_2026q2"]),
            "rankInterest": int(gap.loc[code, "rank_interest_ratio_2026q2"]),
            "gapFlag": "" if pd.isna(gap.loc[code, "flag"]) else gap.loc[code, "flag"],
            "usedResid": r(used.loc[code, "residual"], 1),
            "usedFlag": not pd.isna(used.loc[code, "flag"]) and used.loc[code, "flag"] != "",
            "segment": seg_names[seg.loc[code, "segment"]],
            "pre": [r(pp.loc[code, "pre_actual"]), r(pp.loc[code, "pre_predicted"])],
            "post": [r(pp.loc[code, "post_actual"]), r(pp.loc[code, "post_predicted"])],
            "detroit": r(s.detroit_share_of_ev_models, 1),
            "tesla": r(s.tesla_share_of_ev_models, 1),
        }

    plain = {
        "log_income": "Household income",
        "truck_share": "Truck and SUV share",
        "acc2_adopted_2025q1": "Adopted California's zero-emission rule",
        "pct_multiunit_5plus": "Apartment share (5+ units)",
        "pct_renter": "Renter share",
        "has_ev_fee_in_window": "Special electric car fee",
        "ports_per_10k_2026q2": "Public chargers per 10,000 people",
    }
    coef = lambda m: [{"label": plain[x.predictor], "coef": r(x.coef_pp_per_sd), "lo": r(x.ci95_low),
                       "hi": r(x.ci95_high), "p": r(x.p_value, 3)}
                      for x in models[models.model == m].itertuples()]
    fe = {x.term: {"coef": r(x.coef, 3), "lo": r(x.ci95_low, 3), "hi": r(x.ci95_high, 3), "p": r(x.p_value, 3)}
          for x in panel_fe[panel_fe.spec == "gas+search"].itertuples()}

    comp_themes = {"electrical": "Electrical system", "powertrain_propulsion": "Engine, motor and drivetrain",
                   "driver_assistance": "Driver-assist features", "brakes": "Brakes",
                   "visibility_lighting": "Visibility and lights", "body_safety_equipment": "Body, seats and airbags",
                   "steering_suspension_wheels": "Steering, suspension and wheels", "unknown_other": "Other or unknown"}
    pairs = {}
    for pair, g in themes[themes.pair != "All three pairs"].groupby("pair"):
        g = g.set_index("theme")
        pairs[pair] = {"nEV": int(g.n_ev.iloc[0]), "nGas": int(g.n_gas.iloc[0]),
                       "themes": [{"label": comp_themes[t], "ev": r(g.loc[t, "ev_share_pct"], 1),
                                   "gas": r(g.loc[t, "gas_share_pct"], 1), "p": r(g.loc[t, "p_holm"], 4)}
                                  for t in comp_themes]}

    seg_json = json.load(open(SITE / "segments.json"))
    rc = [spearmanr(g.ev_search_ratio, g.ev_share).statistic for _, g in p.groupby("quarter")]
    ev_search = trends_nat[(trends_nat.group == "B1") & (trends_nat.term == "Electric vehicle")]
    bundle = {
        "generated": date.today().isoformat(),
        "repo": REPO,
        "quarters": QUARTERS,
        "quarterLabels": ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025", "Q1 2026", "Q2 2026"],
        "national": {"ev": [r(nat.loc[q, "ev_share"]) for q in QUARTERS],
                     "bev": [r(nat.loc[q, "bev_share"]) for q in QUARTERS],
                     "phev": [r(nat.loc[q, "phev_share"]) for q in QUARTERS]},
        "searchMonthly": {"month": ev_search.month.tolist(), "value": ev_search.value.astype(int).tolist()},
        "events": [{"date": e.date, "text": e.event, "src": e.source_1} for e in events.itertuples()],
        "states": states,
        "summary": {
            "statesDown": int((st.ev_share_change_yoy < 0).sum()),
            "medianDrop": r(drop.drop_pct.median(), 1),
            "modelR2": r(models[models.model == "A"].r2.iloc[0], 2),
            "rankCorrRange": [r(min(rc), 2), r(max(rc), 2)],
        },
        "modelA": coef("A"), "modelB": coef("B"), "modelC": coef("C"),
        "panel": fe,
        "segments": {seg_names[k]: {"n": int(v.n_states), "income": int(v.median_hh_income), "truck": r(v.truck_share, 1),
                                    "ports": r(v.ports_per_10k_2026q2, 1), "fee": r(v.has_ev_fee_in_window * 100, 0),
                                    "ev": r(v.ev_share_mean, 1), "search": r(v.ev_search_ratio_mean, 1)}
                     for k, v in prof.iterrows()},
        "miPeers": seg_json["michigan_peers"],
        "complaints": pairs,
        "recall": {"id": "24V-868", "date": "2024-11-18",
                   "url": "https://static.nhtsa.gov/odi/rcl/2024/RCAK-24V868-3172.pdf"},
    }
    js = "/* Generated by stage_2_analysis/08_build_site_bundle.py — do not edit by hand. */\n"
    js += "window.F_Y002 = " + json.dumps(bundle, separators=(",", ":"), default=float) + ";\n"
    out = SITE / "ev_insights_data.js"
    out.write_text(js)
    print(f"Wrote {out.relative_to(ROOT)} ({len(js) / 1024:.1f} KB): {len(states)} states, "
          f"{len(pairs)} complaint pairs, {len(bundle['events'])} events")


if __name__ == "__main__":
    main()
