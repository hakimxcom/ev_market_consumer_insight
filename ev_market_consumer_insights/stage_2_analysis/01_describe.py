"""
01_describe.py — descriptive results: how EV share of new registrations moved nationally and by
state from 2025 Q1 to 2026 Q2, and how search interest and gas prices moved alongside.

WHAT IT DOES
  - National series (Alliance U.S. row): EV, BEV, PHEV share by quarter; change Q2->Q3 2025
    (pre-deadline rush) and Q3->Q4 2025 (after the federal credit ended Sept 30, 2025).
  - State changes: 2026 Q2 vs 2025 Q2 (year over year, percentage points) for all 51; counts of
    states up/down; ranks for Michigan.
  - Quarterly averages across states of the EV search ratio and gas price.
  - National monthly search series (Group B1 EV topic) as the timing check around the credit end.
  All shares are percent; changes in percentage points (pp).

INPUTS   data/clean/alliance_state_quarter.csv, panel_state_quarter.csv, trends_national_monthly.csv,
         event_calendar.csv
OUTPUTS  outputs/tables/national_quarterly.csv, state_yoy_change.csv, quarterly_means.csv
         outputs/figures/national_ev_share.png
         outputs/site_data/national.json, states_quarterly.json, events.json
RUN      python stage_2_analysis/01_describe.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from common import CLEAN, FIGURES, QUARTERS, TABLES, alliance, panel, write_json  # noqa: E402


def main() -> None:
    a = alliance()
    us = a[a.is_us].set_index("quarter").loc[QUARTERS, ["ev_share", "bev_share", "phev_share", "evs_per_10k_res",
                                                         "total_ports"]]
    us["ev_share_change_pp"] = us.ev_share.diff().round(2)
    us.to_csv(TABLES / "national_quarterly.csv")

    p = panel()
    wide = p.pivot(index="state", columns="quarter", values="ev_share")
    yoy = pd.DataFrame({"ev_share_2025q2": wide["2025Q2"], "ev_share_2026q2": wide["2026Q2"]})
    yoy["change_pp"] = (yoy.ev_share_2026q2 - yoy.ev_share_2025q2).round(2)
    yoy["rank_2026q2"] = yoy.ev_share_2026q2.rank(ascending=False, method="min").astype(int)
    yoy = yoy.sort_values("change_pp")
    yoy.to_csv(TABLES / "state_yoy_change.csv")

    qm = p.groupby("quarter")[["ev_share", "ev_search_ratio", "gas_regular_mean", "ports_per_10k"]].mean().round(3)
    qm.to_csv(TABLES / "quarterly_means.csv")

    nat = pd.read_csv(CLEAN / "trends_national_monthly.csv")
    ev_search = nat[(nat.group == "B1") & (nat.term == "Electric vehicle")][["month", "value"]]

    # figure (reference only; the website draws its own SVG from the JSON)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(QUARTERS, us.ev_share, marker="o", color="#111")
    ax.axvline(2.5, color="#999", ls="--", lw=1)
    ax.text(2.55, us.ev_share.max(), "federal credit ends\nSept 30, 2025", fontsize=8, va="top")
    ax.set_ylabel("EV share of new registrations (%)")
    ax.set_title("U.S. EV share of new light-duty registrations")
    fig.tight_layout()
    fig.savefig(FIGURES / "national_ev_share.png", dpi=150)

    write_json("national", {
        "quarters": QUARTERS,
        "ev_share": us.ev_share.tolist(), "bev_share": us.bev_share.tolist(), "phev_share": us.phev_share.tolist(),
        "ev_search_ratio_state_mean": qm.ev_search_ratio.tolist(),
        "gas_regular_state_mean": qm.gas_regular_mean.tolist(),
        "ev_search_monthly": {"month": ev_search.month.tolist(), "value": ev_search.value.tolist(),
                              "note": "Google Trends index (0-100) for the Electric vehicle topic, Group B1 export"},
    })
    write_json("states_quarterly", {s: {"ev_share": wide.loc[s, QUARTERS].tolist()} for s in wide.index})
    ev = pd.read_csv(CLEAN / "event_calendar.csv")
    write_json("events", ev.to_dict("records"))

    down = int((yoy.change_pp < 0).sum())
    print("U.S. EV share by quarter:", dict(zip(QUARTERS, us.ev_share)))
    print(f"Q2->Q3 2025: {us.ev_share['2025Q3'] - us.ev_share['2025Q2']:+.2f} pp | "
          f"Q3->Q4 2025: {us.ev_share['2025Q4'] - us.ev_share['2025Q3']:+.2f} pp | "
          f"2026Q2 vs 2025Q2: {us.ev_share['2026Q2'] - us.ev_share['2025Q2']:+.2f} pp")
    print(f"States + DC with lower EV share in 2026 Q2 than 2025 Q2: {down} of 51")
    print("Largest YoY declines:", yoy.change_pp.head(5).to_dict())
    print("Largest YoY gains:", yoy.change_pp.tail(3).to_dict())
    mi = yoy.loc["MI"]
    print(f"Michigan: {mi.ev_share_2025q2}% -> {mi.ev_share_2026q2}% ({mi.change_pp:+} pp), "
          f"rank {mi.rank_2026q2} of 51 in 2026 Q2")


if __name__ == "__main__":
    main()
