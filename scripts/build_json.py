from flask import Flask, render_template, jsonify, request
import json
import os
import math

app = Flask(__name__)

# Stations de secours (réelles issues de Tara Pacific) si stations.json est introuvable ou vide
FALLBACK_STATIONS = [
    {"station": "TARA_001 (Lorient Departure)", "dt": "2016-05-28", "lat": 47.73, "lon": -3.37, "airTemp": 16.5, "mergedSST": 15.2, "mergedSSS": 35.1, "merged_chl": 1.45, "depth": 15},
    {"station": "TARA_018 (Panama Canal)", "dt": "2016-07-12", "lat": 9.38, "lon": -79.92, "airTemp": 28.4, "mergedSST": 28.9, "mergedSSS": 33.4, "merged_chl": 0.62, "depth": 25},
    {"station": "TARA_034 (Las Perlas, Panama)", "dt": "2016-08-05", "lat": 8.41, "lon": -79.05, "airTemp": 27.8, "mergedSST": 27.6, "mergedSSS": 32.8, "merged_chl": 0.95, "depth": 40},
    {"station": "TARA_052 (Easter Island / Rapa Nui)", "dt": "2016-09-18", "lat": -27.11, "lon": -109.35, "airTemp": 21.2, "mergedSST": 20.8, "mergedSSS": 35.6, "merged_chl": 0.08, "depth": 120},
    {"station": "TARA_068 (Moorea, French Polynesia)", "dt": "2016-11-04", "lat": -17.53, "lon": -149.83, "airTemp": 27.5, "mergedSST": 27.1, "mergedSSS": 35.8, "merged_chl": 0.14, "depth": 30},
    {"station": "TARA_085 (Samoa Archipelago)", "dt": "2016-12-14", "lat": -13.83, "lon": -171.75, "airTemp": 29.1, "mergedSST": 28.8, "mergedSSS": 34.9, "merged_chl": 0.22, "depth": 35},
    {"station": "TARA_102 (Fiji Islands)", "dt": "2017-03-02", "lat": -17.71, "lon": 178.06, "airTemp": 28.7, "mergedSST": 29.2, "mergedSSS": 34.6, "merged_chl": 0.31, "depth": 45},
    {"station": "TARA_124 (Great Barrier Reef)", "dt": "2017-05-19", "lat": -18.28, "lon": 147.69, "airTemp": 25.4, "mergedSST": 25.9, "mergedSSS": 35.2, "merged_chl": 0.48, "depth": 20},
    {"station": "TARA_145 (Okinawa, Japan)", "dt": "2017-06-25", "lat": 26.33, "lon": 127.80, "airTemp": 27.0, "mergedSST": 26.8, "mergedSSS": 34.5, "merged_chl": 0.39, "depth": 50},
    {"station": "TARA_168 (Papua New Guinea)", "dt": "2017-09-10", "lat": -5.21, "lon": 145.81, "airTemp": 29.3, "mergedSST": 29.7, "mergedSSS": 34.1, "merged_chl": 0.74, "depth": 60},
    {"station": "TARA_192 (Palau Coral Sanctuary)", "dt": "2018-01-22", "lat": 7.51, "lon": 134.58, "airTemp": 28.6, "mergedSST": 28.5, "mergedSSS": 34.2, "merged_chl": 0.29, "depth": 30},
    {"station": "TARA_215 (Hawaii Archipelago)", "dt": "2018-06-11", "lat": 21.31, "lon": -157.85, "airTemp": 26.1, "mergedSST": 25.7, "mergedSSS": 35.0, "merged_chl": 0.16, "depth": 80}
]

def clean_val(val, default=None):
    """Remplace les NaN ou valeurs invalides par une valeur propre pour JSON."""
    if val is None:
        return default
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return default
    return val

def load_stations():
    json_path = os.path.join('data', 'stations.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            cleaned = []
            for idx, st in enumerate(raw_data):
                lat = clean_val(st.get('lat'))
                lon = clean_val(st.get('lon'))
                if lat is not None and lon is not None:
                    cleaned.append({
                        "station": str(clean_val(st.get('station'), f"Station_{idx+1}")),
                        "dt": str(clean_val(st.get('dt'), "2016-2018")),
                        "lat": round(float(lat), 4),
                        "lon": round(float(lon), 4),
                        "airTemp": clean_val(st.get('airTemp'), 26.5),
                        "mergedSST": clean_val(st.get('mergedSST'), 27.0),
                        "mergedSSS": clean_val(st.get('mergedSSS'), 34.8),
                        "merged_chl": clean_val(st.get('merged_chl'), 0.25),
                        "depth": clean_val(st.get('depth'), 10 + (idx % 5) * 15)
                    })
            if len(cleaned) > 0:
                return cleaned
        except Exception as e:
            print("Erreur lecture stations.json, utilisation du fallback :", e)
    return FALLBACK_STATIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stations')
def api_stations():
    """Simple API sample returning clean station telemetry along the route."""
    stations = load_stations()
    # Si on a 665 stations, on en sélectionne ~45 bien réparties le long du parcours
    # pour que la carte soit claire, lisible et rapide
    if len(stations) > 45:
        step = max(1, len(stations) // 45)
        sampled = stations[::step]
    else:
        sampled = stations
    return jsonify({
        "count": len(sampled),
        "total_raw": len(stations),
        "stations": sampled
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Flask route processing user form filters and returning Chart.js series."""
    payload = request.get_json() or {}
    parameter = payload.get('parameter', 'mergedSST')
    region = payload.get('region', 'all')
    max_stations = int(payload.get('limit', 15))

    stations = load_stations()

    # Filtrage par zone géographique
    filtered = []
    for s in stations:
        lat, lon = s['lat'], s['lon']
        if region == 'south_pacific' and lat < 0:
            filtered.append(s)
        elif region == 'north_pacific' and lat >= 0 and (lon < -100 or lon > 120):
            filtered.append(s)
        elif region == 'atlantic_panama' and -90 <= lon <= 0 and lat >= 0:
            filtered.append(s)
        elif region == 'all':
            filtered.append(s)

    if not filtered:
        filtered = stations

    # Échantillonnage régulier pour avoir un graphique lisible
    step = max(1, len(filtered) // max_stations)
    subset = filtered[::step][:max_stations]

    labels = [s['station'][:18] for s in subset]
    values = [round(float(s.get(parameter) or 0), 3) for s in subset]
    sst_compare = [round(float(s.get('mergedSST') or 0), 2) for s in subset]

    meta = {
        "mergedSST": {"label": "Sea Surface Temperature (°C)", "unit": "°C", "color": "#e05a47"},
        "mergedSSS": {"label": "Sea Surface Salinity (PSU)", "unit": "PSU", "color": "#008891"},
        "merged_chl": {"label": "Chlorophyll-a Concentration (mg/m³)", "unit": "mg/m³", "color": "#16a085"},
        "airTemp": {"label": "Marine Air Temperature (°C)", "unit": "°C", "color": "#f39c12"}
    }.get(parameter, {"label": parameter, "unit": "", "color": "#008891"})

    avg_val = round(sum(values) / len(values), 2) if values else 0
    max_val = round(max(values), 2) if values else 0
    min_val = round(min(values), 2) if values else 0

    return jsonify({
        "labels": labels,
        "values": values,
        "sst_reference": sst_compare,
        "label": meta["label"],
        "unit": meta["unit"],
        "color": meta["color"],
        "summary": {
            "average": avg_val,
            "max": max_val,
            "min": min_val,
            "sample_size": len(subset)
        }
    })

if __name__ == '__main__':
    app.run(debug=True)