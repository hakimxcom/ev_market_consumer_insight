"""
test_census_and_merge.py — unit tests for the state crosswalk, Census checks and panel joins,
using small synthetic inputs only. Run: python -m pytest tests/
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage_1_data"))
import merge_panel as mp  # noqa: E402
import prepare_census as pc  # noqa: E402
from states import STATES, to_abbr  # noqa: E402


def test_crosswalk_has_51_unique():
    assert len(STATES) == 51 and STATES.state.is_unique


def test_unknown_state_name_is_loud():
    with pytest.raises(ValueError):
        to_abbr(pd.Series(["Michigan", "Puerto Rico"]), "synthetic")


def test_census_check_rejects_missing_state():
    df = STATES[["state"]].iloc[:50].assign(x=1)
    with pytest.raises(pc.ValidationError):
        pc._check_51(df, "synthetic")


def test_strict_merge_rejects_unmatched_rows():
    left = pd.DataFrame({"state": ["MI", "CA"], "a": [1, 2]})
    right = pd.DataFrame({"state": ["MI"], "b": [3]})
    with pytest.raises(mp.ValidationError):
        mp.strict_merge(left, right, on="state", label="synthetic", validate="m:1")


def test_ports_per_10k_arithmetic():
    p = mp.add_ports_per_10k(pd.DataFrame({"total_ports": [5000], "pop_2025": [10_000_000]}))
    assert p.ports_per_10k.iloc[0] == 5.0
