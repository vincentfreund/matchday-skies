"""
Matchday Skies - build the data file the demo page reads.

What this does
--------------
1. Builds hourly traffic profiles for Munich Airport (MUC) on three kinds of day:
   a normal Saturday, a Bayern Bundesliga home game and a Champions League night.
2. Trains a simple delay model (linear regression) that estimates average
   arrival delay at MUC around a match, with features for the match itself
   AND for "other causes" (weather, Oktoberfest, trade fairs, holiday peaks).
3. Writes everything to ../data/demo_data.js, which index.html loads.

IMPORTANT: right now the input data is SIMULATED (see simulate_days()).
To go live, replace simulate_days() and hourly_profiles() with loaders for
real data, e.g. OpenSky Network flight tracks + DWD weather + a match calendar.
The page does not need to change: it only reads the JSON structure written here.

Run:  python model/build_demo_data.py
Needs: numpy  (pip install -r requirements.txt)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RNG = np.random.default_rng(42)
OUT = Path(__file__).resolve().parent.parent / "data" / "demo_data.js"

HOURS = list(range(24))

# --------------------------------------------------------------------------
# 1. Hourly profiles  (movements per hour at MUC)
# --------------------------------------------------------------------------

def base_saturday():
    """Typical Saturday shape: night curfew, morning bank, afternoon/evening banks."""
    arr = [1, 0, 0, 0, 0, 3, 18, 30, 34, 33, 31, 30, 29, 31, 33, 32, 30, 31, 33, 32, 28, 22, 14, 6]
    dep = [1, 0, 0, 0, 0, 6, 32, 36, 33, 31, 30, 30, 31, 30, 29, 31, 32, 30, 29, 27, 24, 16, 8, 3]
    biz = [0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 0, 0, 0]
    delay = [4, 0, 0, 0, 0, 3, 4, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 11, 10, 9, 6]
    return {"arrivals": arr, "departures": dep, "bizjets": biz, "avgDelay": delay}


def add_bump(series, centre, width, height):
    """Add a smooth bump (Gaussian) to an hourly series, e.g. fans flying in."""
    return [round(v + height * np.exp(-((h - centre) ** 2) / (2 * width ** 2)), 1)
            for h, v in enumerate(series)]


def hourly_profiles():
    normal = base_saturday()

    # Bundesliga, kickoff 15:30: domestic away fans mostly travel by train/car,
    # a modest extra flow of arrivals + business jets before kickoff, departures after.
    bl = {k: list(v) for k, v in normal.items()}
    bl["arrivals"] = add_bump(bl["arrivals"], 12, 1.5, 4)
    bl["departures"] = add_bump(bl["departures"], 19.5, 1.5, 5)
    bl["bizjets"] = add_bump(add_bump(bl["bizjets"], 12.5, 1.2, 4), 18.5, 1.0, 4)
    bl["avgDelay"] = add_bump(bl["avgDelay"], 19, 1.5, 4)

    # Champions League, kickoff 21:00: away charters land midday, leave after the match,
    # extra business jets, and late departures push into the night curfew edge.
    ucl = {k: list(v) for k, v in normal.items()}
    ucl["arrivals"] = add_bump(ucl["arrivals"], 13, 2.0, 9)
    ucl["departures"] = add_bump(ucl["departures"], 23.2, 0.8, 10)
    ucl["bizjets"] = add_bump(add_bump(ucl["bizjets"], 16, 1.8, 6), 23.3, 0.7, 7)
    ucl["avgDelay"] = add_bump(add_bump(ucl["avgDelay"], 13, 2.0, 5), 23, 1.0, 9)

    return {
        "normal": {"label": "Normal Saturday", "kickoff": None, **normal},
        "bundesliga": {"label": "Bundesliga home game", "kickoff": 15.5, **bl},
        "ucl": {"label": "Champions League night", "kickoff": 21.0, **ucl},
    }


# --------------------------------------------------------------------------
# 2. Delay model
# --------------------------------------------------------------------------

FEATURES = [
    # name,                group,    label shown in the page
    ("comp_bundesliga",     "match",  "Bundesliga match"),
    ("comp_pokal",          "match",  "DFB-Pokal match"),
    ("comp_ucl_group",      "match",  "Champions League (league phase)"),
    ("comp_ucl_ko",         "match",  "Champions League knockout"),
    ("kickoff_evening",     "match",  "Evening kickoff (18:30)"),
    ("kickoff_night",       "match",  "Night kickoff (21:00)"),
    ("away_fans_fly",       "match",  "Away fans travel by air"),
    ("weather_rain",        "other",  "Rain"),
    ("weather_fog",         "other",  "Fog / low visibility"),
    ("weather_storm",       "other",  "Thunderstorms"),
    ("weather_snow",        "other",  "Snow / de-icing"),
    ("oktoberfest",         "other",  "Oktoberfest running"),
    ("trade_fair",          "other",  "Big trade fair (Messe)"),
    ("holiday_peak",        "other",  "School-holiday travel peak"),
]

# "True" effects used only to simulate training data (minutes of extra delay).
TRUE_EFFECTS = {
    "comp_bundesliga": 2.0, "comp_pokal": 2.5, "comp_ucl_group": 4.0, "comp_ucl_ko": 6.5,
    "kickoff_evening": 1.0, "kickoff_night": 2.5, "away_fans_fly": 3.0,
    "weather_rain": 3.0, "weather_fog": 9.0, "weather_storm": 14.0, "weather_snow": 12.0,
    "oktoberfest": 4.5, "trade_fair": 3.0, "holiday_peak": 5.0,
}
TRUE_INTERCEPT = 8.0


def simulate_days(n=3000):
    """Fake historical days. REPLACE with real days built from flight + weather data."""
    names = [f[0] for f in FEATURES]
    X = np.zeros((n, len(names)))
    idx = {name: i for i, name in enumerate(names)}
    for row in X:
        comp = RNG.choice(["none", "comp_bundesliga", "comp_pokal", "comp_ucl_group", "comp_ucl_ko"],
                          p=[0.6, 0.22, 0.04, 0.09, 0.05])
        if comp != "none":
            row[idx[comp]] = 1
            ko = RNG.choice(["day", "kickoff_evening", "kickoff_night"], p=[0.5, 0.2, 0.3])
            if ko != "day":
                row[idx[ko]] = 1
            row[idx["away_fans_fly"]] = RNG.random() < (0.7 if "ucl" in comp else 0.2)
        weather = RNG.choice(["clear", "weather_rain", "weather_fog", "weather_storm", "weather_snow"],
                             p=[0.6, 0.22, 0.07, 0.06, 0.05])
        if weather != "clear":
            row[idx[weather]] = 1
        row[idx["oktoberfest"]] = RNG.random() < 0.05
        row[idx["trade_fair"]] = RNG.random() < 0.08
        row[idx["holiday_peak"]] = RNG.random() < 0.12
    beta = np.array([TRUE_EFFECTS[nm] for nm in names])
    y = TRUE_INTERCEPT + X @ beta + RNG.normal(0, 3.0, n)
    return X, np.clip(y, 0, None)


def fit_linear(X, y):
    """Ordinary least squares with an intercept. Returns intercept, coefs, R^2, MAE."""
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ beta
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    mae = np.abs(y - pred).mean()
    return beta[0], beta[1:], r2, mae


def build_model():
    X, y = simulate_days()
    intercept, coefs, r2, mae = fit_linear(X, y)
    return {
        "target": "Average arrival delay at MUC, 3 hours around kickoff (minutes)",
        "intercept": round(float(intercept), 2),
        "features": [
            {"name": n, "group": g, "label": lab, "coef": round(float(c), 2)}
            for (n, g, lab), c in zip(FEATURES, coefs)
        ],
        "r2": round(float(r2), 3),
        "mae": round(float(mae), 2),
        "trainingDays": int(len(y)),
    }


# --------------------------------------------------------------------------
# 3. Write the data file
# --------------------------------------------------------------------------

def main():
    data = {
        "meta": {
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "simulated": True,
            "note": "Simulated prototype data. Replace simulate_days() and hourly_profiles() with real sources.",
        },
        "scenarios": hourly_profiles(),
        "model": build_model(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "// Generated by model/build_demo_data.py - do not edit by hand.\n"
        "window.MATCHDAY_DATA = " + json.dumps(data, indent=2) + ";\n",
        encoding="utf-8",
    )
    m = data["model"]
    print(f"Wrote {OUT}")
    print(f"Model: R^2={m['r2']}  MAE={m['mae']} min  on {m['trainingDays']} simulated days")


if __name__ == "__main__":
    main()
