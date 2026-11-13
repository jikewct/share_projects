from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def select_labeled(widgets, label):
    return next(widget for widget in widgets if widget.label == label)


def test_all_analysis_pages_and_okr():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert len(app.sidebar.checkbox) == 4
    assert not app.sidebar.expander
    assert not app.sidebar.selectbox
    assert not app.sidebar.multiselect
    assert not app.sidebar.slider
    assert [widget.key for widget in app.sidebar.radio] == ["analysis_navigation"]
    assert not app.sidebar.text_input
    assert len(app.get("plotly_chart")) == 5
    assert select_labeled(app.radio, "分析工作台").options == [
        "全局统计", "Band 维度", "屏幕维度", "实验对比"
    ]
    for page in ["Band 维度", "屏幕维度", "实验对比"]:
        select_labeled(app.radio, "分析工作台").set_value(page).run()
        assert not app.exception, page
        select_labeled(app.selectbox, "当前分析指标").select("OKR").run()
        assert not app.exception, page


def test_integration_missing_dimensions_and_empty_selection():
    script = '''
import pandas as pd
from app import render_dashboard
render_dashboard({"A": pd.DataFrame({"gray": [0, 1], "GammaCurv": [0, 2.2], "GammaIn": [-1, 1]})})
'''
    app = AppTest.from_string(script, default_timeout=30).run()
    assert not app.exception
    for page in ["Band 维度", "屏幕维度", "实验对比"]:
        select_labeled(app.radio, "分析工作台").set_value(page).run()
        assert not app.exception
        assert len(app.info) > 0
    app.checkbox(key="experiment_select_all").uncheck().run()
    assert not app.exception
    assert len(app.warning) > 0
