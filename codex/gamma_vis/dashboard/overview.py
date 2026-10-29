"""Reusable experiment overview driven by summary DataFrame columns."""
from pathlib import Path
import html
import re
import numpy as np
import pandas as pd
import streamlit as st
from analytics import read_table

BIND_POINT_FIELDS = ("band_points", "bind_points")
SUMMARY_FIELDS = {
    "screen_count": ("screen_num",), "total_points": ("toal_num", "total_num"),
    "ok_points": ("ok_num",), "okr_mean": ("okr_mean",),
}


def parse_band_points(value):
    """Normalize a JSON-like or delimited bind-point collection for display."""
    is_collection = isinstance(value, (list, tuple, np.ndarray, pd.Series))
    if value is None or (not is_collection and pd.isna(value)):
        return []
    values = (list(value) if is_collection
              else re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", str(value)))
    result = []
    for item in values:
        try:
            number = float(item)
            result.append(str(int(number)) if number.is_integer() else f"{number:g}")
        except (TypeError, ValueError):
            continue
    return result


def first_csv_value(group, names):
    """Return the first populated summary value from accepted CSV aliases."""
    for name in names:
        if name in group:
            values = group[name].dropna()
            if not values.empty:
                return values.iloc[0]
    return None


def load_bind_points(experiments, df, result_root=None):
    root = Path(result_root).expanduser() if result_root is not None else None
    if root is not None and not root.is_absolute():
        root = Path(__file__).resolve().parents[1] / root
    frames = []
    for experiment in experiments:
        group = df[df.experiment == experiment]
        csv_points = first_csv_value(group, BIND_POINT_FIELDS)
        values = parse_band_points(csv_points)[:24] if csv_points is not None else []
        path = root / experiment / "bind_points.csv" if root is not None else None
        if not values and path is not None and Path(experiment).name == experiment and path.is_file():
            try:
                points = read_table(path.name, path.read_bytes()).copy()
            except Exception:
                points = pd.DataFrame()
        else:
            points = pd.DataFrame()
        if not values:
            if "position" in points:
                points = points.sort_values("position")
            if "point_value" in points:
                values = points.point_value.dropna().astype(str).tolist()[:24]
            elif "point_id" in points:
                values = points.point_id.dropna().astype(str).tolist()[:24]
        values.extend(["未提供"] * (24 - len(values)))
        frames.append(pd.DataFrame({"实验名称": [experiment],
                                    "绑点": [",".join(values)]}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["实验名称", "绑点"])


def experiment_summary_records(df, experiments):
    """Read per-experiment CSV totals independently of curve filters."""
    records = []
    for experiment in experiments:
        group = df[df.experiment == experiment]
        values = {key: pd.to_numeric(first_csv_value(group, aliases), errors="coerce")
                  for key, aliases in SUMMARY_FIELDS.items()}
        screen_count, total_points = values["screen_count"], values["total_points"]
        ok_points, okr_mean = values["ok_points"], values["okr_mean"]
        if pd.notna(okr_mean) and okr_mean > 1:
            okr_mean /= 100
        records.append({"experiment": experiment, "screen_count": screen_count,
                        "total_points": total_points, "ok_points": ok_points,
                        "okr_mean": okr_mean})
    return records


def render_overview(df, experiments, result_root=None):
    """One sticky table for bind points, CSV totals and live baseline deltas."""
    if not experiments:
        return
    css = Path(__file__).with_name("overview.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    records = experiment_summary_records(df, experiments)
    points = load_bind_points(experiments, df, result_root).set_index("实验名称")["绑点"].to_dict()
    baseline = records[0]["okr_mean"] if records else np.nan
    rows = []
    for index, record in enumerate(records):
        if index == 0:
            growth_text, growth_class = "基准", "baseline"
        elif pd.isna(baseline) or baseline == 0 or pd.isna(record["okr_mean"]):
            growth_text, growth_class = "—", "baseline"
        else:
            growth = (record["okr_mean"] - baseline) / baseline * 100
            growth_text = f"{growth:+.2f}%"
            growth_class = "growth" if growth > 0 else "decline" if growth < 0 else "baseline"
        screen_text = "—" if pd.isna(record["screen_count"]) else f'{int(record["screen_count"]):,}'
        total_text = "—" if pd.isna(record["total_points"]) else f'{int(record["total_points"]):,}'
        ok_text = "—" if pd.isna(record["ok_points"]) else f'{int(record["ok_points"]):,}'
        okr_text = "—" if pd.isna(record["okr_mean"]) else f'{record["okr_mean"]:.2%}'
        rows.append('<tr>'
            f'<td class="stats-name">{html.escape(record["experiment"])}</td>'
            f'<td>{screen_text}</td><td>{total_text}</td>'
            f'<td>{ok_text}</td><td>{okr_text}</td>'
            f'<td><span class="rate {growth_class}">{growth_text}</span></td>'
            f'<td class="bind-values">{html.escape(points.get(record["experiment"], "—"))}</td></tr>')
    st.markdown('<section class="experiment-overview" aria-label="实验总览">'
        '<div class="overview-header"><div class="overview-heading">'
        '<span class="overview-dot"></span>实验总览'
        f'<span class="overview-count">{len(records)} 个实验</span></div>'
        '<span class="overview-note">相对首项 · <span class="growth-label">↑ 增长</span>'
        ' / <span class="decline-label">↓ 下降</span></span></div>'
        '<div class="overview-scroll"><table class="overview-table"><thead><tr>'
        '<th>实验名</th><th>屏幕数</th><th>总点数</th><th>OK 点数</th>'
        '<th>OKR 均值</th><th>相对首个实验</th><th>绑点</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></section>', unsafe_allow_html=True)
