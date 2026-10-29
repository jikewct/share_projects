import numpy as np
import pandas as pd
import pytest

from analytics import (combine_experiments, infer_mapping, matched_comparison,
                       prepare_data, read_table)


def test_gamma_and_okr_invalid_rows_are_not_passes():
    raw = pd.DataFrame({"GammaCurv": [0, 2.2, -1, 2.3, np.inf],
                        "LSpecIn": [-1, 1, 1, 1, 1], "GammaIn": [-1, 1, 0, np.nan, 2]})
    data = prepare_data(raw)
    assert data.RealGamma.tolist()[1] == 2.2
    assert data.RealGamma.isna().tolist() == [True, False, True, False, True]
    assert data.OKR.dropna().tolist() == [1., 0.]
    assert data.OKR.mean() == .5
    assert data.OKR.count() == 2
    assert raw.GammaCurv.iloc[0] == 0


def test_existing_okr_scale_and_out_of_range():
    raw = pd.DataFrame({"OKR": [90, 100, 0, 110, -1]})
    data = prepare_data(raw, okr_scale=100, derive_okr=False)
    assert data.OKR.dropna().tolist() == [.9, 1., 0.]
    assert prepare_data(pd.DataFrame({"gray": [1]})).OKR.isna().all()


def test_unmapping_flag_really_excludes_it():
    raw = pd.DataFrame({"LSpecIn": [1], "GammaIn": [0]})
    mapping = infer_mapping(raw.columns)
    mapping["GammaIn"] = None
    result = prepare_data(raw, mapping)
    assert result.OKR.iloc[0] == 1
    assert result["原始::GammaIn"].iloc[0] == 0


def test_alias_and_authoritative_dataframe_experiment():
    raw = pd.DataFrame({"GammaCurv": [2.2], "panel_id": ["a"], "experiment": ["old"]})
    combined = combine_experiments({"new": raw})
    data = prepare_data(combined)
    assert data.experiment.iloc[0] == "new"
    assert data.screen.iloc[0] == "a"
    assert raw.experiment.iloc[0] == "old"


def test_matching_aggregates_duplicates_before_join():
    frame = pd.DataFrame({"experiment": ["a", "a", "a", "b", "b", "b"],
                          "gray": [1, 1, 2, 1, 1, 3], "RealGamma": [2, 4, 5, 4, 6, 8]})
    result, audit = matched_comparison(frame, "a", "b", "RealGamma", ["gray"])
    common = result[result["匹配状态"] == "both"]
    assert len(result) == 3
    assert len(common) == 1
    assert common["差值"].iloc[0] == 2
    assert audit["基准合并重复行"] == 1
    assert audit["仅对比组数"] == 1


def test_okr_comparison_is_percentage_points_and_missing_keys_excluded():
    frame = pd.DataFrame({"experiment": ["a", "b", "b"], "gray": [1, 1, np.nan], "OKR": [.9, .95, 1.]})
    result, audit = matched_comparison(frame, "a", "b", "OKR", ["gray"])
    assert result["差值（百分点）"].iloc[0] == pytest.approx(5)
    assert audit["对比无效行"] == 1
    with pytest.raises(ValueError):
        matched_comparison(frame, "a", "b", "OKR", [])


def test_no_common_keys_and_zero_baseline():
    frame = pd.DataFrame({"experiment": ["a", "b"], "gray": [1, 2], "metric": [0., 1.]})
    result, audit = matched_comparison(frame, "a", "b", "metric", ["gray"])
    assert audit["匹配组数"] == 0
    assert result["差值"].isna().all()
    frame.gray = 1
    result, _ = matched_comparison(frame, "a", "b", "metric", ["gray"])
    assert result["变化率（%）"].isna().all()


def test_csv_encoding_and_duplicate_columns():
    data = read_table("test.csv", "实验,GammaCurv\n试验A,2.2\n".encode("gb18030"))
    assert data["实验"].iloc[0] == "试验A"
    with pytest.raises(ValueError):
        read_table("bad.csv", b"x, x\n1,2")
