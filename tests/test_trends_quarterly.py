"""
test_trends_quarterly.py — unit tests for the quarterly Trends reader and measures,
using small synthetic files only. Run: python -m pytest tests/
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage_1_data"))
import prepare_trends_quarterly as pt  # noqa: E402
from states import STATES  # noqa: E402


def _write(tmp_path, terms, rows, name="f.csv"):
    p = tmp_path / name
    pd.DataFrame(rows, columns=["Region"] + terms).to_csv(p, index=False)
    return p


def _all_states(values):
    return [[n] + values for n in STATES.state_name]


def test_zero_becomes_missing_not_zero(tmp_path):
    rows = _all_states([20, 30, 5, 45])
    rows[0] = [rows[0][0], 20, 35, 0, 45]
    df = pt.read_region_file(_write(tmp_path, pt.TERMS_A, rows), pt.TERMS_A)
    assert df["Plug-in hybrid"].isna().sum() == 1


def test_rows_not_summing_to_100_are_loud(tmp_path):
    rows = _all_states([20, 30, 5, 45])
    rows[3] = [rows[3][0], 20, 30, 5, 40]
    with pytest.raises(pt.ValidationError):
        pt.read_region_file(_write(tmp_path, pt.TERMS_A, rows), pt.TERMS_A)


def test_less_than_one_strings_are_loud(tmp_path):
    rows = _all_states([20, 30, 5, 45])
    rows[0] = [rows[0][0], "<1", 30, 5, 45]
    with pytest.raises(pt.ValidationError):
        pt.read_region_file(_write(tmp_path, pt.TERMS_A, rows), pt.TERMS_A)


def test_ratio_ignores_hybrid_and_artifact_quarter_blanks_hybrid():
    a = pd.DataFrame({"state": ["MI", "CA"], "Electric vehicle": [20, 20], "Hybrid vehicle": [10, 40],
                      "Plug-in hybrid": [5, 5], "Car dealership": [65, 35]})
    a = pd.concat([a] * 1)
    b1 = pd.DataFrame({"state": ["MI", "CA"], "Electric vehicle": [80, 80], "Charging station": [20, 20]})
    with pytest.raises(pt.ValidationError):      # only 2 states -> must refuse
        pt.measures(a, b1, "2025Q3")


def test_ratio_arithmetic():
    a = pd.DataFrame({"state": STATES.state, "Electric vehicle": 20, "Hybrid vehicle": 30,
                      "Plug-in hybrid": 5, "Car dealership": 45})
    b1 = pd.DataFrame({"state": STATES.state, "Electric vehicle": 80, "Charging station": 20})
    out = pt.measures(a, b1, "2025Q3")
    assert out.ev_search_ratio.iloc[0] == round(20 / 65 * 100, 2)
    assert out.hybrid_search_share.isna().all()          # artifact quarter
    assert pt.measures(a, b1, "2025Q2").hybrid_search_share.eq(30).all()
