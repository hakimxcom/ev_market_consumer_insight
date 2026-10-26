"""
test_nhtsa.py — unit tests for NHTSA preparation: personal fields are never loaded, EV
classification rules, collapsing component rows to complaints. Synthetic data only.
"""
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage_1_data"))
import prepare_nhtsa as pn  # noqa: E402


def test_personal_fields_never_in_field_map():
    # CMPL.txt: 13 CITY, 15 VIN, 41 DEALER_NAME, 42 DEALER_TEL, 43 DEALER_CITY, 44 DEALER_STATE, 45 DEALER_ZIP
    assert not {13, 15, 41, 42, 43, 44, 45} & set(pn.FIELDS)


@pytest.mark.parametrize("make,model,expected", [
    ("TESLA", "MODEL Y", "BEV"), ("CHEVROLET", "EQUINOX EV", "BEV"), ("CHEVROLET", "EQUINOX", "not_ev"),
    ("TOYOTA", "RAV4 PRIME", "PHEV"), ("TOYOTA", "RAV4 HYBRID", "not_ev"), ("JEEP", "WRANGLER 4XE", "PHEV"),
    ("HYUNDAI", "IONIQ HYBRID", "not_ev"), ("INDIAN", "SCOUT", "not_ev"), ("VOLVO", "XC40", "not_ev"),
    ("CADILLAC", "redundant LYRIQ", "BEV"), ("FORD", "F-150 LIGHTNING BEV", "BEV"),
])
def test_classify(make, model, expected):
    assert pn.classify(make, model) == expected


def _row(odino, cmplid, comp, model="EQUINOX EV", state="MI", date="20250315", text="dealer said"):
    f = [""] * pn.N_FIELDS
    f[0], f[1], f[3], f[4], f[5], f[11], f[13], f[16], f[19], f[45] = (
        cmplid, odino, "CHEVROLET", model, "2025", comp, state, date, text, "V")
    f[14] = "SECRETVIN123"   # VIN position — must never be read
    f[12] = "SECRETCITY"     # city position — must never be read
    return "\t".join(f)


def test_load_and_collapse(tmp_path):
    lines = [_row("1", "a", "ELECTRICAL SYSTEM"), _row("1", "b", "POWER TRAIN"),
             _row("2", "c", "STEERING", model="EQUINOX", state="PR"),
             _row("3", "d", "AIR BAGS", date="20261001")]
    z = tmp_path / "c.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("c.txt", "\n".join(lines) + "\n")
    rows = pn.load(z)
    assert "SECRETVIN123" not in rows.to_csv() and "SECRETCITY" not in rows.to_csv()
    c, info = pn.to_complaints(rows)
    assert len(c) == 1                                  # PR dropped, Oct 2026 outside window
    assert info["complaints_outside_50_states_dc_dropped"] == 1
    one = c.iloc[0]
    assert one.electrical and one.powertrain_propulsion and one.kw_dealer
    assert one.twin_pair == "Equinox" and one.twin_side == "EV"
