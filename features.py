import numpy as np

CTL_LAMBDA = 1 - np.exp(-1 / 42)
ATL_LAMBDA = 1 - np.exp(-1 / 7)


def compute_rolling_features(daily_loads: list[float], seed: float | None = None) -> dict:
    if not daily_loads:
        return {"ctl": 0.0, "atl": 0.0, "tsb": 0.0, "acwr": 1.0}

    if seed is None:
        seed = float(np.mean(daily_loads[: min(7, len(daily_loads))]))

    ctl = seed
    atl = seed
    recent_loads = []

    for load in daily_loads:
        ctl = ctl + CTL_LAMBDA * (load - ctl)
        atl = atl + ATL_LAMBDA * (load - atl)
        recent_loads.append(load)

    tsb = ctl - atl
    window_7 = recent_loads[-7:]
    window_28 = recent_loads[-28:]
    acute = float(np.mean(window_7))
    chronic = float(np.mean(window_28)) if window_28 else acute
    acwr = acute / chronic if chronic > 0 else 1.0

    return {
        "ctl": round(ctl, 2),
        "atl": round(atl, 2),
        "tsb": round(tsb, 2),
        "acwr": round(acwr, 3),
    }