"""Create visibly labelled demo result directories; never run on app startup."""
import argparse
import json
from pathlib import Path
import pandas as pd
from analytics import prepare_data
from demo import make_demo


def generate_results(root, overwrite=False):
    root = Path(root)
    names = ["DEMO-001_基准", "DEMO-002_优化A", "DEMO-003_优化B"]
    filenames = ["global.csv", "global.df", "band.csv", "screen.csv", "bind_points.csv", "SIMULATED_DATA.txt"]
    if not overwrite:
        existing = [root / name / file for name in names for file in filenames if (root / name / file).exists()]
        if existing:
            raise FileExistsError(f"模拟结果已存在，未覆盖：{existing[0]}")
    df = prepare_data(make_demo())
    for name, (_, data) in zip(names, df.groupby("experiment", sort=True)):
        directory = root / name
        directory.mkdir(parents=True, exist_ok=True)
        gray_points = [0, 4, 8, 12, 16, 20, 24, 28,
                       32, 40, 48, 56, 64, 72, 80, 96,
                       112, 128, 144, 160, 176, 192, 224, 255]
        for filename, keys in [("global.csv", ["freq", "dbv", "gray"]),
                               ("band.csv", ["band", "freq", "dbv", "gray"]),
                               ("screen.csv", ["screen", "freq", "dbv", "gray"])]:
            table = data.groupby(keys, observed=True).agg(
                RealGamma=("RealGamma", "mean"), OKR=("OKR", "mean"),
                SpecGammaMin=("SpecGammaMin", "mean"), SpecGammaMax=("SpecGammaMax", "mean"),
                sample_count=("gray", "size"), okr_valid_count=("OKR", "count"),
                gamma_valid_count=("RealGamma", "count"),
                screen_count=("screen", "nunique")).reset_index()
            if filename == "global.csv":
                valid_okr = data.OKR.dropna()
                table.to_pickle(directory / "global.df")
                summary = pd.DataFrame([{
                    "band_points": json.dumps(gray_points),
                    "screen_num": data.screen.nunique(),
                    "toal_num": len(valid_okr),
                    "ok_num": int(round(valid_okr.sum())),
                    "okr_mean": valid_okr.mean(),
                }])
                summary.to_csv(directory / filename, index=False, encoding="utf-8-sig")
            else:
                table.to_csv(directory / filename, index=False, encoding="utf-8-sig")
        bind_points = [{"position": position, "point_value": value}
                       for position, value in enumerate(gray_points, start=1)]
        pd.DataFrame(bind_points).to_csv(directory / "bind_points.csv", index=False, encoding="utf-8-sig")
        (directory / "SIMULATED_DATA.txt").write_text(
            "此目录由 generate_results.py 生成，所有数据均为模拟数据，仅用于交互功能演示。\n"
            "global.csv 为绑点与汇总数据；global.df 为全局曲线 DataFrame。\n"
            "bind_points.csv 包含 24 个模拟灰阶绑点。\n"
            "OKR 使用 0–1 范围，gray=0 的无效 Gamma/OKR 留空。\n", encoding="utf-8")
    return names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成 Gamma Lab 模拟实验目录")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent / "result")
    parser.add_argument("--overwrite", action="store_true", help="覆盖同名的模拟实验文件")
    args = parser.parse_args()
    for name in generate_results(args.root, args.overwrite):
        print(args.root / name)
