"""
02_state_models.py — cross-sectional models: which state characteristics go with higher EV share
of new registrations? (H2b housing, H4 policy, H5 charging, H6 trucks, plus income.)

WHAT IT DOES
  Unit: 51 states. Outcome: mean EV share of new registrations over the 6 quarters (percent).
  Ordinary least squares with HC3 robust standard errors (good for small samples). All predictors
  are standardized (z-scores) so coefficients read as "pp of EV share per 1 SD of the predictor".
  With n = 51, each model uses at most 5 predictors.
    Model A (structural):  log income, % units in 5+ unit buildings, truck share, EV fee (0/1)
    Model B (adds charging): Model A + public ports per 10K residents
    Model C (policy check): Model A with ACC II adoption instead of the EV fee
  Renter share is not entered alongside 5+ units (correlation 0.87); Model A is re-run with renter
  share instead as a check (table row "A_renter").
  Caution printed with results: ports follow EV demand as much as they drive it (reverse
  causality), so Model B's ports coefficient is an association, not an effect.
  Robustness: Model A without California and DC (the two highest-EV geographies), "A_noCA_DC".
  Also writes each state's predicted vs. actual EV share from Model A (residual = actual -
  predicted: positive = more EVs than its income, housing, trucks and fee status would suggest).
  Pre/post check: Model A re-fit separately on mean EV share before the federal credit ended
  (2025 Q1–Q3) and after (2025 Q4 – 2026 Q2); residuals for every state in both periods
  (state_model_residuals_pre_post.csv) show whose over/under-performance depended on the credit.
  Also reports pairwise correlations and the variance inflation factor (VIF) for each model.

INPUTS   data/clean/state_table.csv
OUTPUTS  outputs/tables/state_models.csv, state_correlations.csv, state_model_residuals.csv,
         state_model_residuals_pre_post.csv
         outputs/site_data/state_models.json
RUN      python stage_2_analysis/02_state_models.py
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import TABLES, panel, state_table, write_json

LABELS = {
    "log_income": "Median household income (log)",
    "pct_multiunit_5plus": "% homes in 5+ unit buildings",
    "pct_renter": "% renter households",
    "truck_share": "Truck/SUV share of registrations",
    "has_ev_fee_in_window": "Special EV registration fee",
    "acc2_adopted_2025q1": "Adopted ACC II (ZEV rule)",
    "ports_per_10k_2026q2": "Public charging ports per 10K residents",
}
MODELS = {
    "A": ["log_income", "pct_multiunit_5plus", "truck_share", "has_ev_fee_in_window"],
    "A_renter": ["log_income", "pct_renter", "truck_share", "has_ev_fee_in_window"],
    "B": ["log_income", "pct_multiunit_5plus", "truck_share", "has_ev_fee_in_window", "ports_per_10k_2026q2"],
    "C": ["log_income", "pct_multiunit_5plus", "truck_share", "acc2_adopted_2025q1"],
}


def fit(df: pd.DataFrame, y: str, xs: list[str]):
    z = df[xs].apply(lambda c: (c - c.mean()) / c.std(ddof=0))
    X = sm.add_constant(z)
    res = sm.OLS(df[y], X).fit(cov_type="HC3")
    vif = {x: variance_inflation_factor(X.values, i + 1) for i, x in enumerate(xs)}
    return res, vif


def main() -> None:
    s = state_table().copy()
    s["log_income"] = np.log(s.median_hh_income)
    y = "ev_share_mean"
    rows, site = [], {}
    runs = [(n, xs, s) for n, xs in MODELS.items()]
    runs.append(("A_noCA_DC", MODELS["A"], s[~s.state.isin(["CA", "DC"])]))
    for name, xs, data in runs:
        res, vif = fit(data, y, xs)
        if name == "A":
            resid = pd.DataFrame({"state": data.state, "actual": data[y].round(2),
                                  "predicted": res.fittedvalues.round(2), "residual": res.resid.round(2)})
            resid["residual_rank"] = resid.residual.rank(ascending=False, method="min").astype(int)
            resid.sort_values("residual").to_csv(TABLES / "state_model_residuals.csv", index=False)
        for x in xs:
            lo, hi = res.conf_int().loc[x]
            rows.append({"model": name, "predictor": x, "label": LABELS[x],
                         "coef_pp_per_sd": round(res.params[x], 3), "se_hc3": round(res.bse[x], 3),
                         "ci95_low": round(lo, 3), "ci95_high": round(hi, 3), "p_value": round(res.pvalues[x], 4),
                         "vif": round(vif[x], 2), "n": int(res.nobs), "r2": round(res.rsquared, 3),
                         "adj_r2": round(res.rsquared_adj, 3)})
        site[name] = {"r2": round(res.rsquared, 3), "n": int(res.nobs),
                      "coefs": {LABELS[x]: [round(res.params[x], 2), round(res.pvalues[x], 3)] for x in xs}}
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "state_models.csv", index=False)

    w = panel().pivot(index="state", columns="quarter", values="ev_share").loc[s.state]
    pp = pd.DataFrame({"state": s.state.values})
    for label, qs in [("pre", ["2025Q1", "2025Q2", "2025Q3"]), ("post", ["2025Q4", "2026Q1", "2026Q2"])]:
        data = s.assign(**{y: w[qs].mean(axis=1).values})
        res, _ = fit(data, y, MODELS["A"])
        pp[f"{label}_actual"] = data[y].round(2).values
        pp[f"{label}_predicted"] = np.asarray(res.fittedvalues).round(2)
        pp[f"{label}_residual"] = np.asarray(res.resid).round(2)
        pp[f"{label}_r2"] = round(res.rsquared, 3)
    pp["residual_change"] = (pp.post_residual - pp.pre_residual).round(2)
    pp.sort_values("residual_change").to_csv(TABLES / "state_model_residuals_pre_post.csv", index=False)

    cols = [y, "log_income", "pct_multiunit_5plus", "pct_renter", "truck_share", "has_ev_fee_in_window",
            "acc2_adopted_2025q1", "ports_per_10k_2026q2", "ev_search_ratio_mean", "gas_regular_mean"]
    corr = s[cols].corr().round(2)
    corr.to_csv(TABLES / "state_correlations.csv")
    write_json("state_models", {"outcome": "Mean EV share of new registrations, 2025 Q1 – 2026 Q2 (%)",
                                "units": "pp per 1 standard deviation; HC3 robust SEs; n = 51",
                                "models": site,
                                "caution": "Associations only. Charging ports follow EV demand as much as they drive it."})

    pd.set_option("display.width", 160)
    print(out[["model", "predictor", "coef_pp_per_sd", "ci95_low", "ci95_high", "p_value", "vif", "r2"]]
          .to_string(index=False))
    r = pd.read_csv(TABLES / "state_model_residuals.csv").set_index("state")
    print("\nModel A residuals (actual - predicted, pp): lowest", r.residual.head(4).to_dict(),
          "| highest", r.residual.tail(4).to_dict())
    print("Michigan:", r.loc["MI"].to_dict())
    pp = pd.read_csv(TABLES / "state_model_residuals_pre_post.csv").set_index("state")
    print("Michigan pre/post credit:", pp.loc["MI", ["pre_actual", "pre_predicted", "pre_residual", "post_actual",
                                                      "post_predicted", "post_residual"]].to_dict())
    print("\nCorrelation with mean EV share:")
    print(corr[y].drop(y).sort_values().to_string())


if __name__ == "__main__":
    main()
