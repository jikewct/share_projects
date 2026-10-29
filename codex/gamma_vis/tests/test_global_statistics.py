"""Page contract tests: independent DataFrames, stable totals and selection order."""
import json
import pandas as pd
from streamlit.testing.v1 import AppTest

from dashboard.data import load_global_experiment


PAGE_SCRIPT = '''
import sys
import pandas as pd
from pandas.testing import assert_frame_equal
app_was_loaded = "app" in sys.modules
from dashboard.global_statistics import render_page

assert ("app" in sys.modules) == app_was_loaded
curves = pd.DataFrame({
    "experiment": ["A", "A", "B", "B"], "gray": [4, 8, 4, 8],
    "OKR": [0.6, 0.8, 0.9, 1.0], "RealGamma": [2.18, 2.19, 2.2, 2.21],
})
summary = pd.DataFrame({
    "experiment": ["A", "B"], "band_points": [[0, 4, 8], [0, 8, 16]],
    "screen_num": [2, 3], "toal_num": [1000, 2000], "ok_num": [700, 1900],
    "okr_mean": [0.7, 0.95],
})
original_curves, original_summary = curves.copy(deep=True), summary.copy(deep=True)
render_page(CURVE_INPUT, SELECTED, summary_df=summary)
assert_frame_equal(curves, original_curves)
assert_frame_equal(summary, original_summary)
'''


def run_page(curves="curves", selected='["A", "B"]'):
    script = PAGE_SCRIPT.replace("CURVE_INPUT", curves).replace("SELECTED", selected)
    app = AppTest.from_string(script, default_timeout=30).run()
    assert not app.exception, app.exception
    return app


def overview_html(app):
    return next(m.value for m in app.markdown if 'class="experiment-overview"' in m.value)


def test_standalone_page_uses_summary_and_last_experiment_guides():
    app = run_page('curves[curves.gray == 4]')
    summary = overview_html(app)
    assert "1,000" in summary and "2,000" in summary
    assert "+35.71%" in summary
    charts = app.get("plotly_chart")
    assert len(charts) == 2
    for chart in charts:
        spec = json.loads(chart.proto.spec)
        assert spec["layout"]["xaxis"]["tickvals"] == [0, 8, 16]
        assert len(spec["layout"]["shapes"]) == 3
    okr = json.loads(charts[0].proto.spec)
    assert any("60.00%" in trace["name"] for trace in okr["data"])


def test_ordered_selection_changes_baseline_and_bind_source():
    app = run_page(selected='["B", "A"]')
    assert "-26.32%" in overview_html(app)
    for chart in app.get("plotly_chart"):
        assert json.loads(chart.proto.spec)["layout"]["xaxis"]["tickvals"] == [0, 4, 8]


def test_empty_curve_filter_preserves_csv_overview():
    app = run_page("curves.iloc[:0]")
    assert "1,000" in overview_html(app)
    assert app.info and not app.get("plotly_chart")


def test_empty_selection_and_missing_gamma_are_handled_by_page():
    app = run_page(selected="[]")
    assert app.warning and not app.get("plotly_chart")
    app = run_page('curves.drop(columns="RealGamma")')
    assert app.info and len(app.get("plotly_chart")) == 1


def test_file_loader_returns_new_dataframe_and_csv_totals(tmp_path):
    summary_path = tmp_path / "global.csv"
    curves = pd.DataFrame({"gray": [4, 8], "OKR": [0.2, 0.3]})
    curves.to_pickle(tmp_path / "global.df")
    pd.DataFrame([{"band_points": "[0,4,8]", "screen_num": 3,
                   "toal_num": 100, "ok_num": 70, "okr_mean": 0.7}]).to_csv(summary_path, index=False)
    loaded = load_global_experiment(summary_path)
    assert loaded["OKR"].tolist() == [0.2, 0.3]
    assert loaded["toal_num"].tolist() == [100, 100]
    assert loaded["band_points"].tolist() == ["[0,4,8]", "[0,4,8]"]
    assert "toal_num" not in curves
