"""
03_panel_fe.py — within-state panel: when a state's gas price or EV search interest moves more
than the national quarter-to-quarter change, does its EV share move too?

WHAT IT DOES
  Unit: state x quarter (306 rows). Two-way fixed effects (state and quarter dummies):
      ev_share[s,q] = b1 * gas_regular_mean[s,q] + b2 * ev_search_ratio[s,q]
                      + state effect[s] + quarter effect[q] + error
  State effects absorb everything constant within a state (income, housing, climate, culture);
  quarter effects absorb everything national in that quarter (federal credit end, national
  launches, national gas moves). So b1, b2 use only DIFFERENCES between states in how much
  their gas price / search moved. The federal credit's effect is NOT estimable here (absorbed
  by quarter effects) and is shown descriptively in 01_describe.py.
  Standard errors are clustered by state (51 clusters).
  Variants: gas only; search only; both; both with the outcome lagged search (search one quarter
  earlier, 5 quarters of data) to check whether interest LEADS registrations.
  Also: the credit-end drop (2025 Q3 -> Q4) by state vs. state characteristics, as a descriptive
  table (which kinds of states fell most).

INPUTS   data/clean/panel_state_quarter.csv, state_table.csv
OUTPUTS  outputs/tables/panel_fe.csv, credit_end_drop.csv
         outputs/site_data/panel.json
RUN      python stage_2_analysis/03_panel_fe.py
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from common import TABLES, panel, state_table, write_json


def twfe(df: pd.DataFrame, rhs: str):
    m = smf.ols(f"ev_share ~ {rhs} + C(state) + C(quarter)", data=df)
    return m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df.state)[0]})


def main() -> None:
    p = panel().sort_values(["state", "quarter"]).copy()
    p["ev_search_ratio_lag1"] = p.groupby("state").ev_search_ratio.shift(1)
    p["gas_regular_lag1"] = p.groupby("state").gas_regular_mean.shift(1)
    specs = {
        "gas": "gas_regular_mean",
        "search": "ev_search_ratio",
        "gas+search": "gas_regular_mean + ev_search_ratio",
        "lagged gas+search": "gas_regular_lag1 + ev_search_ratio_lag1",
    }
    rows, site = [], {}
    for name, rhs in specs.items():
        d = p.dropna(subset=[t.strip() for t in rhs.split("+")])
        res = twfe(d, rhs)
        for x in [t.strip() for t in rhs.split("+")]:
            lo, hi = res.conf_int().loc[x]
            rows.append({"spec": name, "term": x, "coef": round(res.params[x], 4), "se_cluster": round(res.bse[x], 4),
                         "ci95_low": round(lo, 4), "ci95_high": round(hi, 4), "p_value": round(res.pvalues[x], 4),
                         "n": int(res.nobs), "within_note": "state + quarter fixed effects"})
        site[name] = {x.strip(): [round(res.params[x.strip()], 3), round(res.pvalues[x.strip()], 3)]
                      for x in rhs.split("+")}
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "panel_fe.csv", index=False)

    # credit-end drop by state
    w = p.pivot(index="state", columns="quarter", values="ev_share")
    drop = pd.DataFrame({"q3_2025": w["2025Q3"], "q4_2025": w["2025Q4"]})
    drop["drop_pp"] = (drop.q4_2025 - drop.q3_2025).round(2)
    drop["drop_pct"] = (drop.drop_pp / drop.q3_2025 * 100).round(1)
    s = state_table().set_index("state")
    drop = drop.join(s[["median_hh_income", "truck_share", "acc2_adopted_2025q1", "ports_per_10k_2026q2"]])
    drop.sort_values("drop_pct").to_csv(TABLES / "credit_end_drop.csv")
    corr = drop[["drop_pct", "median_hh_income", "truck_share", "acc2_adopted_2025q1",
                 "ports_per_10k_2026q2", "q3_2025"]].corr()["drop_pct"].round(2)

    write_json("panel", {"specs": site, "note": "Two-way fixed effects; SEs clustered by state; n = 306 (255 lagged)",
                         "credit_end_drop_pct": drop.drop_pct.to_dict()})
    pd.set_option("display.width", 160)
    print(out[["spec", "term", "coef", "ci95_low", "ci95_high", "p_value", "n"]].to_string(index=False))
    print(f"\nQ3->Q4 2025 relative drop: median {drop.drop_pct.median()}%, "
          f"range {drop.drop_pct.min()}% to {drop.drop_pct.max()}% | Michigan {drop.loc['MI', 'drop_pct']}%")
    print("Correlation of relative drop with state traits:", corr.drop("drop_pct").to_dict())


if __name__ == "__main__":
    main()
