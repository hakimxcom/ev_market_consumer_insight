"""
06_nhtsa_twins.py — H1: do EV owners complain differently from owners of comparable gas models?
Also: EV complaint rates by state, and a random sample for hand-checking the keyword flags.

WHAT IT DOES
  1. For each matched pair (Equinox EV / Equinox; Ioniq 5 / Tucson; Mach-E / Escape, same model
     years) and for the three pairs pooled: share of complaints that mention each theme,
     EV vs. gas. Shares, not rates: there is no per-state sales denominator for the gas twins.
     Tests: within each pair, two-sided Fisher exact test per theme. Pooled across pairs,
     Cochran–Mantel–Haenszel test stratified by pair (compares EV vs. gas only WITHIN each pair,
     so the large Ioniq 5 group does not dominate), with its common odds ratio. Holm correction
     across the 16 themes within each row group. Pooled shares are the mean of the three
     pair-level shares (each pair weighted equally). Breslow–Day p-value reports whether the
     EV-vs-gas difference varies across pairs (low p = pairs disagree; read pair rows).
  2. State EV complaint rate = EV complaints (Jan 2025 – Jun 2026) per 10K EVs in operation
     (descriptive; recall-heavy models shape it).
  3. Validation sample: 120 random twin complaints (seeded) with narrative text and keyword
     flags, written to data/interim/ (NOT published) for hand-coding by the author. Agreement
     between hand codes and keyword flags is computed by 07_validate_keywords.py once filled.

INPUTS   data/interim/nhtsa_complaints_slim.csv, data/raw/nhtsa/COMPLAINTS_RECEIVED_2025-2026.zip
         (narratives for the sample only), data/clean/state_table.csv
OUTPUTS  outputs/tables/nhtsa_twin_themes.csv, nhtsa_state_rates.csv
         outputs/site_data/nhtsa.json
         data/interim/keyword_validation_sample.csv  (private; contains narratives)
RUN      python stage_2_analysis/06_nhtsa_twins.py
"""
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.multitest import multipletests

from common import CLEAN, ROOT, TABLES, state_table, write_json

sys.path.insert(0, str(ROOT / "stage_1_data"))
from prepare_nhtsa import COMPONENT_THEMES, FIELDS, KEYWORD_FLAGS, ZIP  # noqa: E402

INTERIM = ROOT / "data" / "interim"
SEED = 20261025
THEMES = list(COMPONENT_THEMES) + list(KEYWORD_FLAGS)


def theme_table(c: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in list(c.groupby("twin_pair")) + [("All three pairs", c)]:
        ev, gas = g[g.twin_side == "EV"], g[g.twin_side == "gas"]
        for t in THEMES:
            if pair == "All three pairs":
                ev_sh = c[c.twin_side == "EV"].groupby("twin_pair")[t].mean().mean()
                gas_sh = c[c.twin_side == "gas"].groupby("twin_pair")[t].mean().mean()
            else:
                ev_sh, gas_sh = ev[t].mean(), gas[t].mean()
            het = np.nan
            if pair == "All three pairs":
                tables = []
                for _, gp in c.groupby("twin_pair"):
                    e, g2 = gp[gp.twin_side == "EV"][t], gp[gp.twin_side == "gas"][t]
                    tables.append(np.array([[e.sum(), len(e) - e.sum()], [g2.sum(), len(g2) - g2.sum()]], float) + 0.5)
                st = StratifiedTable(tables)
                odds, p = st.oddsratio_pooled, st.test_null_odds().pvalue
                het = st.test_equal_odds().pvalue
            else:
                a, b = int(ev[t].sum()), int(len(ev) - ev[t].sum())
                cc, d = int(gas[t].sum()), int(len(gas) - gas[t].sum())
                odds, p = fisher_exact([[a, b], [cc, d]])
            rows.append({"pair": pair, "theme": t, "n_ev": len(ev), "n_gas": len(gas),
                         "ev_share_pct": round(ev_sh * 100, 1), "gas_share_pct": round(gas_sh * 100, 1),
                         "diff_pp": round((ev_sh - gas_sh) * 100, 1), "odds_ratio": round(odds, 2), "p_value": p,
                         "p_pairs_differ": None if np.isnan(het) else round(het, 5)})
    out = pd.DataFrame(rows)
    for pair in out.pair.unique():
        m = out.pair == pair
        out.loc[m, "p_holm"] = multipletests(out.loc[m, "p_value"], method="holm")[1]
    out["p_value"] = out.p_value.round(5)
    out["p_holm"] = out.p_holm.round(5)
    return out


def validation_sample(c: pd.DataFrame, n: int = 120) -> pd.DataFrame:
    samp = c[c.twin_pair.notna()].sample(n=n, random_state=SEED)
    ids = set(samp.odino.astype(str))
    with zipfile.ZipFile(ZIP) as z:
        name = z.namelist()[0]
        raw = pd.read_csv(z.open(name), sep="\t", header=None, usecols=[1, 19], dtype=str, quoting=3)
    raw.columns = ["odino", "narrative"]
    text = raw[raw.odino.isin(ids)].groupby("odino").narrative.first()
    samp = samp.assign(odino=samp.odino.astype(str))
    samp["narrative"] = samp.odino.map(text)
    keep = ["odino", "twin_pair", "twin_side", "narrative"] + list(KEYWORD_FLAGS)
    out = samp[keep].copy()
    for f in KEYWORD_FLAGS:
        out[f"hand_{f}"] = ""  # to be filled 1/0 by the author
    return out


def main() -> None:
    c = pd.read_csv(INTERIM / "nhtsa_complaints_slim.csv", dtype={"odino": str, "year": str})
    tw = c[c.twin_pair.notna()]
    themes = theme_table(tw)
    themes.to_csv(TABLES / "nhtsa_twin_themes.csv", index=False)

    st = state_table().set_index("state")
    rates = st[["complaints_ev", "ev_stock_mean", "ev_complaints_per_10k_evs"]].sort_values(
        "ev_complaints_per_10k_evs", ascending=False)
    rates.to_csv(TABLES / "nhtsa_state_rates.csv")

    vs = validation_sample(c)
    vs.to_csv(INTERIM / "keyword_validation_sample.csv", index=False)

    pooled = themes[themes.pair == "All three pairs"].set_index("theme")
    write_json("nhtsa", {
        "pairs": {p: {"n_ev": int(g.n_ev.iloc[0]), "n_gas": int(g.n_gas.iloc[0])}
                  for p, g in themes.groupby("pair")},
        "pooled_themes": pooled[["ev_share_pct", "gas_share_pct", "diff_pp", "p_holm"]].to_dict("index"),
        "by_pair": {p: g.set_index("theme")[["ev_share_pct", "gas_share_pct", "diff_pp"]].to_dict("index")
                    for p, g in themes[themes.pair != "All three pairs"].groupby("pair")},
        "state_rate_per_10k_evs": rates.ev_complaints_per_10k_evs.to_dict(),
        "notes": ["Shares of complaints mentioning each theme; complainers only (survivorship).",
                  "Keyword flags (kw_*) pending hand-validation.",
                  "Component themes use NHTSA component codes."],
    })
    pd.set_option("display.width", 200)
    print(pooled[["n_ev", "n_gas", "ev_share_pct", "gas_share_pct", "diff_pp", "odds_ratio", "p_holm",
                  "p_pairs_differ"]].to_string())
    print("\nBy pair, electrical / powertrain / dealer / cost:")
    sel = themes[themes.theme.isin(["electrical", "powertrain_propulsion", "kw_dealer", "kw_cost", "kw_mechanic"])
                 & (themes.pair != "All three pairs")]
    print(sel[["pair", "theme", "ev_share_pct", "gas_share_pct", "diff_pp", "p_holm"]].to_string(index=False))
    print(f"\nValidation sample written: {len(vs)} complaints (private, data/interim/)")


if __name__ == "__main__":
    main()
