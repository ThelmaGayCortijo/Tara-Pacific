from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

def load_stations():
    json_path = os.path.join('data', 'stations.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'stations' in data:
                return data['stations']
            return data
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stations')
def get_stations():
    stations = load_stations()
    return jsonify(stations)

@app.route('/analyser', methods=['POST'])
def analyser():
    parametre = request.form.get('parametre', 'merged_chl')
    stations = load_stations()
    labels = []
    valeurs = []
    for s in stations[:15]:
        labels.append(s.get('station', 'Station'))
        val = s.get(parametre)
        valeurs.append(val if val is not None else 0)
    
    titre = "Chlorophyll Concentration (mg/m³)" if parametre == 'merged_chl' else "Surface Water Temp (°C)"
    return jsonify({"labels": labels, "valeurs": valeurs, "titre": titre})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    payload = request.get_json(silent=True) or {}
    parameter = payload.get('parameter', 'merged_chl')
    region = payload.get('region', 'all')
    limit = int(payload.get('limit', 20))

    stations = load_stations()
    filtered = []
    for s in stations:
        lat = s.get('lat')
        lon = s.get('lon')
        if lat is None or lon is None:
            continue
        lat, lon = float(lat), float(lon)
        if region == 'south_pacific' and lat >= 0:
            continue
        if region == 'north_pacific' and not (lat >= 0 and (lon < -100 or lon > 120)):
            continue
        if region == 'atlantic_panama' and not (lon >= -90 and lon <= 0 and lat >= 0):
            continue
        filtered.append(s)

    subset = (filtered if filtered else stations)[:limit]
    labels = [str(s.get('station', 'Station'))[:18] for s in subset]
    values = [float(s.get(parameter) or 0) for s in subset]

    meta_map = {
        "mergedSST": {"label": "Sea Surface Temperature (°C)", "unit": "°C", "color": "#e05a47"},
        "merged_chl": {"label": "Chlorophyll-a Concentration (mg/m³)", "unit": "mg/m³", "color": "#16a085"},
        "mergedSSS": {"label": "Sea Surface Salinity (PSU)", "unit": "PSU", "color": "#008891"},
        "airTemp": {"label": "Marine Air Temperature (°C)", "unit": "°C", "color": "#f39c12"}
    }
    meta = meta_map.get(parameter, meta_map["merged_chl"])

    avg_val = round(sum(values) / len(values), 2) if values else 0
    min_val = round(min(values), 2) if values else 0
    max_val = round(max(values), 2) if values else 0

    return jsonify({
        "labels": labels,
        "values": values,
        "label": meta["label"],
        "unit": meta["unit"],
        "color": meta["color"],
        "summary": {
            "average": avg_val,
            "min": min_val,
            "max": max_val,
            "sample_size": len(subset)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)