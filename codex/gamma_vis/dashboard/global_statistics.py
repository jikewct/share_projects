"""Complete global statistics page. Public entry point: render_page(df, ...)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from curves import aggregate_curve, make_curve_figure
from .overview import BIND_POINT_FIELDS, first_csv_value, parse_band_points, render_overview
from .ui import COLORS, chart, render_page_header, section


def curve_axes(df):
    return [column for column in ["gray", "dbv", "freq"]
            if column in df and df[column].notna().any()]


def color_map(experiments):
    return {name: COLORS[index % len(COLORS)] for index, name in enumerate(sorted(experiments))}


def add_bind_point_guides(fig, df, experiment, curve_x):
    """Use the final selected experiment's CSV bind points as ticks and guides."""
    if curve_x != "gray" or not experiment:
        return []
    group = df[df.experiment == experiment]
    raw_points = first_csv_value(group, BIND_POINT_FIELDS)
    points = [float(value) for value in parse_band_points(raw_points)] if raw_points is not None else []
    points = sorted(dict.fromkeys(points))
    for point in points:
        fig.add_vline(x=point, line_width=1, line_dash="dot",
                      line_color="rgba(68, 91, 112, 0.24)", layer="below")
    if points:
        labels = [str(int(value)) if value.is_integer() else f"{value:g}" for value in points]
        fig.update_xaxes(tickmode="array", tickvals=points, ticktext=labels,
                         tickangle=-45, tickfont=dict(size=10))
    return points


def render_okr_curve(df, curve_x, colors, bind_source, reference_df):
    with st.container(border=True):
        heading, control = st.columns([3, 1])
        heading.markdown("#### OKR 曲线")
        show_mean = control.checkbox("显示均值线", value=True, key="global_okr_mean")
        if "OKR" not in df or not df.OKR.notna().any():
            st.info("当前全局统计表没有有效 OKR 数据。请映射已有 OKR 列，或提供可计算 OKR 的判定列。")
            return
        okr_curve = aggregate_curve(df, "OKR", curve_x)
        fig = make_curve_figure(okr_curve, "OKR", curve_x, colors,
                                show_curve=True, show_mean=show_mean)
        add_bind_point_guides(fig, reference_df, bind_source, curve_x)
        chart(fig, "global_okr_curve", global_curve=True)


def add_gamma_specs(fig, df, curve_x):
    if not all(column in df for column in ["SpecGammaMin", "SpecGammaMax"]):
        return
    specs = (df.dropna(subset=[curve_x]).groupby(curve_x, observed=True)
             [["SpecGammaMin", "SpecGammaMax"]].mean().reset_index())
    for column, label in [("SpecGammaMin", "规格下限"), ("SpecGammaMax", "规格上限")]:
        fig.add_trace(go.Scatter(x=specs[curve_x], y=specs[column], name=label,
            mode="lines", line=dict(color="#aab5c4", dash="dot", width=1.5)))


def render_gamma_curve(df, curve_x, colors, bind_source, reference_df):
    with st.container(border=True):
        heading, control = st.columns([3, 1])
        heading.markdown("#### Gamma 曲线")
        automatic = control.checkbox("纵轴自动范围", value=True, key="global_gamma_auto")
        if "RealGamma" not in df or not df.RealGamma.notna().any():
            st.info("当前全局统计表没有有效 RealGamma 数据。请将 GammaCurv 等测量列映射到 RealGamma。")
            return
        gamma_curve = aggregate_curve(df, "RealGamma", curve_x)
        valid_gamma = gamma_curve.value.dropna()
        default_low = float(valid_gamma.min()) if not valid_gamma.empty else 2.0
        default_high = float(valid_gamma.max()) if not valid_gamma.empty else 2.4
        padding = max((default_high - default_low) * .08, .01)
        y_range = None
        if not automatic:
            ranges = st.columns([1, 1, 2])
            gamma_min = ranges[0].number_input("纵轴下限", value=round(default_low - padding, 4),
                                               format="%.4f", key="global_gamma_min")
            gamma_max = ranges[1].number_input("纵轴上限", value=round(default_high + padding, 4),
                                               format="%.4f", key="global_gamma_max")
            if gamma_min >= gamma_max:
                st.error("纵轴下限必须小于上限。")
                return
            y_range = (gamma_min, gamma_max)
        fig = make_curve_figure(gamma_curve, "RealGamma", curve_x, colors,
                                y_range=y_range)
        add_gamma_specs(fig, df, curve_x)
        add_bind_point_guides(fig, reference_df, bind_source, curve_x)
        chart(fig, "global_gamma_curve", global_curve=True)


def render_curves(df, selected_experiments, reference_df):
    section("全局曲线")
    experiments = sorted(df.experiment.dropna().unique().tolist())
    axes = curve_axes(df)
    colors = color_map(experiments)
    if not axes:
        st.warning("全局统计表缺少 gray、dbv 或 freq，无法绘制曲线。请在字段映射中指定横轴字段。")
        return
    curve_x = "gray" if "gray" in axes else axes[0]
    bind_source = selected_experiments[-1]
    st.caption(f"绑点参考：{bind_source} · 横轴刻度 / 垂直线")
    render_okr_curve(df, curve_x, colors, bind_source, reference_df)
    render_gamma_curve(df, curve_x, colors, bind_source, reference_df)


def render_page(df, selected_experiments=None, *, summary_df=None, result_root=None, source_label=""):
    """Render the entire page from canonical DataFrames without importing app.

    df: curve rows with experiment, gray, OKR and/or RealGamma.
    summary_df: unfiltered CSV totals and band_points; defaults to df.
    selected_experiments: ordered experiment IDs; first is baseline, last supplies guides.
    result_root: optional explicit path for legacy bind_points.csv fallback only.
    Inputs are never modified. A single-experiment df may omit experiment.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df 必须是 pandas DataFrame")
    reference_df = df if summary_df is None else summary_df
    if not isinstance(reference_df, pd.DataFrame):
        raise TypeError("summary_df 必须是 pandas DataFrame")
    df = df.copy()
    reference_df = reference_df.copy()
    for frame in (df, reference_df):
        if not frame.columns.is_unique:
            raise ValueError("DataFrame 含重复列名")
        if "experiment" not in frame:
            frame["experiment"] = "实验 01"
        frame["experiment"] = frame["experiment"].astype("string").fillna("未标注实验")
    available = list(dict.fromkeys(reference_df.experiment.tolist() + df.experiment.tolist()))
    selected = available if selected_experiments is None else list(dict.fromkeys(map(str, selected_experiments)))
    selected = [name for name in selected if name in available]
    render_page_header("全局统计", source_label)
    if not selected:
        st.warning("请选择需要对比的实验。")
        return
    render_overview(reference_df, selected, result_root=result_root)
    curves = df[df.experiment.isin(selected)]
    if curves.empty:
        st.info("当前筛选没有曲线数据，请调整筛选条件。")
        return
    render_curves(curves, selected, reference_df)
