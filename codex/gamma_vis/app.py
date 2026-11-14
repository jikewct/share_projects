"""Streamlit entry point: data setup, shared experiment selection and routing."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import combine_experiments, infer_mapping, numeric_metrics, prepare_data
from result_store import discover_result_tables
from dashboard.data import load_global_experiment
from dashboard.global_statistics import render_page as render_global_statistics
from dashboard.overview import render_overview
from dashboard.dimensions import dimension_view
from dashboard.comparison import compare_view
from dashboard.ui import COLORS, apply_styles, kpis, render_page_header

ROOT = Path(__file__).resolve().parent
ANALYSIS_PAGES = ("全局统计", "Band 维度", "屏幕维度", "实验对比")
px.defaults.color_discrete_sequence = COLORS


def result_source(root):
    """Read experiment folders on each rerun without sidebar configuration."""
    try:
        tables, errors = discover_result_tables(root)
    except (OSError, ValueError) as exc:
        st.error(str(exc))
        st.info("每个实验目录需提供 global.csv 和 global.df。")
        st.stop()
    frames, demo_count = [], 0
    for name, path in tables.items():
        try:
            part = load_global_experiment(path)
            part["experiment"] = name
            part["_source_experiment"] = name
            frames.append(part)
            demo_count += int((root / name / "SIMULATED_DATA.txt").is_file())
        except Exception as exc:
            errors[name] = str(exc)
    if errors:
        st.warning("以下实验未参与分析：" + "；".join(
            f"{name}（{error}）" for name, error in errors.items()))
    if not frames:
        st.info("未发现完整的全局数据。每个实验目录需同时提供 global.csv 和 global.df。")
        st.stop()
    label = "模拟目录数据" if demo_count == len(frames) else "含模拟实验" if demo_count else "result 实验目录"
    return pd.concat(frames, ignore_index=True), f"{label} · {len(frames)} 个实验"


def source_data(experiments, result_root):
    if experiments is not None:
        return combine_experiments(experiments), "已接入 DataFrame"
    return result_source(result_root)



def select_all_experiments(experiments):
    checked = st.session_state.get("experiment_select_all", True)
    for experiment in experiments:
        st.session_state[f"experiment::{experiment}"] = checked


def sync_experiment_root(experiments):
    st.session_state["experiment_select_all"] = all(
        st.session_state.get(f"experiment::{experiment}", False) for experiment in experiments)


def select_experiments(df, experiment_slot):
    experiments = sorted(df.experiment.unique().tolist())
    if "experiment_select_all" not in st.session_state:
        st.session_state["experiment_select_all"] = True
    for experiment in experiments:
        key = f"experiment::{experiment}"
        if key not in st.session_state:
            st.session_state[key] = st.session_state["experiment_select_all"]
    with experiment_slot:
        with st.container(key="experiment_tree"):
            st.markdown('<div class="sidebar-section-title">实验选择</div>'
                        '<div class="sidebar-folder"><svg aria-hidden="true" viewBox="0 0 24 24" '
                        'fill="none" stroke="currentColor" stroke-width="1.6">'
                        '<path d="M3 7V5h6l2 2h10v12H3Z"/></svg>result</div>',
                        unsafe_allow_html=True)
            st.checkbox("全部实验", key="experiment_select_all",
                        on_change=select_all_experiments, args=(experiments,))
            for index, experiment in enumerate(experiments):
                branch = "└─" if index == len(experiments) - 1 else "├─"
                st.checkbox(f"{branch} {experiment}", key=f"experiment::{experiment}",
                            on_change=sync_experiment_root, args=(experiments,))
        selected = [experiment for experiment in experiments
                    if st.session_state.get(f"experiment::{experiment}", False)]
    return df[df.experiment.isin(selected)], selected


def render_dashboard(experiments=None, *, result_root=None):
    """Application shell. Page modules consume prepared DataFrames."""
    st.set_page_config(page_title="Gamma Lab · 实验分析", page_icon="◈", layout="wide")
    apply_styles()
    st.sidebar.markdown(
        '<div class="brand"><span>◈</span> Gamma Lab</div>'
        '<div class="subbrand">DISPLAY ANALYTICS WORKSPACE</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="sidebar-section-title">分析工作台</div>',
                        unsafe_allow_html=True)
    menu = st.sidebar.radio("分析工作台", ANALYSIS_PAGES,
                            label_visibility="collapsed", key="analysis_navigation")
    experiment_slot = st.sidebar.container()
    root = Path(result_root).expanduser() if result_root is not None else ROOT / "result"
    if not root.is_absolute():
        root = ROOT / root
    raw, source_label = source_data(experiments, root)
    if raw.empty:
        st.warning("数据为空，请提供至少一条测量记录。")
        return
    if not raw.columns.is_unique:
        st.error("DataFrame 含重复列名，请先处理重复列名。")
        return
    mapping = infer_mapping(raw.columns)
    if "_source_experiment" in raw:
        mapping["experiment"] = "_source_experiment"
    df = prepare_data(raw, mapping, derive_okr=not bool(mapping.get("OKR")))
    filtered, selected = select_experiments(df, experiment_slot)
    result_root = root if experiments is None else None

    if menu == "全局统计":
        render_global_statistics(
            filtered, selected, summary_df=df,
            result_root=result_root, source_label=source_label,
        )
        return

    render_page_header(menu, source_label)
    if filtered.empty:
        st.warning("当前筛选没有数据，请选择实验或调整条件。")
        return
    render_overview(df, selected, result_root=result_root)
    metrics = numeric_metrics(filtered)
    if not metrics:
        st.warning("当前没有有效数值指标，请检查字段映射、筛选条件和缺失值。")
        st.dataframe(filtered.head(500), use_container_width=True)
        return
    controls, _ = st.columns([1, 2])
    metric = controls.selectbox("当前分析指标", metrics)
    kpis(filtered, metric, selected)
    if menu in ("Band 维度", "屏幕维度"):
        dimension_view(filtered, metric, "band" if menu == "Band 维度" else "screen")
    elif menu == "实验对比":
        compare_view(filtered, metric)


if __name__ == "__main__":
    render_dashboard()
