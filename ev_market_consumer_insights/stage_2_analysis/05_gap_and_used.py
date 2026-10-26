"""
05_gap_and_used.py — (1) where EV search interest and EV adoption diverge, and (2) a signal of
EV stock growing faster than new-EV sales would suggest (possible used/inflow activity).

WHAT IT DOES
  1. Interest-to-adoption gap, 2026 Q2 and full period:
       gap = rank on EV share of new registrations - rank on EV search interest
       (positive = more interest than adoption; ranks 1 = highest, 51 states)
     computed twice: interest measured by the EV search ratio (main) and by EV share of the four
     Group A terms (robustness, quarterly only). A state is flagged only if |gap| >= 10 ranks,
     with the same sign, under BOTH 2026 Q2 measures AND over the full period (persistence rule:
     one-quarter search blips in small states, e.g. Wyoming, are not flagged).
     Known artifact noted in the output: Indiana's 2026 Q2 EV share was lifted by fleet
     registrations (128 in Q1 -> 3,080 in Q2, per the Alliance 2026 Q2 report).
  2. Used-EV signal (rate-based):
       y = growth in EVs in operation per 10K residents, 2025 Q1 -> 2026 Q2
       x = mean EV share of new registrations
     Fit y = a + b*x (OLS); residual = actual - fitted, in EVs per 10K. States with residuals in
     the top 10% are flagged "stock grew faster than new sales suggest" — consistent with used
     EV purchases, people moving in with EVs, or fleet re-registration; NOT a count of used sales.
     Caveat: new-vehicle sales per resident differ by state, which also moves this residual.
     Two Alliance reports print EVs per 10K as whole numbers (2025 Q3, 2026 Q2), so residuals
     under ~1 per 10K are noise.

INPUTS   data/clean/panel_state_quarter.csv, state_table.csv
OUTPUTS  outputs/tables/interest_gap.csv, used_ev_signal.csv
         outputs/site_data/interest_gap.json, used_ev_signal.json
RUN      python stage_2_analysis/05_gap_and_used.py
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import TABLES, panel, state_table, write_json

FLAG_RANKS = 10


def rank(s: pd.Series) -> pd.Series:
    return s.rank(ascending=False, method="min").astype(int)


def main() -> None:
    p = panel()
    q = p[p.quarter == "2026Q2"].set_index("state")
    st = state_table().set_index("state")
    gap = pd.DataFrame({
        "ev_share_2026q2": q.ev_share,
        "rank_adoption_2026q2": rank(q.ev_share),
        "rank_interest_ratio_2026q2": rank(q.ev_search_ratio),
        "rank_interest_share4_2026q2": rank(q.ev_search_share4),
        "rank_adoption_full": rank(st.ev_share_mean),
        "rank_interest_ratio_full": rank(st.ev_search_ratio_full),
    })
    gap["gap_ratio_2026q2"] = gap.rank_adoption_2026q2 - gap.rank_interest_ratio_2026q2
    gap["gap_share4_2026q2"] = gap.rank_adoption_2026q2 - gap.rank_interest_share4_2026q2
    gap["gap_ratio_full"] = gap.rank_adoption_full - gap.rank_interest_ratio_full
    both = (gap.gap_ratio_2026q2.abs() >= FLAG_RANKS) & (gap.gap_share4_2026q2.abs() >= FLAG_RANKS) \
        & (gap.gap_ratio_full.abs() >= FLAG_RANKS) \
        & (np.sign(gap.gap_ratio_2026q2) == np.sign(gap.gap_share4_2026q2)) \
        & (np.sign(gap.gap_ratio_2026q2) == np.sign(gap.gap_ratio_full))
    gap["flag"] = np.where(both & (gap.gap_ratio_2026q2 > 0), "interest > adoption",
                           np.where(both, "adoption > interest", ""))
    gap["note"] = ""
    gap.loc["IN", "note"] = "2026 Q2 EV share lifted by fleet registrations (128 -> 3,080; Alliance 2026 Q2)"
    gap.sort_values("gap_ratio_2026q2", ascending=False).to_csv(TABLES / "interest_gap.csv")

    u = st[["ev_share_mean", "evs_per_10k_start", "evs_per_10k_end", "ev_stock_growth_per_10k"]].copy()
    res = sm.OLS(u.ev_stock_growth_per_10k, sm.add_constant(u.ev_share_mean)).fit(cov_type="HC3")
    u["fitted"] = res.fittedvalues.round(2)
    u["residual"] = res.resid.round(2)
    cut = u.residual.quantile(0.9)
    u["flag"] = np.where(u.residual >= cut, "stock grew faster than new sales suggest", "")
    u.sort_values("residual", ascending=False).to_csv(TABLES / "used_ev_signal.csv")

    write_json("interest_gap", {"flag_rule": f"|rank gap| >= {FLAG_RANKS} under both 2026 Q2 search measures and over the full period",
                                "states": gap.reset_index().to_dict("records")})
    write_json("used_ev_signal", {"slope_per_pp": round(res.params.ev_share_mean, 3), "r2": round(res.rsquared, 3),
                                  "states": u.reset_index().to_dict("records"),
                                  "caution": "A signal, not a count of used purchases."})

    print("Flagged gaps (both measures):")
    print(gap[gap.flag != ""][["ev_share_2026q2", "rank_adoption_2026q2", "rank_interest_ratio_2026q2",
                               "rank_interest_share4_2026q2", "gap_ratio_full", "flag"]].to_string())
    print("Michigan:", gap.loc["MI", ["rank_adoption_2026q2", "rank_interest_ratio_2026q2",
                                      "rank_interest_share4_2026q2", "gap_ratio_full"]].to_dict())
    print(f"\nUsed-EV signal: growth per 10K = {res.params.const:.1f} + {res.params.ev_share_mean:.2f} x EV share "
          f"(R2 {res.rsquared:.2f})")
    print(u.sort_values("residual", ascending=False).head(6)[["ev_share_mean", "ev_stock_growth_per_10k",
                                                               "fitted", "residual"]].to_string())
    print("Michigan:", u.loc["MI", ["ev_stock_growth_per_10k", "fitted", "residual"]].to_dict())


if __name__ == "__main__":
    main()
