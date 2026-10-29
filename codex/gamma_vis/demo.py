"""Reproducible synthetic measurements, explicitly separate from production data."""
import numpy as np
import pandas as pd


def make_demo():
    rng = np.random.default_rng(42)
    frames = []
    for experiment, shift, noise in [("EXP-001 · 基准", -.035, .055),
                                      ("EXP-002 · 优化 A", .008, .029),
                                      ("EXP-003 · 优化 B", -.008, .038)]:
        for screen in range(1, 7):
            for band, band_shift in [("R", .018), ("G", 0), ("B", -.022)]:
                for freq in [60, 120]:
                    for dbv in [2048, 4094]:
                        gray = np.unique(np.r_[np.arange(0, 256, 4), 255])
                        gamma = 2.2 + shift + band_shift + .025 * np.exp(-gray / 45)
                        gamma = gamma + rng.normal(0, noise, len(gray)) + (screen - 3) * .003
                        luminance = 500 * (dbv / 4094) * (gray / 255) ** gamma
                        x = .31 + rng.normal(0, .0015, len(gray))
                        y = .33 + rng.normal(0, .0015, len(gray))
                        frame = pd.DataFrame({"experiment": experiment, "screen": f"PANEL-{screen:03}",
                            "band": band, "freq": freq, "dbv": dbv, "gray": gray,
                            "Mesure_L": luminance, "Mesure_x": x, "Mesure_y": y,
                            "GammaCurv": gamma, "SpecLMax": luminance * 1.08 + .001,
                            "SpecLMin": luminance * .92, "SpecXMax": .315, "SpecXMin": .305,
                            "SpecYMax": .335, "SpecYMin": .325,
                            "SpecGammaMax": 2.25, "SpecGammaMin": 2.15,
                            "LSpecIn": 1, "XSpecIn": (abs(x - .31) <= .005).astype(int),
                            "YSpecIn": (abs(y - .33) <= .005).astype(int),
                            "GammaIn": ((gamma >= 2.15) & (gamma <= 2.25)).astype(int)})
                        frame.loc[frame.gray == 0, ["GammaCurv", "GammaIn", "LSpecIn"]] = [0, -1, -1]
                        frames.append(frame)
    return pd.concat(frames, ignore_index=True)
