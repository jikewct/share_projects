"""Raw and prepared DataFrame detail view."""
import pandas as pd
import streamlit as st
from .ui import section, csv_download


def render_page(df):
    section("筛选后数据", "表格展示前 5,000 行；下载包含全部筛选记录和标准化分析字段。")
    st.dataframe(df.head(5000), hide_index=True, use_container_width=True)
    csv_download(df, "下载全部筛选数据 CSV", "filtered_data")
    st.dataframe(pd.DataFrame({
        "字段": df.columns, "类型": df.dtypes.astype(str).values,
        "有效行": df.notna().sum().values, "缺失率": df.isna().mean().values,
    }), hide_index=True, use_container_width=True)
