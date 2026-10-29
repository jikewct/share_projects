"""Local experiment file loading, independent of Streamlit UI."""
from pathlib import Path
import pandas as pd
from analytics import read_table
from .overview import BIND_POINT_FIELDS, SUMMARY_FIELDS


def load_global_experiment(summary_path, curve_path=None):
    """Combine global.csv totals and global.df curves into a new DataFrame."""
    summary_path = Path(summary_path)
    curve_path = Path(curve_path) if curve_path is not None else summary_path.parent / "global.df"
    summary = read_table(summary_path.name, summary_path.read_bytes())
    if summary.empty:
        raise ValueError("global.csv 为空")
    if not curve_path.is_file():
        raise FileNotFoundError("未找到 global.df")
    curves = pd.read_pickle(curve_path)
    if not isinstance(curves, pd.DataFrame):
        raise TypeError("global.df 不是 pandas DataFrame")
    if curves.empty:
        raise ValueError("global.df 为空")
    if not curves.columns.is_unique:
        raise ValueError("global.df 含重复列名")
    curves = curves.copy()
    fields = list(BIND_POINT_FIELDS) + [name for aliases in SUMMARY_FIELDS.values() for name in aliases]
    for column in fields:
        if column in summary and summary[column].notna().any():
            curves[column] = summary[column].dropna().iloc[0]
    return curves
