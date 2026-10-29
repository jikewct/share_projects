"""Streamlit entry point: data setup, shared experiment selection and routing."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import ALIASES, combine_experiments, infer_mapping, numeric_metrics, prepare_data, read_table
from demo import make_demo
from result_store import discover_result_tables
from dashboard.data import load_global_experiment
from dashboard.global_statistics import render_page as render_global_statistics
from dashboard.overview import render_overview
from dashboard.dimensions import dimension_view
from dashboard.comparison import compare_view
from dashboard.explorer import explorer_view
from dashboard.details import render_page as render_details
from dashboard.ui import COLORS, apply_styles, kpis, render_page_header

ROOT = Path(__file__).resolve().parent
ANALYSIS_PAGES = ("全局统计", "Band 维度", "屏幕维度", "实验对比", "自定义分析", "数据明细")
px.defaults.color_discrete_sequence = COLORS


@st.cache_data(show_spinner=False)
def demo_data():
    return make_demo()


@st.cache_data(show_spinner=False)
def load_table(name, content):
    return read_table(name, content)




def result_source(ui):
    root_text = ui.text_input("实验根目录", str(ROOT / "result"), key="result_root")
    root = Path(root_text).expanduser()
    if not root.is_absolute():
        root = ROOT / root
    filename = ui.text_input("全局汇总文件", "", key="result_filename",
        help="实验总览读取 global.csv；全局曲线读取同目录 global.df。也可指定汇总文件的相对路径。")
    ui.button("刷新实验 / 数据", use_container_width=True,
        help="重新扫描实验子目录并读取更新后的文件；每次页面交互也会重新扫描。")
    try:
        tables, errors = discover_result_tables(root, filename.strip())
    except (OSError, ValueError) as exc:
        st.error(str(exc))
        st.info("请设置实验根目录。示例：result/实验A/global.csv、result/实验B/global.csv。")
        st.stop()
    frames, inventory, demo_count = [], [], 0
    for name, path in tables.items():
        try:
            curve_path = path.parent / "global.df"
            part = load_global_experiment(path, curve_path)
            # Directory names win over any stale experiment column inside a file.
            part["experiment"] = name
            part["_source_experiment"] = name
            frames.append(part)
            simulated = (root / name / "SIMULATED_DATA.txt").is_file()
            demo_count += int(simulated)
            inventory.append({"实验": name, "汇总 CSV": str(path.relative_to(root.resolve())),
                              "曲线 DataFrame": str(curve_path.relative_to(root.resolve())),
                              "曲线记录数": len(part), "状态": "模拟数据" if simulated else "已加载"})
        except Exception as exc:
            errors[name] = str(exc)
    for name, error in errors.items():
        inventory.append({"实验": name, "汇总 CSV": "—", "曲线 DataFrame": "—",
                          "曲线记录数": 0, "状态": error})
    with ui.container():
        st.caption("实验目录读取状态")
        st.dataframe(pd.DataFrame(inventory), hide_index=True, use_container_width=True)
    if errors:
        st.warning("以下实验未参与分析：" + "；".join(f"{name}（{error}）" for name, error in errors.items()))
    if not frames:
        st.info("未发现完整的全局数据。每个实验目录需同时提供 global.csv 和 global.df。")
        st.stop()
    label = "模拟目录数据" if demo_count == len(frames) else "含模拟实验" if demo_count else "result 实验目录"
    return pd.concat(frames, ignore_index=True), f"{label} · {len(frames)} 个实验"


def source_data(experiments, ui):
    if experiments is not None:
        ui.caption("数据来源 · Python DataFrame")
        return combine_experiments(experiments), "已接入 DataFrame"
    source = ui.radio("数据来源", ["result 实验目录", "演示数据", "上传文件", "本地 data 目录"], horizontal=False)
    if source == "result 实验目录":
        return result_source(ui)
    if source == "演示数据":
        return demo_data(), "模拟数据 · 仅用于功能演示"
    if source == "上传文件":
        uploads = ui.file_uploader("选择实验文件", type=["csv", "parquet", "xlsx"],
            accept_multiple_files=True, help="一个文件可包含多个实验；无实验列时使用文件名。XLSX 读取第一个工作表。")
        inputs = [(f.name, f.getvalue()) for f in uploads]
    else:
        folder = ROOT / "data"
        files = sorted(p for p in folder.glob("*") if p.suffix.lower() in [".csv", ".parquet", ".xlsx"])
        ui.caption(f"从 {folder} 读取；添加文件后点击刷新。")
        ui.button("刷新数据", use_container_width=True)
        inputs = [(p.name, p.read_bytes()) for p in files]
    frames, errors = [], []
    for name, content in inputs:
        try:
            part = load_table(name, content).copy()
            if not any(str(c).casefold() in [a.casefold() for a in ALIASES["experiment"]] for c in part):
                part["_source_experiment"] = Path(name).stem
            else:
                exp_col = infer_mapping(part.columns)["experiment"]
                part["_source_experiment"] = part[exp_col]
            frames.append(part)
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    for error in errors:
        ui.error(error)
    if errors:
        st.error("部分文件读取失败。请修正后再分析，避免使用不完整的实验数据。")
        st.stop()
    if not frames:
        st.info("请在左侧上传数据，或切换到演示数据查看完整功能。")
        st.stop()
    return pd.concat(frames, ignore_index=True), f"{len(frames)} 个文件"


def mapping_controls(raw):
    detected = infer_mapping(raw.columns)
    if "_source_experiment" in raw:
        detected["experiment"] = "_source_experiment"
    with st.sidebar.expander("字段映射与计算口径", expanded=False):
        st.caption("自动识别截图中的 Mesure_L / GammaCurv 等字段。可手动修正。")
        mapping = {}
        options = ["（未映射）"] + raw.columns.tolist()
        for key in ALIASES:
            mapping[key] = st.selectbox(key, options, index=options.index(detected[key]) if detected[key] else 0,
                                       key=f"mapping_{key}")
            if mapping[key] == "（未映射）":
                mapping[key] = None
        modes = ["根据判定列计算"]
        if mapping.get("OKR"):
            modes.insert(0, "使用已有 OKR 列")
        mode = st.selectbox("OKR 来源", modes)
        scale_label = st.selectbox("已有 OKR 列的数值范围", ["0–1", "0–100"],
                                   disabled=mode != "使用已有 OKR 列")
        zero = st.checkbox("RealGamma=0 视为无效值", value=True,
                           help="截图 gray=0 的 GammaCurv=0 通常无法用于 Gamma 分析。负值始终排除。")
        st.caption("派生 OKR：所有已映射判定列均为 1 才合格；任一列为 -1、缺失或非 0/1 时，该行不参与 OKR。")
    return mapping, 100 if scale_label == "0–100" else 1, mode == "根据判定列计算", zero


def select_all_experiments(experiments):
    checked = st.session_state.get("experiment_select_all", True)
    for experiment in experiments:
        st.session_state[f"experiment::{experiment}"] = checked


def sync_experiment_root(experiments):
    st.session_state["experiment_select_all"] = all(
        st.session_state.get(f"experiment::{experiment}", False) for experiment in experiments)


def filter_data(df, experiment_slot, filter_slot):
    experiments = sorted(df.experiment.unique().tolist())
    if "experiment_select_all" not in st.session_state:
        st.session_state["experiment_select_all"] = True
    for experiment in experiments:
        key = f"experiment::{experiment}"
        if key not in st.session_state:
            st.session_state[key] = st.session_state["experiment_select_all"]
    with experiment_slot:
        st.markdown("**实验选择**")
        with st.container(border=True):
            st.markdown("📁 **result**")
            st.checkbox("全部实验", key="experiment_select_all",
                        on_change=select_all_experiments, args=(experiments,))
            for index, experiment in enumerate(experiments):
                branch = "└─" if index == len(experiments) - 1 else "├─"
                st.checkbox(f"{branch} {experiment}", key=f"experiment::{experiment}",
                            on_change=sync_experiment_root, args=(experiments,))
        selected = [experiment for experiment in experiments
                    if st.session_state.get(f"experiment::{experiment}", False)]
    filter_slot.markdown("**条件筛选**")
    filtered = df[df.experiment.isin(selected)]
    for column, label in [("band", "Band"), ("screen", "屏幕"), ("freq", "刷新率 / Hz"), ("dbv", "DBV")]:
        if column in df and df[column].notna().any():
            options = sorted(df[column].dropna().unique().tolist())
            chosen = filter_slot.multiselect(label, options, default=[], key=f"filter_{column}", placeholder="全部")
            if chosen:
                filtered = filtered[filtered[column].isin(chosen)]
    if "gray" in df and df.gray.notna().any():
        lo, hi = float(df.gray.min()), float(df.gray.max())
        if lo < hi:
            bounds = filter_slot.slider("灰阶范围", lo, hi, (lo, hi), key="gray_filter")
            filtered = filtered[filtered.gray.between(*bounds)]
    filter_slot.caption(f"曲线记录 {len(filtered):,} / {len(df):,}")
    return filtered, selected

def render_dashboard(experiments=None):
    """Application shell. Page modules consume prepared DataFrames."""
    st.set_page_config(page_title="Gamma Lab · 实验分析", page_icon="◈", layout="wide")
    apply_styles()
    st.sidebar.markdown(
        '<div class="brand"><span>◈</span> Gamma Lab</div>'
        '<div class="subbrand">DISPLAY ANALYTICS WORKSPACE</div>',
        unsafe_allow_html=True,
    )
    experiment_slot = st.sidebar.container()
    filter_slot = st.sidebar.container()
    settings_slot = st.sidebar.expander("数据配置", expanded=False)
    menu = st.radio("分析工作台", ANALYSIS_PAGES, horizontal=True,
                    label_visibility="collapsed", key="analysis_navigation")
    raw, source_label = source_data(experiments, settings_slot)
    if raw.empty:
        st.warning("数据为空，请提供至少一条测量记录。")
        return
    if not raw.columns.is_unique:
        st.error("DataFrame 含重复列名，请先处理重复列名。")
        return
    mapping, scale, derived, zero = mapping_controls(raw)
    df = prepare_data(raw, mapping, scale, derived, zero)
    filtered, selected = filter_data(df, experiment_slot, filter_slot)
    result_root = st.session_state.get("result_root") if experiments is None else None

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
    elif menu == "自定义分析":
        explorer_view(filtered, metrics)
    else:
        render_details(filtered)


if __name__ == "__main__":
    render_dashboard()
