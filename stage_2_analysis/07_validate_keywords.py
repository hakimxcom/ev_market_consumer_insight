"""
07_validate_keywords.py — check the NHTSA narrative keyword flags against hand coding.

WHAT IT DOES
  Reads data/interim/keyword_validation_sample.csv (120 random matched-twin complaints written by
  06_nhtsa_twins.py). The author fills each hand_kw_* column with 1 (theme present) or 0 after
  reading the narrative. For each flag this script reports: agreement %, Cohen's kappa
  (agreement beyond chance; >0.6 is usually called substantial), precision and recall of the
  keyword rule against the hand code. Until the hand columns are filled it reports "pending"
  and exits normally, so the pipeline still runs.
  Keyword-based results should be published only for flags with kappa >= 0.6.

INPUTS   data/interim/keyword_validation_sample.csv  (private: contains narratives)
OUTPUTS  outputs/tables/keyword_validation.csv  (agreement statistics only, no text)
RUN      python stage_2_analysis/07_validate_keywords.py
"""
import pandas as pd
from sklearn.metrics import cohen_kappa_score, precision_score, recall_score

from common import ROOT, TABLES

SAMPLE = ROOT / "data" / "interim" / "keyword_validation_sample.csv"


def main() -> None:
    if not SAMPLE.exists():
        print("Validation sample not found — run 06_nhtsa_twins.py first.")
        return
    d = pd.read_csv(SAMPLE)
    flags = [c for c in d.columns if c.startswith("kw_")]
    rows = []
    for f in flags:
        h = pd.to_numeric(d[f"hand_{f}"], errors="coerce")
        if h.isna().all():
            continue
        m = h.notna()
        auto, hand = d.loc[m, f].astype(bool).astype(int), h[m].astype(int)
        rows.append({"flag": f, "n_coded": int(m.sum()), "agreement_pct": round((auto == hand).mean() * 100, 1),
                     "kappa": round(cohen_kappa_score(hand, auto), 3),
                     "precision": round(precision_score(hand, auto, zero_division=0), 3),
                     "recall": round(recall_score(hand, auto, zero_division=0), 3)})
    if not rows:
        print("Keyword validation: PENDING — hand_kw_* columns are empty "
              f"({len(d)} complaints in {SAMPLE.relative_to(ROOT)}).")
        pd.DataFrame(columns=["flag", "n_coded", "agreement_pct", "kappa", "precision", "recall"]).to_csv(
            TABLES / "keyword_validation.csv", index=False)
        return
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "keyword_validation.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
