"""
PowerSense - Electricity Bill Predictor
Model Training Script

Dataset: Synthetic data based on real Telangana (TSSPDCL) electricity tariff slabs.
Features: household size, appliance usage, season
Targets : monthly units (kWh) + monthly bill (INR)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os

np.random.seed(42)
N = 6000  # number of training samples

# ── Feature Generation ────────────────────────────────────────────────────────
members       = np.random.randint(1, 9, N)                              # 1-8 people
ac_units      = np.random.choice([0, 1, 2, 3, 4], N, p=[0.15, 0.40, 0.30, 0.10, 0.05])
ac_hours      = np.where(ac_units > 0, np.random.uniform(1, 14, N), 0.0)
fan_hours     = np.random.uniform(3, 22, N)
tv_hours      = np.random.uniform(1, 10, N)
fridge        = np.random.choice([0, 1], N, p=[0.08, 0.92])
washing_uses  = np.random.randint(0, 31, N)   # times/month
season        = np.random.choice([0, 1, 2], N)  # 0=Summer, 1=Winter, 2=Monsoon

light_count   = members + np.random.randint(1, 4, N)
light_hours   = np.random.uniform(4, 12, N)

# ── Physics-based Monthly Unit Calculation (kWh) ─────────────────────────────
monthly_units = (
    ac_units    * ac_hours    * 1.50 * 30  +   # AC       ~1.5 kWh/hr/unit
    members     * 0.5         * fan_hours * 0.075 * 30 +  # Fans  ~0.075 kWh/hr
    tv_hours    * 0.10 * 30  +                  # TV       ~0.10 kWh/hr
    fridge      * 0.15 * 24 * 30 +             # Fridge   ~108 kWh/month
    washing_uses * 0.50 +                       # W.M.     ~0.5 kWh/use
    light_count * light_hours * 0.04 * 30 +    # Lights   ~0.04 kWh/hr
    members * 5.0                               # Misc chargers, pumps, etc.
)

# Season multiplier
season_mult = np.where(season == 0, 1.25,        # Summer  : more AC
              np.where(season == 1, 0.82, 1.00))  # Winter  : less AC
monthly_units = monthly_units * season_mult

# Add realistic noise ± 8%
monthly_units += np.random.normal(0, monthly_units * 0.08)
monthly_units  = np.clip(monthly_units, 10, 4000).round(2)


# ── TSSPDCL Tariff Slab Calculator ───────────────────────────────────────────
def calculate_bill(units: float) -> float:
    """
    Telangana State Southern Power Distribution Company Ltd (TSSPDCL)
    Domestic (LT-1) tariff slabs (approximate 2024 rates).
    """
    slabs = [
        (50,  1.45),
        (50,  2.60),
        (100, 3.50),
        (100, 5.00),
        (100, 6.00),
    ]
    remaining = units
    bill = 0.0
    for limit, rate in slabs:
        consumed = min(remaining, limit)
        bill += consumed * rate
        remaining -= consumed
        if remaining <= 0:
            break
    if remaining > 0:              # above 400 units
        bill += remaining * 8.50
    bill += 50                     # fixed monthly charge
    return round(bill, 2)

monthly_bill = np.array([calculate_bill(u) for u in monthly_units])

# ── Build DataFrame ───────────────────────────────────────────────────────────
df = pd.DataFrame({
    'members':      members,
    'ac_units':     ac_units,
    'ac_hours':     ac_hours,
    'fan_hours':    fan_hours,
    'tv_hours':     tv_hours,
    'fridge':       fridge,
    'washing_uses': washing_uses,
    'season':       season,
    'monthly_units': monthly_units,
    'monthly_bill':  monthly_bill,
})

FEATURES = ['members', 'ac_units', 'ac_hours', 'fan_hours',
            'tv_hours', 'fridge', 'washing_uses', 'season']

X      = df[FEATURES].values
y_units = df['monthly_units'].values
y_bill  = df['monthly_bill'].values

X_tr, X_te, yu_tr, yu_te, yb_tr, yb_te = train_test_split(
    X, y_units, y_bill, test_size=0.2, random_state=42
)

# ── Train Models ──────────────────────────────────────────────────────────────
print("Training Units model ...")
model_units = RandomForestRegressor(n_estimators=150, max_depth=20,
                                    min_samples_leaf=2, random_state=42, n_jobs=-1)
model_units.fit(X_tr, yu_tr)

print("Training Bill model ...")
model_bill = RandomForestRegressor(n_estimators=150, max_depth=20,
                                   min_samples_leaf=2, random_state=42, n_jobs=-1)
model_bill.fit(X_tr, yb_tr)

# ── Evaluate ──────────────────────────────────────────────────────────────────
print("\n── Model Evaluation ──────────────────────────")
print(f"  Units  MAE : {mean_absolute_error(yu_te, model_units.predict(X_te)):.2f} kWh")
print(f"  Units  R²  : {r2_score(yu_te, model_units.predict(X_te)):.4f}")
print(f"  Bill   MAE : ₹{mean_absolute_error(yb_te, model_bill.predict(X_te)):.2f}")
print(f"  Bill   R²  : {r2_score(yb_te, model_bill.predict(X_te)):.4f}")

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(__file__), exist_ok=True)
model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
with open(model_path, 'wb') as f:
    pickle.dump({'units': model_units, 'bill': model_bill, 'features': FEATURES}, f)

print(f"\n✅  Model saved → {model_path}")
