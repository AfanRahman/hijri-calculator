from flask import Flask, render_template_string, request
from datetime import datetime
from hijridate import Gregorian, Hijri  # Works with both hijridate and hijri-converter

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hijri Birth Date & Age Calculator</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f4f8; margin: 0; padding: 30px; display: flex; justify-content: center; }
        .container { background: white; padding: 35px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); max-width: 450px; width: 100%; text-align: center; }
        h2 { color: #1b4d3e; margin-bottom: 25px; font-size: 26px; }
        .form-group { text-align: left; margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; color: #4a5568; font-weight: 600; font-size: 14px; }
        input[type="date"], select { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; font-size: 16px; background-color: #fff; }
        button { background-color: #1b4d3e; color: white; border: none; padding: 14px 20px; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold; margin-top: 10px; transition: background 0.2s; }
        button:hover { background-color: #12352a; }
        .result-box { margin-top: 30px; padding: 20px; background-color: #f4fbf7; border-left: 5px solid #1b4d3e; text-align: left; border-radius: 6px; }
        .age-text { font-size: 18px; color: #2d3748; margin-top: 8px; line-height: 1.5; }
        .comparison { font-size: 13px; color: #718096; margin-top: 10px; font-style: italic; border-top: 1px dashed #cbd5e1; padding-top: 8px; }
        .error { color: #721c24; background-color: #f8d7da; border-left: 5px solid #dc3545; }
    </style>
</head>
<body>

<div class="container">
    <h2>Hijri Birthday Calculator</h2>
    <form method="POST">
        <div class="form-group">
            <label for="g_date">Select Gregorian Birth Date:</label>
            <input type="date" id="g_date" name="g_date" value="{{ selected_date }}" required>
        </div>
        
        <div class="form-group">
            <label for="offset">Regional Hijri Adjustment:</label>
            <select id="offset" name="offset">
                <option value="-1" {% if offset == '-1' %}selected{% endif %}>Minus 1 day (e.g., often parts of Europe/Americas)</option>
                <option value="0" {% if offset == '0' or not offset %}selected{% endif %}>Standard (Umm al-Qura / UAE / Saudi)</option>
                <option value="1" {% if offset == '1' %}selected{% endif %}>Plus 1 day (e.g., often India / Pakistan / Morocco)</option>
                <option value="2" {% if offset == '2' %}selected{% endif %}>Plus 2 days</option>
            </select>
        </div>
        
        <button type="submit">Calculate Age & Hijri Date</button>
    </form>

    {% if hijri_date_str %}
    <div class="result-box">
        <div style="color: #1b4d3e; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Your Hijri Birth Date</div>
        <div style="font-size: 22px; font-weight: bold; margin: 5px 0 15px 0; color: #1a202c;">{{ hijri_date_str }}</div>
        
        <div style="color: #1b4d3e; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Your Age in Hijri Time</div>
        <div class="age-text">
            <strong>{{ h_years }}</strong> years, <strong>{{ h_months }}</strong> months, and <strong>{{ h_days }}</strong> days old.
        </div>
        
        <div class="comparison">
            Note: In Solar (Gregorian) time, you are {{ g_years }} years old. You are "older" in the Hijri calendar because lunar years are shorter!
        </div>
    </div>
    {% elif error %}
    <div class="result-box error">
        <strong>Error:</strong><br>
        {{ error }}
    </div>
    {% endif %}
</div>

</body>
</html>
"""

def calculate_hijri_age(birth_hijri, current_hijri):
    """Calculates age breakdown purely in Hijri years, months, and days."""
    years = current_hijri.year - birth_hijri.year
    months = current_hijri.month - birth_hijri.month
    days = current_hijri.day - birth_hijri.day

    if days < 0:
        months -= 1
        days += 30  # Approximation of lunar month length
    if months < 0:
        years -= 1
        months += 12
        
    return years, months, days

@app.route('/', methods=['GET', 'POST'])
def index():
    hijri_date_str = None
    error = None
    selected_date = ""
    offset = "0"
    h_years, h_months, h_days = 0, 0, 0
    g_years = 0

    if request.method == 'POST':
        selected_date = request.form.get('g_date')
        offset = request.form.get('offset', '0')
        day_shift = int(offset)
        
        try:
            # 1. Parse Input Date
            birth_greg = datetime.strptime(selected_date, '%Y-%m-%d').date()
            today_greg = datetime.today().date()
            
            if birth_greg > today_greg:
                error = "Birth date cannot be in the future!"
                return render_template_string(HTML_TEMPLATE, error=error, selected_date=selected_date, offset=offset)

            # 2. Apply Local Region Offset Adjustment directly to the Gregorian date object
            if day_shift != 0:
                adjusted_greg_dn = birth_greg.toordinal() + day_shift
                birth_greg = datetime.fromordinal(adjusted_greg_dn).date()

            # 3. Convert to Hijri safely across library versions
            birth_hijri = Gregorian(birth_greg.year, birth_greg.month, birth_greg.day).to_hijri()

            # Format Hijri Birth String
            hijri_date_str = f"{birth_hijri.day} {birth_hijri.month_name()} {birth_hijri.year} AH"

            # 4. Get Current Hijri Date for Today
            current_hijri = Gregorian(today_greg.year, today_greg.month, today_greg.day).to_hijri()

            # 5. Calculate Age Breakdowns
            h_years, h_months, h_days = calculate_hijri_age(birth_hijri, current_hijri)
            g_years = today_greg.year - birth_greg.year - ((today_greg.month, today_greg.day) < (birth_greg.month, birth_greg.day))

        except ValueError:
            error = "Selected date is outside the supported calendar range (1343 AH - 1500 AH)."
        except Exception as e:
            error = f"An error occurred: {str(e)}"

    return render_template_string(
        HTML_TEMPLATE, 
        hijri_date_str=hijri_date_str, 
        error=error, 
        selected_date=selected_date, 
        offset=offset,
        h_years=h_years, h_months=h_months, h_days=h_days,
        g_years=g_years
    )

if __name__ == '__main__':
    app.run(debug=True)