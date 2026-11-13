"""Normalize component OKR columns without Streamlit or filesystem access."""
import pandas as pd

OKR_COMPONENTS = {
    "L_OKR": ("L OKR", "LSpecIn", ("L_OKR", "LOKR", "OKR_L", "L_pass_rate")),
    "X_OKR": ("X OKR", "XSpecIn", ("X_OKR", "XOKR", "OKR_X", "X_pass_rate")),
    "Y_OKR": ("Y OKR", "YSpecIn", ("Y_OKR", "YOKR", "OKR_Y", "Y_pass_rate")),
}


def prepare_component_okr(df):
    """Return 0–1 rates; fall back to independent 0/1 flags for missing values.

    Explicit out-of-range rates stay invalid. In particular, -1 flags must not
    become failures or passes, and an absent channel must not copy overall OKR.
    """
    result = df.copy()
    columns = {str(column).strip().casefold(): column for column in df.columns}
    for metric, (_, flag, aliases) in OKR_COMPONENTS.items():
        source = next((columns[name.casefold()] for name in aliases
                       if name.casefold() in columns), None)
        flag_column = columns.get(flag.casefold())
        if source is None and flag_column is None:
            continue
        fallback = pd.Series(float("nan"), index=df.index)
        if flag_column is not None:
            flags = pd.to_numeric(df[flag_column], errors="coerce")
            fallback = flags.where(flags.isin([0, 1]))
        if source is None:
            result[metric] = fallback
        else:
            values = pd.to_numeric(df[source], errors="coerce")
            result[metric] = values.where(values.between(0, 1)).where(
                df[source].notna(), fallback)
    return result
