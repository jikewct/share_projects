"""Plot construction kept independent of Streamlit for numeric verification."""
import pandas as pd
import plotly.graph_objects as go


def aggregate_curve(df, metric, x):
    if metric not in df:
        return pd.DataFrame(columns=["experiment", x, "value", "count"])
    data = df.dropna(subset=[x])
    return (data.groupby(["experiment", x], observed=True, sort=True)[metric]
            .agg(value="mean", count="count").reset_index())


def make_curve_figure(curve, metric, x, colors, show_curve=True, show_mean=False, y_range=None):
    fig = go.Figure()
    valid = curve.dropna(subset=["value"])
    if valid.empty:
        return fig
    xmin, xmax = valid[x].min(), valid[x].max()
    if xmin == xmax:
        xmin, xmax = xmin - .5, xmax + .5
    for experiment, group in curve.groupby("experiment", observed=True, sort=True):
        points = group.dropna(subset=["value"])
        if points.empty:
            continue
        color = colors[experiment]
        mean = points.value.mean()
        mean_label = f"{experiment} · 均值 {mean:.2%}" if metric == "OKR" else f"{experiment} · 均值 {mean:.4f}"
        if show_curve:
            fig.add_trace(go.Scatter(x=group[x], y=group.value,
                name=mean_label if show_mean else experiment,
                legendgroup=experiment, mode="lines+markers", connectgaps=False,
                line=dict(color=color, width=2), marker=dict(size=4),
                customdata=group[["count"]].to_numpy(),
                hovertemplate=f"{x}=%{{x}}<br>{metric}=%{{y:.2%}}<br>有效记录=%{{customdata[0]}}<extra>%{{fullData.name}}</extra>"
                if metric == "OKR" else f"{x}=%{{x}}<br>{metric}=%{{y:.4f}}<br>有效记录=%{{customdata[0]}}<extra>%{{fullData.name}}</extra>"))
        if show_mean:
            # Equal weight per valid plotted point, rather than reweighting by repeated rows.
            fig.add_trace(go.Scatter(x=[xmin, xmax], y=[mean, mean], mode="lines",
                name=mean_label, showlegend=not show_curve, legendgroup=experiment,
                line=dict(color=color, dash="dash", width=1.5),
                hovertemplate="均值=%{y:.2%}<extra>%{fullData.name}</extra>"
                if metric == "OKR" else "均值=%{y:.4f}<extra>%{fullData.name}</extra>"))
    fig.update_layout(xaxis_title=x, yaxis_title="OKR / 合格率" if metric == "OKR" else "RealGamma")
    if metric == "OKR":
        fig.update_yaxes(tickformat=".0%", range=[0, 1.05])
    if y_range is not None:
        if y_range[0] >= y_range[1]:
            raise ValueError("纵轴下限必须小于上限")
        fig.update_yaxes(range=list(y_range), autorange=False)
    return fig
