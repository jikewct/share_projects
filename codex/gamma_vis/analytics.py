"""Pure, reusable DataFrame preparation and matched experiment comparisons."""
from io import BytesIO
from pathlib import Path
import numpy as np
import pandas as pd

ALIASES = {
    "experiment": ["experiment", "experiment_id", "exp", "exp_id", "实验", "实验名称"],
    "band": ["band", "band_id", "BandName", "频段"],
    "screen": ["screen", "screen_id", "panel", "panel_id", "sn", "屏幕", "屏幕编号"],
    "freq": ["freq", "frequency", "刷新率"],
    "dbv": ["dbv", "brightness", "亮度档位"],
    "gray": ["gray", "grey", "gray_level", "灰阶"],
    "RealGamma": ["RealGamma", "real_gamma", "GammaCurv", "GammaCurve", "Gamma"],
    "OKR": ["OKR", "ok_rate", "pass_rate", "良率"],
    "Mesure_L": ["Mesure_L", "Measure_L", "measured_l"],
    "Mesure_x": ["Mesure_x", "Measure_x", "measured_x"],
    "Mesure_y": ["Mesure_y", "Measure_y", "measured_y"],
    "LSpecIn": ["LSpecIn"], "XSpecIn": ["XSpecIn"],
    "YSpecIn": ["YSpecIn"], "GammaIn": ["GammaIn"],
    "SpecGammaMax": ["SpecGammaMax", "SpecGammaUpper", "SpecGammaU"],
    "SpecGammaMin": ["SpecGammaMin", "SpecGammaLower", "SpecGammaL"],
}
FLAGS = ["LSpecIn", "XSpecIn", "YSpecIn", "GammaIn"]
MATCH_KEYS = ["screen", "band", "freq", "dbv", "gray"]


def infer_mapping(columns):
    lookup = {str(c).strip().casefold(): c for c in columns}
    return {key: next((lookup[a.casefold()] for a in aliases if a.casefold() in lookup), None)
            for key, aliases in ALIASES.items()}


def read_table(name, content):
    suffix = Path(name).suffix.lower()
    stream = BytesIO(content)
    if suffix == ".csv":
        try:
            frame = pd.read_csv(stream, encoding="utf-8-sig")
        except UnicodeDecodeError:
            stream.seek(0)
            frame = pd.read_csv(stream, encoding="gb18030")
    elif suffix == ".parquet":
        frame = pd.read_parquet(stream)
    elif suffix == ".xlsx":
        frame = pd.read_excel(stream)
    else:
        raise ValueError("支持 CSV、Parquet、XLSX 文件")
    frame.columns = [str(c).strip() for c in frame.columns]
    if not frame.columns.is_unique:
        raise ValueError("列名去除空格后存在重复，请先修改重复列名")
    return frame


def combine_experiments(experiments):
    """Dictionary keys are authoritative experiment IDs, including for existing DFs."""
    frames = []
    for name, frame in experiments.items():
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name} 必须是 pandas DataFrame")
        part = frame.copy()
        part["experiment"] = str(name)
        frames.append(part)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def prepare_data(raw, mapping=None, okr_scale=1, derive_okr=True, gamma_zero_invalid=True):
    """Keep raw fields; make mapped canonical fields without mutating the caller."""
    mapping = mapping if mapping is not None else infer_mapping(raw.columns)
    df = raw.copy()
    # An explicitly unmapped canonical field must not remain active accidentally.
    for target in ALIASES:
        if target in df and mapping.get(target) is None:
            raw_name = f"原始::{target}"
            while raw_name in df:
                raw_name = f"原始::{raw_name}"
            df = df.rename(columns={target: raw_name})
    # Read every source from raw so mappings cannot overwrite each other's source.
    for target, source in mapping.items():
        if source is not None and source in raw:
            df[target] = raw[source]
    if "experiment" not in df:
        df["experiment"] = "实验 01"
    for column in ["experiment", "screen", "band"]:
        if column in df:
            df[column] = df[column].astype("string").str.strip().replace("", pd.NA)
    df["experiment"] = df["experiment"].fillna("未标注实验")
    for column in df.columns:
        if column in ("experiment", "screen", "band"):
            continue
        converted = pd.to_numeric(df[column], errors="coerce")
        if column in ALIASES or converted.notna().any():
            df[column] = converted.replace([np.inf, -np.inf], np.nan)
    if "RealGamma" in df:
        df.loc[df.RealGamma < 0, "RealGamma"] = np.nan
        if gamma_zero_invalid:
            df.loc[df.RealGamma == 0, "RealGamma"] = np.nan
    flags = [c for c in FLAGS if c in df]
    for flag in flags:
        df[flag] = df[flag].where(df[flag].isin([0, 1]))
    if flags:
        df["有效判定项数"] = df[flags].notna().sum(axis=1)
    if derive_okr:
        # Only judge complete rows: missing/-1 must not silently inflate the pass rate.
        if flags:
            complete = df[flags].notna().all(axis=1)
            df["OKR"] = df[flags].eq(1).all(axis=1).astype(float).where(complete)
        else:
            df["OKR"] = np.nan
    elif "OKR" in df:
        df["OKR"] = df.OKR.div(okr_scale).where(df.OKR.between(0, okr_scale))
    return df


def numeric_metrics(df):
    excluded = set(MATCH_KEYS + ["experiment", "有效判定项数"])
    columns = [c for c in df.select_dtypes(include="number").columns
               if c not in excluded and not c.startswith("原始::") and df[c].notna().any()]
    preferred = [c for c in ["RealGamma", "OKR", "Mesure_L", "Mesure_x", "Mesure_y"] if c in columns]
    return preferred + [c for c in columns if c not in preferred]


def summarize(df, metrics, groups=("experiment",)):
    if not metrics:
        return pd.DataFrame()
    result = df.groupby(list(groups), dropna=False, observed=True)[metrics].agg(
        ["count", "mean", "median", "std", "min", "max"])
    result.columns = [f"{metric} · {stat}" for metric, stat in result.columns]
    return result.reset_index()


def matched_comparison(df, baseline, candidate, metric, keys):
    """Aggregate repeated keys before outer joining; never create a Cartesian join."""
    if baseline == candidate:
        raise ValueError("请选择两个不同实验")
    if not keys:
        raise ValueError("请至少选择一个匹配字段")
    missing = set(keys + [metric, "experiment"]) - set(df.columns)
    if missing:
        raise ValueError(f"字段不存在：{', '.join(sorted(missing))}")
    parts, audit = [], {}
    for name, label in [(baseline, "基准"), (candidate, "对比")]:
        source = df.loc[df.experiment == name, keys + [metric]]
        valid = source.dropna(subset=keys + [metric])
        grouped = valid.groupby(keys, observed=True, dropna=False)[metric].agg(["mean", "size"]).reset_index()
        grouped = grouped.rename(columns={"mean": label, "size": f"{label}重复数"})
        parts.append(grouped)
        audit[f"{label}无效行"] = len(source) - len(valid)
        audit[f"{label}合并重复行"] = len(valid) - len(grouped)
    merged = parts[0].merge(parts[1], on=keys, how="outer", validate="one_to_one", indicator=True)
    audit.update({"匹配组数": int(merged._merge.eq("both").sum()),
                  "仅基准组数": int(merged._merge.eq("left_only").sum()),
                  "仅对比组数": int(merged._merge.eq("right_only").sum())})
    merged["差值"] = merged["对比"] - merged["基准"]
    if metric == "OKR":
        merged["差值（百分点）"] = merged["差值"] * 100
    else:
        merged["变化率（%）"] = merged["差值"].div(merged["基准"].replace(0, np.nan)) * 100
    return merged.rename(columns={"_merge": "匹配状态"}), audit
