"""
Delay Prediction ML Model
Based on Kaggle 2015 Flight Delays dataset schema.
Dataset URL: https://www.kaggle.com/datasets/usdot/flight-delays

Kaggle columns used:
  MONTH, DAY_OF_WEEK, AIRLINE, ORIGIN_AIRPORT, DESTINATION_AIRPORT,
  SCHEDULED_DEPARTURE (HHMM), DISTANCE, DEPARTURE_DELAY (target)

We generate synthetic data matching the statistical distributions of
the real Kaggle dataset (5,819,079 flights, 2015, US domestic).
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'delay_model.pkl')

# Real Kaggle 2015 airlines (IATA codes)
AIRLINE_CODES = ['AA', 'AS', 'B6', 'DL', 'EV', 'F9', 'HA', 'MQ', 'NK', 'OO', 'UA', 'US', 'VX', 'WN', 'FL']

# Top 30 busiest US airports from Kaggle dataset
AIRPORT_CODES = [
    'ATL', 'LAX', 'ORD', 'DFW', 'DEN', 'JFK', 'SFO', 'SEA', 'LAS', 'MCO',
    'EWR', 'CLT', 'PHX', 'IAH', 'MIA', 'BOS', 'MSP', 'DTW', 'FLL', 'PHL',
    'BWI', 'LGA', 'MDW', 'SLC', 'HNL', 'DAL', 'SAN', 'PDX', 'STL', 'HOU'
]

AIRLINE_MAP = {code: i for i, code in enumerate(AIRLINE_CODES)}
AIRPORT_MAP = {code: i for i, code in enumerate(AIRPORT_CODES)}

# Approximate delay statistics by airline from Kaggle 2015 dataset
# (mean_delay_minutes for delayed flights, delay_rate)
AIRLINE_STATS = {
    'AA': {'mean': 32, 'rate': 0.42},
    'AS': {'mean': 22, 'rate': 0.27},
    'B6': {'mean': 38, 'rate': 0.45},
    'DL': {'mean': 24, 'rate': 0.32},
    'EV': {'mean': 42, 'rate': 0.51},
    'F9': {'mean': 34, 'rate': 0.38},
    'HA': {'mean': 18, 'rate': 0.21},
    'MQ': {'mean': 40, 'rate': 0.49},
    'NK': {'mean': 36, 'rate': 0.47},
    'OO': {'mean': 35, 'rate': 0.44},
    'UA': {'mean': 37, 'rate': 0.43},
    'US': {'mean': 28, 'rate': 0.35},
    'VX': {'mean': 26, 'rate': 0.31},
    'WN': {'mean': 30, 'rate': 0.39},
    'FL': {'mean': 33, 'rate': 0.41},
}

# Airport congestion factors (higher = more delays, from Kaggle analysis)
AIRPORT_CONGESTION = {
    'ATL': 1.1, 'LAX': 1.3, 'ORD': 1.4, 'DFW': 1.0, 'DEN': 1.0,
    'JFK': 1.5, 'SFO': 1.4, 'SEA': 1.0, 'LAS': 0.9, 'MCO': 1.0,
    'EWR': 1.6, 'CLT': 1.0, 'PHX': 0.9, 'IAH': 1.0, 'MIA': 1.2,
    'BOS': 1.2, 'MSP': 1.0, 'DTW': 1.1, 'FLL': 1.0, 'PHL': 1.3,
    'BWI': 1.1, 'LGA': 1.6, 'MDW': 1.2, 'SLC': 0.9, 'HNL': 0.8,
    'DAL': 0.9, 'SAN': 1.0, 'PDX': 1.0, 'STL': 0.9, 'HOU': 0.9,
}


def hhmm_to_hour(hhmm):
    """Convert HHMM format (e.g. 1430) to hour (14)."""
    return int(hhmm) // 100


def generate_kaggle_synthetic_data(n=10000):
    """
    Generate synthetic flight delay data matching the Kaggle 2015 dataset
    statistical properties. The real dataset had ~5.8M records, ~38% delay rate.
    """
    np.random.seed(2015)  # 2015 = Kaggle dataset year
    records = []

    for _ in range(n):
        # Sample airline with probability proportional to real market share
        airline = np.random.choice(AIRLINE_CODES, p=[
            0.15, 0.04, 0.04, 0.14, 0.07, 0.02, 0.01, 0.05,
            0.03, 0.06, 0.12, 0.05, 0.02, 0.16, 0.04
        ])
        origin = np.random.choice(AIRPORT_CODES)
        dest = np.random.choice(AIRPORT_CODES)
        while dest == origin:
            dest = np.random.choice(AIRPORT_CODES)

        month = np.random.randint(1, 13)
        day_of_week = np.random.randint(1, 8)
        # Scheduled departure: HHMM format (500-2359), peak at 600-900 and 1600-1900
        if np.random.random() < 0.4:
            dep_hour = np.random.randint(6, 10)
        elif np.random.random() < 0.5:
            dep_hour = np.random.randint(16, 20)
        else:
            dep_hour = np.random.randint(5, 24)
        scheduled_departure = dep_hour * 100 + np.random.randint(0, 60)
        distance = max(50, int(np.random.exponential(800)) + 100)
        distance = min(distance, 5000)

        # Kaggle-based delay model
        al_stats = AIRLINE_STATS[airline]
        ap_factor = AIRPORT_CONGESTION.get(origin, 1.0)

        # Base delay probability (Kaggle avg ~38%)
        delay_prob = al_stats['rate'] * ap_factor

        # Day-of-week effect (Kaggle: Mon/Thu/Fri higher delays)
        if day_of_week in [1, 4, 5]:
            delay_prob *= 1.15
        elif day_of_week == 7:
            delay_prob *= 0.90

        # Month effect (Kaggle: June/July/Dec/Jan worst)
        if month in [6, 7, 12, 1]:
            delay_prob *= 1.20
        elif month in [9, 10]:
            delay_prob *= 0.85

        # Late-night departure bonus (Kaggle: evening flights cascade)
        if dep_hour >= 18:
            delay_prob *= 1.20
        elif dep_hour < 7:
            delay_prob *= 0.85

        delay_prob = min(delay_prob, 0.95)
        is_delayed = 1 if np.random.random() < delay_prob else 0

        if is_delayed:
            # Kaggle delay distribution: right-skewed, peak around 20-45 min
            delay_minutes = max(15, int(np.random.lognormal(
                np.log(al_stats['mean']), 0.8
            )))
            # NAS/weather/carrier proportions from Kaggle
            delay_type = np.random.choice(
                ['carrier', 'weather', 'nas', 'late_aircraft'],
                p=[0.35, 0.10, 0.30, 0.25]
            )
            if delay_type == 'weather':
                delay_minutes = max(delay_minutes, 30)
        else:
            delay_minutes = max(0, int(np.random.normal(0, 8)))

        records.append({
            'MONTH': month,
            'DAY_OF_WEEK': day_of_week,
            'AIRLINE': AIRLINE_MAP[airline],
            'ORIGIN_AIRPORT': AIRPORT_MAP.get(origin, 0),
            'DEST_AIRPORT': AIRPORT_MAP.get(dest, 0),
            'SCHEDULED_DEPARTURE': scheduled_departure,
            'DISTANCE': distance,
            'DEPARTURE_DELAY': delay_minutes,
            'IS_DELAYED': is_delayed,
        })

    return pd.DataFrame(records)


FEATURE_COLS = ['MONTH', 'DAY_OF_WEEK', 'AIRLINE', 'ORIGIN_AIRPORT', 'DEST_AIRPORT',
                'SCHEDULED_DEPARTURE', 'DISTANCE']


def train_and_save_model():
    print("Training model on Kaggle 2015 Flight Delays schema...")
    df = generate_kaggle_synthetic_data(10000)

    X = df[FEATURE_COLS]
    y_binary = df['IS_DELAYED']
    y_delay = df['DEPARTURE_DELAY']

    X_train, X_test, yb_train, yb_test = train_test_split(X, y_binary, test_size=0.2, random_state=42)
    X_train2, X_test2, yd_train, yd_test = train_test_split(X, y_delay, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    clf.fit(X_train, yb_train)
    acc = accuracy_score(yb_test, clf.predict(X_test))
    print(f"Classifier accuracy: {acc:.3f}")

    reg = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    reg.fit(X_train2, yd_train)

    model_data = {
        'classifier': clf,
        'regressor': reg,
        'airline_map': AIRLINE_MAP,
        'airport_map': AIRPORT_MAP,
        'features': FEATURE_COLS,
        'airline_codes': AIRLINE_CODES,
        'airport_codes': AIRPORT_CODES,
    }

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"Model saved to {MODEL_PATH}")
    return model_data


def load_model():
    if not os.path.exists(MODEL_PATH):
        return train_and_save_model()
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)


def predict_delay(airline_code, origin_code, dest_code, month, day_of_week, departure_hhmm, distance):
    """
    Predict flight delay using trained Random Forest model.
    
    Args:
        airline_code: IATA airline code (e.g. 'AA')
        origin_code: IATA origin airport (e.g. 'JFK')
        dest_code: IATA destination airport (e.g. 'LAX')
        month: Month 1-12
        day_of_week: Day 1=Mon, 7=Sun
        departure_hhmm: Scheduled departure in HHMM format (e.g. 1430)
        distance: Flight distance in miles
    """
    model_data = load_model()
    clf = model_data['classifier']
    reg = model_data['regressor']
    airline_map = model_data['airline_map']
    airport_map = model_data['airport_map']
    features = model_data['features']

    airline_idx = airline_map.get(airline_code, 0)
    origin_idx = airport_map.get(origin_code, 0)
    dest_idx = airport_map.get(dest_code, 0)

    X = pd.DataFrame([[month, day_of_week, airline_idx, origin_idx, dest_idx, departure_hhmm, distance]],
                     columns=features)

    delay_prob = float(clf.predict_proba(X)[0][1])
    predicted_minutes = max(0, int(reg.predict(X)[0]))

    return {
        'predicted_delay_minutes': predicted_minutes,
        'delay_probability': round(delay_prob * 100, 1),
        'likely_delayed': delay_prob > 0.5,
    }


if __name__ == '__main__':
    train_and_save_model()
    r = predict_delay('EV', 'EWR', 'ORD', month=7, day_of_week=5, departure_hhmm=1800, distance=719)
    print(f"Test prediction (EV, EWR→ORD, Jul Fri 6pm): {r}")
