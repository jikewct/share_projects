"""Discover experiment directories without mixing global, band and screen tables."""
from pathlib import Path

TABLE_SUFFIXES = {".csv", ".parquet", ".xlsx"}
GLOBAL_NAMES = {"global", "globalstats", "globalstatistics", "globaldataframe",
                "globaldata", "dfglobal", "overall", "全局统计", "全局统计dataframe"}


def find_global_table(directory, filename=""):
    directory = Path(directory).resolve()
    if filename:
        path = (directory / filename).resolve()
        if not path.is_relative_to(directory):
            raise ValueError("全局统计文件必须位于对应实验目录内")
        if path.suffix.lower() not in TABLE_SUFFIXES:
            raise ValueError("全局统计文件支持 CSV、Parquet、XLSX")
        if not path.is_file():
            raise FileNotFoundError(f"未找到 {filename}")
        return path
    candidates = [p for p in directory.iterdir() if p.is_file()
                  and p.suffix.lower() in TABLE_SUFFIXES
                  and p.stem.lower().replace("_", "").replace("-", "").replace(" ", "") in GLOBAL_NAMES]
    if not candidates:
        raise FileNotFoundError("未找到全局统计文件，请指定相对文件路径")
    if len(candidates) > 1:
        raise ValueError("发现多个全局统计文件，请指定文件名：" + "、".join(sorted(p.name for p in candidates)))
    return candidates[0]


def discover_result_tables(root, filename=""):
    """Rescan on every call. Directory names are authoritative experiment IDs."""
    root = Path(root).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"实验根目录不存在：{root}")
    tables, errors = {}, {}
    for directory in sorted(root.iterdir(), key=lambda p: p.name):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        try:
            tables[directory.name] = find_global_table(directory, filename)
        except (OSError, ValueError) as exc:
            errors[directory.name] = str(exc)
    return tables, errors
