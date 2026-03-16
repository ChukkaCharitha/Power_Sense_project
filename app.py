"""
PowerSense - Smart Electricity Bill & Consumption Predictor
Flask Backend: app.py
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from model.predict import predict_bill

app = Flask(__name__)
app.secret_key = 'powersense_secret_key_2024'

DB_PATH = 'powersense.db'


# ── Database Helpers ──────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            members       INTEGER NOT NULL,
            ac_units      INTEGER NOT NULL,
            ac_hours      REAL    NOT NULL,
            fan_hours     REAL    NOT NULL,
            tv_hours      REAL    NOT NULL,
            fridge        INTEGER NOT NULL,
            washing_uses  INTEGER NOT NULL,
            season        TEXT    NOT NULL,
            pred_units    REAL    NOT NULL,
            pred_bill     REAL    NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# ── Utility Functions ─────────────────────────────────────────────────────────

def generate_tips(data: dict) -> list[tuple[str, str]]:
    """Return a list of (icon, tip) energy-saving recommendations."""
    tips = []
    ac_units = data['ac_units']
    ac_hours = data['ac_hours']
    fan_hours = data['fan_hours']
    members = data['members']
    washing_uses = data['washing_uses']
    season = data['season']
    units = data['pred_units']

    if ac_units > 0 and ac_hours > 8:
        tips.append(("🌡️", "Your AC runs over 8 hrs/day — the #1 electricity guzzler. Aim for 6–7 hrs to save 15–20%."))
    if ac_units > 0:
        tips.append(("❄️", "Set your AC to 24°C–26°C. Each degree lower increases consumption by ~6%."))
    if ac_units > 1:
        tips.append(("🔄", "Use a 5-star BEE-rated AC. It consumes up to 40% less power than a 1-star model."))
    if fan_hours > 16:
        tips.append(("💨", "Fans running 16+ hrs/day? Switch to BLDC fans — they save ~50% fan energy."))
    if washing_uses > 15:
        tips.append(("🫧", "Run the washing machine only with full loads and use the cold-water cycle."))
    if members >= 4:
        tips.append(("👨‍👩‍👧", "Larger households save the most by upgrading to 5-star rated appliances."))
    if units > 300:
        tips.append(("📉", "Your usage is high. Track daily meter readings to spot sudden spikes early."))
    tips.append(("💡", "Replace all bulbs with LED — they use 80% less power and last 25× longer."))
    tips.append(("🔌", "Unplug chargers, TVs, and set-top boxes when idle — standby 'phantom' load adds 5–10%."))
    if season == 'summer':
        tips.append(("☀️", "Summer tip: Use curtains/reflective blinds during 10 AM–4 PM to reduce AC load significantly."))
    elif season == 'winter':
        tips.append(("🛁", "Winter tip: Use a solar geyser or heat only the required amount of water — geysers are energy-heavy."))
    elif season == 'monsoon':
        tips.append(("🌧️", "Monsoon tip: Natural ventilation often suffices. Turn off AC and open windows when it's cool."))
    return tips


def calculate_breakdown(data: dict) -> dict[str, float]:
    """Return per-appliance estimated monthly consumption in kWh."""
    ac     = round(data['ac_units'] * data['ac_hours'] * 1.50 * 30, 1)
    fans   = round(data['members'] * 0.5 * data['fan_hours'] * 0.075 * 30, 1)
    tv     = round(data['tv_hours'] * 0.10 * 30, 1)
    fridge = round(0.15 * 24 * 30, 1) if data['fridge'] else 0.0
    wm     = round(data['washing_uses'] * 0.50, 1)
    lights = round((data['members'] + 2) * 7 * 0.04 * 30, 1)
    misc   = round(data['members'] * 5.0, 1)
    return {
        'AC': ac,
        'Fans': fans,
        'TV & Entertainment': tv,
        'Refrigerator': fridge,
        'Washing Machine': wm,
        'Lights': lights,
        'Miscellaneous': misc,
    }


def consumption_level(units: float) -> tuple[str, str, str]:
    """Return (label, Bootstrap color, emoji)."""
    if units < 100:
        return ('Low', 'success', '🌿')
    elif units < 250:
        return ('Moderate', 'warning', '⚡')
    elif units < 450:
        return ('High', 'danger', '🔥')
    else:
        return ('Very High', 'dark', '💸')


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        name         = request.form.get('name', '').strip()
        members      = int(request.form['members'])
        ac_units     = int(request.form['ac_units'])
        ac_hours     = float(request.form['ac_hours'])
        fan_hours    = float(request.form['fan_hours'])
        tv_hours     = float(request.form['tv_hours'])
        fridge       = 1 if request.form.get('fridge') == '1' else 0
        washing_uses = int(request.form['washing_uses'])
        season       = request.form['season']

        # Basic server-side validation
        if not name:
            flash('Please enter your name.', 'danger')
            return redirect(url_for('index'))
        if season not in ('summer', 'winter', 'monsoon'):
            flash('Invalid season selected.', 'danger')
            return redirect(url_for('index'))
        if not (1 <= members <= 12):
            flash('Members must be between 1 and 12.', 'danger')
            return redirect(url_for('index'))

        units, bill = predict_bill(members, ac_units, ac_hours, fan_hours,
                                   tv_hours, fridge, washing_uses, season)

        conn = get_db()
        cur = conn.execute('''
            INSERT INTO predictions
              (name, members, ac_units, ac_hours, fan_hours, tv_hours,
               fridge, washing_uses, season, pred_units, pred_bill)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, members, ac_units, ac_hours, fan_hours, tv_hours,
              fridge, washing_uses, season, units, bill))
        conn.commit()
        pred_id = cur.lastrowid
        conn.close()

        return redirect(url_for('result', pred_id=pred_id))

    except ValueError:
        flash('Invalid input values. Please check all fields and try again.', 'danger')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'danger')
        return redirect(url_for('index'))


@app.route('/result/<int:pred_id>')
def result(pred_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM predictions WHERE id = ?', (pred_id,)).fetchone()
    conn.close()

    if not row:
        flash('Prediction record not found.', 'warning')
        return redirect(url_for('index'))

    data      = dict(row)
    tips      = generate_tips(data)
    breakdown = calculate_breakdown(data)
    level     = consumption_level(data['pred_units'])

    return render_template('result.html',
                           data=data,
                           tips=tips,
                           breakdown=breakdown,
                           level=level)


@app.route('/history')
def history():
    conn    = get_db()
    rows    = conn.execute(
        'SELECT * FROM predictions ORDER BY created_at DESC LIMIT 20'
    ).fetchall()
    conn.close()
    records = [dict(r) for r in rows]
    return render_template('history.html', records=records)


@app.route('/delete/<int:pred_id>', methods=['POST'])
def delete(pred_id):
    conn = get_db()
    conn.execute('DELETE FROM predictions WHERE id = ?', (pred_id,))
    conn.commit()
    conn.close()
    flash('Record deleted successfully.', 'success')
    return redirect(url_for('history'))


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
