from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

def load_stations():
    json_path = os.path.join('data', 'stations.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
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

if __name__ == '__main__':
    app.run(debug=True)