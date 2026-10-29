"""Custom DataFrame exploration page."""
import plotly.express as px
import streamlit as st
from .ui import chart, section


def explorer_view(df, metrics):
    section("自定义分析", "自由组合横轴、指标与分组字段。折线/柱状图先聚合，散点图使用原始有效记录。")
    a, b, c = st.columns(3)
    axes = [col for col in df.columns if col != "experiment" and df[col].notna().any()]
    default = axes.index("gray") if "gray" in axes else 0
    x = a.selectbox("横轴字段", axes, index=default, key="explore_x")
    y = b.selectbox("纵轴字段", metrics, key="explore_y")
    kind = c.selectbox("图表类型", ["折线图", "柱状图", "散点图", "箱线图", "直方图"])
    a, b = st.columns(2)
    split_options = ["不拆分"] + [col for col in ["band", "screen", "freq", "dbv"] if col in df and col != x]
    split = a.selectbox("实验内分组", split_options)
    method = b.selectbox("聚合方式", ["mean", "median", "min", "max"],
                          disabled=kind not in ["折线图", "柱状图"])
    plot = df.copy()
    color = "experiment"
    if split != "不拆分":
        color = "实验 / 分组"
        plot[color] = plot.experiment.astype(str) + " / " + plot[split].astype("string").fillna("缺失")
    if kind in ["折线图", "柱状图"]:
        plotted_y = y if y != x else f"{y} · {method}"
        plot = plot.groupby(list(dict.fromkeys([color, x])), observed=True)[y].agg(method).rename(plotted_y).reset_index()
        fn = px.line if kind == "折线图" else px.bar
        args = {"markers": True} if kind == "折线图" else {"barmode": "group"}
        fig = fn(plot, x=x, y=plotted_y, color=color, **args)
    elif kind == "散点图":
        if len(plot) > 20000:
            st.caption("散点展示固定随机抽样的 20,000 行；统计和下载仍使用完整筛选数据。")
            plot = plot.sample(20000, random_state=42)
        fig = px.scatter(plot, x=x, y=y, color=color, opacity=.5)
    elif kind == "箱线图":
        fig = px.box(plot, x=color, y=y, color=color, points=False)
    else:
        fig = px.histogram(plot, x=y, color=color, barmode="overlay", opacity=.65, nbins=50)
    chart(fig, "custom_chart")
    if kind in ["箱线图", "直方图"]:
        st.caption("分布图使用纵轴字段作为分布指标，按实验与实验内分组展示。")
