"""
(Claude generated)
Synthetic training-load data generator.

Simulates N athletes over ~12 months of daily training, computes real
sports-science load metrics (session-RPE load, CTL, ATL, TSB, ACWR),
and generates a probabilistic, state-adaptive injury label.

Deliberately injects realistic messiness: rest days, missing fields,
sensor errors (this data requires real cleaning before modeling, same as real-world data would).
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass

rng = np.random.default_rng(seed=42)  # reproducible randomness

N_ATHLETES = 60
N_DAYS = 365

CTL_LAMBDA = 1 - np.exp(-1 / 42)   # 42-day EWMA decay
ATL_LAMBDA = 1 - np.exp(-1 / 7)    # 7-day EWMA decay

@dataclass
class Athlete:
    athlete_id: int
    training_age_years: float   # 0.5 = beginner, 10+ = veteran
    baseline_load: float        # "normal" session-RPE load on an average training day
    consistency: float          # 0-1: how regular their training schedule is


def make_athletes(n: int) -> list[Athlete]:
    athletes = []
    for i in range(n):
        # mix of beginners, intermediates, veterans
        training_age = rng.choice(
            [rng.uniform(0.2, 2), rng.uniform(2, 6), rng.uniform(6, 15)],
            p=[0.4, 0.35, 0.25],
        )
        # more training age -> higher sustainable baseline load (session-RPE units)
        baseline_load = max(150 + training_age * 25 + rng.normal(0, 20), 60)

        # some athletes are steady, some erratic -- per your point about real variation
        consistency = rng.choice([rng.uniform(0.7, 0.95), rng.uniform(0.2, 0.5)], p=[0.6, 0.4])

        athletes.append(Athlete(
            athlete_id=i + 1,
            training_age_years=round(training_age, 2),
            baseline_load=round(baseline_load, 1),
            consistency=round(consistency, 2),
        ))
    return athletes

def pick_spike_windows(n_days: int) -> set:
    """Randomly choose several multi-day 'training spike' windows across the year."""
    spike_days = set()
    n_spikes = rng.integers(3, 8)  # a handful of spike periods over the year
    for _ in range(n_spikes):
        start = rng.integers(0, n_days - 14)
        length = rng.integers(5, 14)
        spike_days.update(range(start, start + length))
    return spike_days

def simulate_athlete(athlete: Athlete, n_days: int) -> pd.DataFrame:
    spike_days = pick_spike_windows(n_days)

    ctl = athlete.baseline_load * 0.9  # seed near steady-state so early rows aren't degenerate
    atl = athlete.baseline_load * 0.9
    recent_loads = []  # rolling history for ACWR (7d/28d simple rolling avg)

    susceptibility = 1.0       # adaptive multiplier -- rises after injuries, decays when stable
    recovering_days_left = 0  # >0 means athlete is in enforced recovery, minimal load

    rows = []

    for day in range(n_days):
        rest_day_prob = 1 - athlete.consistency
        is_rest_day = rng.random() < rest_day_prob or recovering_days_left > 0

        if is_rest_day:
            duration = 0.0
            intensity = 0
            rpe = 0
            speed = 0.0
            avg_hr = 0
            session_type = "rest"
            daily_load = 0.0
        else:
            # spike days: THIS athlete's own baseline gets multiplied up, not an absolute jump
            multiplier = rng.uniform(1.4, 2.0) if day in spike_days else rng.uniform(0.8, 1.15)
            duration = max(rng.normal(60, 15), 15)  # minutes
            rpe = int(np.clip(rng.normal(6, 1.5) * multiplier, 1, 10))
            intensity = int(np.clip(rpe + rng.integers(-1, 2), 1, 10))
            speed = round(max(rng.normal(10, 2), 4), 1)  # km/h, rough proxy
            avg_hr = int(np.clip(rng.normal(150, 15), 90, 200))
            session_type = rng.choice(["easy_run", "tempo", "intervals", "long_run", "recovery", "race"])

            daily_load = duration * rpe * multiplier
            daily_load = daily_load * (athlete.baseline_load / 400)  # scale to this athlete's own range

        # --- update CTL / ATL (EWMA) and TSB ---
        ctl = ctl + CTL_LAMBDA * (daily_load - ctl)
        atl = atl + ATL_LAMBDA * (daily_load - atl)
        tsb = ctl - atl

        # --- ACWR: 7-day rolling avg / 28-day rolling avg ---
        recent_loads.append(daily_load)
        window_28 = recent_loads[-28:]
        window_7 = recent_loads[-7:]
        acute = np.mean(window_7)
        chronic = np.mean(window_28) if window_28 else acute
        acwr = acute / chronic if chronic > 0 else 1.0

        # --- injury probability: driven by ACWR relative to THIS athlete, not absolute load ---
        base_risk = 0.002
        acwr_risk = max(0, (acwr - 1.3)) ** 2 * 0.15
        daily_injury_prob = np.clip((base_risk + acwr_risk) * susceptibility, 0, 0.9)

        injured_today = False
        if recovering_days_left == 0 and rng.random() < daily_injury_prob:
            injured_today = True
            recovering_days_left = int(rng.integers(7, 21))  # forced recovery period
            susceptibility = min(susceptibility * 1.3, 3.0)   # each injury raises future susceptibility
        else:
            # susceptibility slowly decays back toward baseline when training is stable
            susceptibility = max(1.0, susceptibility * 0.995)

        if recovering_days_left > 0:
            recovering_days_left -= 1

        rows.append(dict(
            athlete_id=athlete.athlete_id,
            day=day,
            training_age_years=athlete.training_age_years,
            is_rest_day=is_rest_day,
            session_type=session_type,
            duration_min=round(duration, 1),
            intensity=intensity,
            rpe=rpe,
            speed_kmh=speed,
            avg_hr=avg_hr,
            daily_load=round(daily_load, 1),
            ctl=round(ctl, 2),
            atl=round(atl, 2),
            tsb=round(tsb, 2),
            acwr=round(acwr, 3),
            injured=int(injured_today),
        ))

    return pd.DataFrame(rows)


def inject_messiness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add realistic missingness and sensor errors, per your point #4:
    - specific fields randomly missing (athlete forgot to log something)
    - occasional clearly-wrong sensor values (HR spikes, negative durations, etc.)
    Rest days are left alone -- missing data on a rest day isn't really "missing," it's zero.
    """
    df = df.copy()
    trainable_mask = df["is_rest_day"] == False  # noqa: E712

    # --- missing fields (set to NaN), only on training days ---
    for col, missing_rate in [("avg_hr", 0.06), ("speed_kmh", 0.04), ("rpe", 0.03)]:
        idx = df[trainable_mask].sample(frac=missing_rate, random_state=1).index
        df.loc[idx, col] = np.nan

    # --- sensor errors: implausible values injected on a small fraction of rows ---
    hr_error_idx = df[trainable_mask].sample(frac=0.01, random_state=2).index
    df.loc[hr_error_idx, "avg_hr"] = rng.integers(220, 260, size=len(hr_error_idx))  # implausible HR

    speed_error_idx = df[trainable_mask].sample(frac=0.01, random_state=3).index
    df.loc[speed_error_idx, "speed_kmh"] = rng.uniform(40, 60, size=len(speed_error_idx))  # implausible speed

    duration_error_idx = df[trainable_mask].sample(frac=0.005, random_state=4).index
    df.loc[duration_error_idx, "duration_min"] = -rng.uniform(1, 10, size=len(duration_error_idx))  # negative

    return df


def main():
    athletes = make_athletes(N_ATHLETES)
    all_rows = [simulate_athlete(a, N_DAYS) for a in athletes]
    df = pd.concat(all_rows, ignore_index=True)
    df = inject_messiness(df)

    out_path = "sentinel_data.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows across {N_ATHLETES} athletes to {out_path}")
    print(f"Injury rate: {df['injured'].mean():.3%}")
    print(df.head(10).to_string())


if __name__ == "__main__":
    main()