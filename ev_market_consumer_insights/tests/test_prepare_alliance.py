"""
test_prepare_alliance.py — unit tests for the Alliance parsers and checks, using small
synthetic inputs only (no real data). Run: python -m pytest tests/
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage_1_data"))
import prepare_alliance as pa  # noqa: E402


def _reg_frame(states, phev=1.0, bev=2.0, fcev=0.0):
    return pd.DataFrame({"state": states, "phev": phev, "bev": bev, "fcev": fcev,
                         "ev_total": phev + bev + fcev, "d_phev": 0.0, "d_bev": 0.0,
                         "d_fcev": 0.0, "d_ev_total": 0.0})


ALL = sorted(pa.EXPECTED)


def test_parse_registrations_stops_at_second_table():
    text = ("AK   0.60%   2.80%   0.00%   3.40%   0.02   0.29   0.00   0.31\n"
            "CA*  3.76%  19.90%   0.02%  23.68%  -0.02  -1.05  -0.03  -1.10\n"
            "AK   9.99%   9.99%   0.00%  19.98%   0.0%   0.0%   0.0%   0.00%\n")  # YTD table
    df = pa.parse_registrations(text)
    assert df.state.tolist() == ["AK", "CA"]          # asterisk stripped, YTD row ignored
    assert df.loc[1, "ev_total"] == 23.68


def test_parse_registrations_accepts_percent_signs_in_change_columns():
    df = pa.parse_registrations("MI  0.90%  4.04%  0.00%  4.93%  -2.9%  -2.2%  0.0%  -5.16%")
    assert df.loc[0, "d_ev_total"] == -5.16


def test_parse_vio_handles_blank_and_present_hydrogen():
    text = ("AK   110   97          207   0.88%   0.07%   27   75\n"
            "CA 46,369 18,051  43  64,463  7.57%  30.70%  37  614\n")
    df = pa.parse_vio(text)
    assert df.h2_stations.tolist() == [0, 43]
    assert df.total_ports.tolist() == [207, 64463]


def test_component_sum_failure_is_loud():
    df = _reg_frame(ALL)
    df.loc[0, "ev_total"] += 0.5
    with pytest.raises(pa.ValidationError):
        pa.check_registrations(df, "synthetic")


def test_missing_state_is_loud():
    with pytest.raises(pa.ValidationError):
        pa.check_registrations(_reg_frame([s for s in ALL if s != "WY"]), "synthetic")


def test_yoy_check_catches_transcription_error():
    earlier, later = _reg_frame(ALL), _reg_frame(ALL)
    later["d_ev_total"] = 0.0
    earlier.loc[earlier.state == "MI", "ev_total"] = 9.99   # typo in the earlier table
    with pytest.raises(pa.ValidationError):
        pa.check_yoy(earlier, later, "synthetic")
