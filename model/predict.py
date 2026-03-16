"""
PowerSense - predict.py
Loads the trained model and provides the predict_bill() function used by app.py.
"""

import pickle
import numpy as np
import os

_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')

_SEASON_MAP = {
    'summer':  0,
    'winter':  1,
    'monsoon': 2,
}

def _load_model():
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(
            "model.pkl not found. Please run  python model/train_model.py  first."
        )
    with open(_MODEL_PATH, 'rb') as f:
        return pickle.load(f)

_models = _load_model()


def predict_bill(members: int,
                 ac_units: int,
                 ac_hours: float,
                 fan_hours: float,
                 tv_hours: float,
                 fridge: int,
                 washing_uses: int,
                 season: str) -> tuple[float, float]:
    """
    Returns (predicted_monthly_units_kWh, predicted_monthly_bill_INR).

    Parameters
    ----------
    members       : number of people in household (1-8)
    ac_units      : number of air conditioners (0-4)
    ac_hours      : average AC usage hours per day (0-14)
    fan_hours     : average fan usage hours per day (0-22)
    tv_hours      : average TV/entertainment hours per day (1-10)
    fridge        : 1 if household has refrigerator, else 0
    washing_uses  : number of washing machine uses per month (0-30)
    season        : 'summer' | 'winter' | 'monsoon'
    """
    season_enc = _SEASON_MAP.get(season.lower(), 2)
    features = np.array([[
        int(members),
        int(ac_units),
        float(ac_hours),
        float(fan_hours),
        float(tv_hours),
        int(fridge),
        int(washing_uses),
        season_enc,
    ]])

    units = float(_models['units'].predict(features)[0])
    bill  = float(_models['bill'].predict(features)[0])

    return max(0.0, round(units, 2)), max(0.0, round(bill, 2))
