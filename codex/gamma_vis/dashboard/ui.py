"""Shared presentation components; no page or filesystem data dependencies."""
from pathlib import Path
import html
import pandas as pd
import streamlit as st

COLORS = ["#098793", "#ee9b46", "#6f79c9", "#df6984", "#4ca888", "#9774b6"]


def chart(fig, key, *, global_curve=False):
    fig.update_layout(font=dict(family="Inter, PingFang SC, Microsoft YaHei, sans-serif", color="#506176"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=12, t=48 if global_curve else 12, b=18),
        height=330 if global_curve else 315,
        legend=dict(title_text="", orientation="h", x=0,
                    y=1.2 if global_curve else -.25,
                    yanchor="bottom" if global_curve else "top", font=dict(size=11)),
        hovermode="x unified" if global_curve else "closest")
    fig.update_xaxes(showgrid=False, linecolor="#e9eef4", title_standoff=12, automargin=True)
    fig.update_yaxes(gridcolor="#e9eef4", zerolinecolor="#e9eef4")
    st.plotly_chart(fig, use_container_width=True, key=key,
                    config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}})


def section(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def csv_download(df, label, key):
    st.download_button(label, df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"gamma_{key}.csv", mime="text/csv", key=key)


def fmt(value, metric, delta=False):
    if pd.isna(value):
        return "—"
    if metric == "OKR":
        return f"{value * 100:+.2f} pp" if delta else f"{value:.2%}"
    return f"{value:+.4f}" if delta else f"{value:.4f}"


def kpis(df, metric, experiments):
    cols = st.columns(4)
    cols[0].metric("测量记录", f"{len(df):,}")
    cols[1].metric("对比实验", str(df.experiment.nunique()))
    cols[2].metric(f"{metric} · 均值", fmt(df[metric].mean(), metric))
    coverage = df[metric].notna().mean()
    cols[3].metric("有效数据覆盖率", f"{coverage:.1%}")
    st.caption("统计单位为筛选后的测量行；OKR 为有效测量行的平均合格率。记录数不同的实验在总体均值中按行加权。")


def render_page_header(title, source_label=""):
    heading, badge = st.columns([3, 2])
    heading.title(title)
    if source_label:
        badge.markdown(
            f'<div style="text-align:right;padding-top:8px"><span class="source-chip">● {html.escape(source_label)}</span></div>',
            unsafe_allow_html=True,
        )


def apply_styles():
    css = Path(__file__).with_name("base.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
