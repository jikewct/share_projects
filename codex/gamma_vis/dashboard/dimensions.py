"""Band and screen dimension views."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analytics import summarize
from .ui import chart, section, csv_download


def trend_view(df, metric, key):
    axes = [c for c in ["gray", "dbv", "freq"] if c in df and df[c].notna().any()]
    if not axes:
        return
    with st.container(border=True):
        title, control = st.columns([3, 1])
        title.markdown(f"**{metric} · 条件趋势**")
        x = control.selectbox("横坐标", axes, key=f"x_{key}", label_visibility="collapsed")
        agg = df.groupby(["experiment", x], observed=True)[metric].agg(["mean", "count"]).reset_index()
        fig = px.line(agg, x=x, y="mean", color="experiment", markers=True,
                      hover_data=["count"], labels={"mean": metric, "experiment": "实验", "count": "有效行"})
        if metric == "RealGamma" and all(c in df for c in ["SpecGammaMin", "SpecGammaMax"]):
            bounds = df.groupby(x, observed=True)[["SpecGammaMin", "SpecGammaMax"]].mean().sort_index()
            # Varying specs are drawn at their actual x values, not a misleading constant band.
            for col, label in [("SpecGammaMin", "规格下限（均值）"), ("SpecGammaMax", "规格上限（均值）")]:
                fig.add_trace(go.Scatter(x=bounds.index, y=bounds[col], name=label, mode="lines",
                    line=dict(color="#aab5c4", dash="dash", width=1)))
        if metric == "OKR":
            fig.update_yaxes(tickformat=".0%")
        chart(fig, f"trend_{key}")
        st.caption("同一横坐标的多条测量记录取均值；其余条件合并。需要固定条件时使用左侧筛选。规格曲线仅用于参考，OKR 使用判定列。")


def dimension_view(df, metric, dimension):
    label = "Band" if dimension == "band" else "屏幕"
    if dimension not in df or not df[dimension].notna().any():
        st.info(f"当前数据没有{label}标识。请在字段映射中指定 {dimension} 列，或在 DataFrame 中补充该列。")
        return
    section(f"{label}维度分析", "同一维度内按实验分组；均值来自当前筛选条件内的有效测量行。")
    agg = df.groupby(["experiment", dimension], observed=True)[metric].agg(["mean", "count"]).reset_index()
    with st.container(border=True):
        fig = px.bar(agg, x=dimension, y="mean", color="experiment", barmode="group",
                     hover_data=["count"], labels={"mean": metric, dimension: label, "experiment": "实验"})
        if metric == "OKR":
            fig.update_yaxes(tickformat=".0%")
        chart(fig, f"dimension_{dimension}")
    if dimension == "screen" and "band" in df and df.band.notna().any():
        exp = st.selectbox("热力图实验", sorted(df.experiment.unique()), key="heat_experiment")
        pivot = df[df.experiment == exp].pivot_table(index="screen", columns="band", values=metric, aggfunc="mean")
        if not pivot.empty:
            with st.container(border=True):
                st.markdown(f"**屏幕 × Band · {metric}**")
                chart(px.imshow(pivot, color_continuous_scale="Teal", aspect="auto",
                    labels={"color": metric}, text_auto=".2%" if metric == "OKR" else ".3f"), "heatmap")
    st.dataframe(summarize(df, [metric], ["experiment", dimension]), hide_index=True, use_container_width=True)
    csv_download(agg, f"下载{label}统计 CSV", f"dimension_export_{dimension}")
