import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard.okr_metrics import prepare_component_okr
from generate_results import generate_results


def test_rates_override_flags_and_invalid_values_do_not_become_passes():
    raw = pd.DataFrame({
        "LOKR": [0.8, -1, None, 2],
        "LSpecIn": [0, 1, 0, 1],
        "XSpecIn": [-1, 1, 0, None],
        "OKR": [0.5, 0.5, 0.5, 0.5],
    })
    original = raw.copy(deep=True)
    result = prepare_component_okr(raw)
    assert result["L_OKR"].dropna().tolist() == [0.8, 0.0]
    assert result["X_OKR"].dropna().tolist() == [1.0, 0.0]
    assert "Y_OKR" not in result
    assert result["OKR"].tolist() == raw["OKR"].tolist()
    assert_frame_equal(raw, original)


def test_mixed_experiments_can_use_direct_rates_and_raw_flags():
    raw = pd.DataFrame({"experiment": ["A", "B"],
                        "X_OKR": [0.75, None], "XSpecIn": [None, 1]})
    assert prepare_component_okr(raw)["X_OKR"].tolist() == [0.75, 1.0]


def test_demo_files_include_three_component_rates(tmp_path):
    names = generate_results(tmp_path)
    for name in names:
        curves = pd.read_pickle(tmp_path / name / "global.df")
        assert all(metric in curves for metric in ("L_OKR", "X_OKR", "Y_OKR"))
        assert curves["L_OKR"].dropna().eq(1).all()
        assert curves["L_OKR"].isna().sum() == 4
        for metric in ("L_OKR", "X_OKR", "Y_OKR"):
            assert curves[metric].dropna().between(0, 1).all()
