"""
Gets features, calls model and generates a prediction

must match, column for column, what train.py expects: 

['training_age_years', 'is_rest_day', 'duration_min', 'intensity', 'rpe',
 'speed_kmh', 'avg_hr', 'daily_load', 'ctl', 'atl', 'tsb', 'acwr',
 'session_type_easy_run', 'session_type_intervals', 'session_type_long_run',
 'session_type_rest', 'session_type_tempo']
"""

from datetime import date, timedelta
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Workout, Athlete
from features import compute_rolling_features
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "ML"

model = joblib.load(MODEL_DIR / "injury_risk_model.pkl")
encoder = joblib.load(MODEL_DIR / "session_type_encoder.pkl")

async def predict_injury_risk(user_id: int, db: AsyncSession) -> dict | None:
    today = date.today()
    window_start = today - timedelta(days=41)

    stmt = (
        select(Workout)
        .where(Workout.athlete_id == user_id, Workout.date >= window_start)
        .order_by(Workout.date.asc())
    )
    athlete_stmt = select(Athlete).where(Athlete.id == user_id)

    result = await db.execute(stmt)
    workouts = result.scalars().all()
    result2 = await db.execute(athlete_stmt)
    athlete_info = result2.scalar_one_or_none()

    if athlete_info is None:
        return None

    # build the day-by-day load sequence (rest days = 0), same as ml_features.py
    loads_by_date = {}
    for w in workouts:
        daily_load = w.duration * w.rpe
        loads_by_date[w.date] = loads_by_date.get(w.date, 0) + daily_load

    daily_loads = []
    current = window_start
    while current <= today:
        daily_loads.append(loads_by_date.get(current, 0))
        current += timedelta(days=1)

    seed = athlete_info.baseline_load * 0.9 if athlete_info.baseline_load else None
    rolling = compute_rolling_features(daily_loads, seed=seed)

    most_recent = workouts[-1] if workouts else None
    is_today = most_recent is not None and most_recent.date == today

    if is_today:
        duration_min = most_recent.duration
        intensity = most_recent.intensity
        rpe = most_recent.rpe
        speed_kmh = most_recent.speed
        avg_hr = most_recent.average_hr
        session_type = most_recent.session_type
        is_rest_day = False
        daily_load = duration_min * rpe
    else:
        duration_min = 0.0
        intensity = 0
        rpe = 0
        speed_kmh = 0.0
        avg_hr = 0
        session_type = "rest"
        is_rest_day = True
        daily_load = 0.0

    row = {
        "training_age_years": athlete_info.training_age_years or 0,
        "is_rest_day": is_rest_day,
        "duration_min": duration_min,
        "intensity": intensity,
        "rpe": rpe,
        "speed_kmh": speed_kmh,
        "avg_hr": avg_hr,
        "daily_load": daily_load,
        "ctl": rolling["ctl"],
        "atl": rolling["atl"],
        "tsb": rolling["tsb"],
        "acwr": rolling["acwr"],
        "session_type": session_type,
    }

    features_df = pd.DataFrame([row])

    # one-hot encode session_type using the same fitted encoder from training
    encoded = encoder.transform(features_df[["session_type"]])
    encoded_cols = encoder.get_feature_names_out(["session_type"])
    encoded_df = pd.DataFrame(encoded, columns=encoded_cols)

    final_row = pd.concat(
        [features_df.drop(columns=["session_type"]).reset_index(drop=True), encoded_df], axis=1
    )
    final_row = final_row.reindex(columns=model.feature_names_in_, fill_value=0)

    probability = model.predict_proba(final_row)[0][1]

    return {
        "athlete_id": user_id,
        "injury_risk_probability": round(float(probability), 3),
        "acwr": rolling["acwr"],
        "tsb": rolling["tsb"],
        "ctl": rolling["ctl"],
        "atl": rolling["atl"],
    }