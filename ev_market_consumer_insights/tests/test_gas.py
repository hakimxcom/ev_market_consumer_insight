"""
test_gas.py — unit tests for the gas-price step: quarterly mean over observed days only,
no filling of missing days, loud failure on duplicates. Synthetic data only.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage_1_data"))
import prepare_gas as pg  # noqa: E402
from states import STATES  # noqa: E402


def _daily(skip=None):
    days = pd.date_range(pg.START, pg.END, freq="D")
    rows = [(s, d, 3.0 if d.month <= 3 and d.year == 2025 else 4.0)
            for s in STATES.state for d in days if not (skip and d == pd.Timestamp(skip))]
    return pd.DataFrame(rows, columns=["state", "date", "regular"])


def test_mean_uses_observed_days_only_and_reports_missing():
    q, miss = pg.quarterly(_daily(skip="2025-02-10"))
    mi = q[(q.state == "MI") & (q.quarter == "2025Q1")].iloc[0]
    assert mi.gas_regular_mean == 3.0 and mi.gas_days_observed == 89 and mi.gas_days_in_quarter == 90
    assert len(miss) == 51 and miss.date.eq(pd.Timestamp("2025-02-10")).all()


def test_duplicate_state_day_is_loud(tmp_path):
    p = tmp_path / "g.csv"
    rows = [(n, "$3.00", "2025-01-01") for n in STATES.state_name] + [("Michigan", "$3.10", "2025-01-01")]
    pd.DataFrame(rows, columns=["State", "Regular", "Date"]).to_csv(p, index=False)
    with pytest.raises(pg.ValidationError):
        pg.load(p)
