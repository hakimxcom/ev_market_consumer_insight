"""
04_segments.py — group the 51 states into EV market segments: factor analysis of state
characteristics, then clustering of the factor scores.

WHAT IT DOES
  1. Takes 10 state characteristics, standardizes them (z-scores):
       structure: log income, % renters, % 5+ unit housing, truck/SUV share
       market:    ports per 10K (2026 Q2), mean gas price, ACC II adoption, EV fee (0/1)
       demand:    mean EV search ratio, mean EV share of new registrations
  2. Factor analysis (maximum likelihood, varimax rotation). Number of factors = eigenvalues of
     the correlation matrix above 1 (Kaiser rule), capped at 3. Loadings are saved so each
     factor can be named from what loads on it.
  3. k-means on the factor scores for k = 2..6 (50 random starts, fixed seed); k chosen by the
     highest silhouette score. Check: a Gaussian mixture model with the same k; agreement
     reported as the adjusted Rand index (1 = identical grouping, 0 = chance).
  4. Segment profiles: mean of each original variable per segment, member states, Michigan's
     segment and its nearest peers (closest states in factor space).
  Segment names (Urban cores, Electric-ready, Truck-first) are given in docs/methodology.md.

INPUTS   data/clean/state_table.csv
OUTPUTS  outputs/tables/factor_loadings.csv, segments.csv, segment_profiles.csv
         outputs/site_data/segments.json
RUN      python stage_2_analysis/04_segments.py
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import FactorAnalysis
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture

from common import TABLES, state_table, write_json

SEED = 20261025
VARS = {
    "log_income": "Income (log median)",
    "pct_renter": "% renters",
    "pct_multiunit_5plus": "% 5+ unit housing",
    "truck_share": "Truck/SUV share",
    "ports_per_10k_2026q2": "Charging ports per 10K",
    "gas_regular_mean": "Gas price (mean)",
    "acc2_adopted_2025q1": "ACC II state",
    "has_ev_fee_in_window": "EV registration fee",
    "ev_search_ratio_mean": "EV search interest",
    "ev_share_mean": "EV share of new registrations",
}


def main() -> None:
    s = state_table().copy()
    s["log_income"] = np.log(s.median_hh_income)
    X = s[list(VARS)]
    Z = (X - X.mean()) / X.std(ddof=0)

    eig = np.sort(np.linalg.eigvalsh(np.corrcoef(Z.T.values)))[::-1]
    n_f = int(min(3, max(1, (eig > 1).sum())))
    fa = FactorAnalysis(n_components=n_f, rotation="varimax", random_state=SEED).fit(Z.values)
    load = pd.DataFrame(fa.components_.T, index=[VARS[v] for v in VARS],
                        columns=[f"F{i + 1}" for i in range(n_f)]).round(3)
    load.to_csv(TABLES / "factor_loadings.csv")
    F = fa.transform(Z.values)

    sil = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(F)
        sil[k] = silhouette_score(F, km.labels_)
    k = max(sil, key=sil.get)
    km = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(F)
    gmm = GaussianMixture(n_components=k, n_init=20, random_state=SEED).fit(F)
    ari = adjusted_rand_score(km.labels_, gmm.predict(F))

    # order segments by mean EV share so labels are stable: S1 = highest adoption
    order = s.groupby(km.labels_).ev_share_mean.mean().sort_values(ascending=False).index
    relabel = {old: f"S{i + 1}" for i, old in enumerate(order)}
    s["segment"] = [relabel[l] for l in km.labels_]
    for i in range(n_f):
        s[f"F{i + 1}"] = F[:, i].round(3)
    s[["state", "segment"] + [f"F{i + 1}" for i in range(n_f)]].to_csv(TABLES / "segments.csv", index=False)

    prof = s.groupby("segment")[list(VARS)].mean()
    prof["log_income"] = np.exp(prof.log_income).round(0)
    prof = prof.rename(columns={"log_income": "median_hh_income"}).round(2)
    prof["n_states"] = s.segment.value_counts()
    prof["states"] = s.groupby("segment").state.apply(lambda x: " ".join(sorted(x)))
    prof.to_csv(TABLES / "segment_profiles.csv")

    fcols = [f"F{i + 1}" for i in range(n_f)]
    mi = s.set_index("state").loc["MI", fcols].astype(float)
    dist = ((s.set_index("state")[fcols] - mi) ** 2).sum(axis=1).pow(0.5).drop("MI").sort_values()
    peers = dist.head(5).round(3)

    write_json("segments", {
        "k": k, "silhouette": {str(a): round(b, 3) for a, b in sil.items()}, "gmm_agreement_ari": round(ari, 3),
        "loadings": load.to_dict(), "state_segment": dict(zip(s.state, s.segment)),
        "profiles": prof.drop(columns="states").to_dict("index"),
        "members": prof.states.to_dict(), "michigan_peers": peers.index.tolist(),
    })
    pd.set_option("display.width", 200)
    print("Eigenvalues:", np.round(eig, 2).tolist(), "-> factors:", n_f)
    print(load.to_string())
    print("Silhouette by k:", {a: round(b, 3) for a, b in sil.items()}, "-> k =", k, "| GMM agreement (ARI):", round(ari, 3))
    print(prof.to_string())
    print("Michigan segment:", s.set_index("state").loc["MI", "segment"], "| nearest peers:", peers.to_dict())


if __name__ == "__main__":
    main()
