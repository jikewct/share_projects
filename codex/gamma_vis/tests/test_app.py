from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def select_labeled(widgets, label):
    return next(widget for widget in widgets if widget.label == label)


def test_all_analysis_pages_and_okr():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 2
    for page in ["Band 维度", "屏幕维度", "实验对比", "自定义分析", "数据明细"]:
        select_labeled(app.radio, "分析工作台").set_value(page).run()
        assert not app.exception, page
        select_labeled(app.selectbox, "当前分析指标").select("OKR").run()
        assert not app.exception, page


def test_custom_same_axis_and_grouping():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    select_labeled(app.radio, "分析工作台").set_value("自定义分析").run()
    select_labeled(app.selectbox, "横轴字段").select("RealGamma").run()
    select_labeled(app.selectbox, "纵轴字段").select("RealGamma").run()
    assert not app.exception
    select_labeled(app.selectbox, "实验内分组").select("freq").run()
    assert not app.exception
    for kind in ["柱状图", "散点图", "箱线图", "直方图"]:
        select_labeled(app.selectbox, "图表类型").select(kind).run()
        assert not app.exception, kind


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
