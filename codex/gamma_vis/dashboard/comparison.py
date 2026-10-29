"""Matched experiment comparison page."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analytics import MATCH_KEYS, matched_comparison
from .ui import COLORS, chart, section, csv_download, fmt


def compare_view(df, metric):
    section("实验配对对比", "按相同屏幕、Band、刷新率、DBV 和灰阶配对，查看对比实验相对基准的变化。")
    experiments = sorted(df.experiment.unique().tolist())
    if len(experiments) < 2:
        st.info("请在左侧至少选择两个实验。")
        return
    a, b = st.columns(2)
    baseline = a.selectbox("基准实验", experiments)
    candidates = [e for e in experiments if e != baseline]
    candidate = b.selectbox("对比实验", candidates)
    available = [c for c in MATCH_KEYS if c in df and df[c].notna().any()]
    keys = st.multiselect("配对字段", available, default=available,
        help="先对同一实验内重复组合取均值，再按所选字段匹配。两实验屏幕编号不同时，可取消 screen，比较相同条件的总体均值。")
    if not keys:
        st.info("至少选择一个配对字段，才能进行逐条件对比。")
        return
    result, audit = matched_comparison(df, baseline, candidate, metric, keys)
    matched = result[result["匹配状态"] == "both"]
    with st.expander("配对质量与计算口径", expanded=True):
        st.write(" · ".join(f"{k}：{v:,}" for k, v in audit.items()))
        st.caption("每个匹配条件组等权；未匹配组和匹配字段/指标缺失行不参与差值。重复测量先取组均值。OKR 差值使用百分点，其他字段相对变化以基准为分母，基准为 0 时不计算变化率。")
    if matched.empty:
        st.warning("没有可匹配的有效条件组。请检查筛选条件、屏幕标识及配对字段。")
        st.dataframe(result, hide_index=True, use_container_width=True)
        csv_download(result, "下载完整配对结果 CSV", "matched_empty")
        return
    cells = st.columns(4)
    cells[0].metric("匹配条件组", f"{len(matched):,}")
    cells[1].metric("基准 · 配对均值", fmt(matched["基准"].mean(), metric))
    cells[2].metric("对比 · 配对均值", fmt(matched["对比"].mean(), metric))
    cells[3].metric("平均差值 · 对比 − 基准", fmt(matched["差值"].mean(), metric, True))
    l, r = st.columns(2)
    with l, st.container(border=True):
        st.markdown("**相同条件下的测量值**")
        fig = px.scatter(matched, x="基准", y="对比", hover_data=keys, opacity=.65)
        lo = matched[["基准", "对比"]].min().min()
        hi = matched[["基准", "对比"]].max().max()
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="相等参考线",
                                 line=dict(color="#bbc4d0", dash="dash")))
        chart(fig, "paired_scatter")
    with r, st.container(border=True):
        delta = "差值（百分点）" if metric == "OKR" else "差值"
        st.markdown("**差值分布 · 对比 − 基准**")
        fig = px.histogram(matched, x=delta, nbins=40, color_discrete_sequence=[COLORS[0]])
        fig.add_vline(x=0, line_dash="dash", line_color="#ee9b46")
        chart(fig, "paired_hist")
    st.dataframe(result, hide_index=True, use_container_width=True)
    csv_download(result, "下载完整配对结果 CSV", "matched")
