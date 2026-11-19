import json
import math
import os
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Stations de secours pour la carte interactive (non surchargée)
# 22 stations couvrant tout l'itinéraire depuis Lorient jusqu'à la fin du Pacifique
FALLBACK_STATIONS = [
    {
        "station": "Port of Lorient (Brittany, France)",
        "dt": "2016-05-28",
        "lat": 47.73,
        "lon": -3.37,
        "mergedSST": 15.2,
        "mergedSSS": 35.1,
        "merged_chl": 1.45,
        "no3": 6.8,
        "o2": 258.4,
    },
    {
        "station": "Azores Archipelago (North Atlantic)",
        "dt": "2016-06-08",
        "lat": 37.74,
        "lon": -25.67,
        "mergedSST": 19.8,
        "mergedSSS": 36.1,
        "merged_chl": 0.42,
        "no3": 1.8,
        "o2": 234.0,
    },
    {
        "station": "Miami & Florida Reef Tract (USA)",
        "dt": "2016-06-26",
        "lat": 25.76,
        "lon": -80.13,
        "mergedSST": 28.4,
        "mergedSSS": 35.9,
        "merged_chl": 0.38,
        "no3": 1.4,
        "o2": 199.5,
    },
    {
        "station": "Port of Colón & Panama Canal",
        "dt": "2016-07-12",
        "lat": 9.38,
        "lon": -79.92,
        "mergedSST": 28.9,
        "mergedSSS": 33.4,
        "merged_chl": 0.62,
        "no3": 2.9,
        "o2": 196.2,
    },
    {
        "station": "Las Perlas Archipelago (Panama)",
        "dt": "2016-08-05",
        "lat": 8.41,
        "lon": -79.05,
        "mergedSST": 27.6,
        "mergedSSS": 32.8,
        "merged_chl": 0.95,
        "no3": 4.5,
        "o2": 203.1,
    },
    {
        "station": "Equatorial East Pacific (Galápagos)",
        "dt": "2016-08-24",
        "lat": -0.95,
        "lon": -90.96,
        "mergedSST": 21.4,
        "mergedSSS": 34.8,
        "merged_chl": 0.82,
        "no3": 3.8,
        "o2": 228.5,
    },
    {
        "station": "Rapa Nui / Easter Island (Chile)",
        "dt": "2016-09-18",
        "lat": -27.11,
        "lon": -109.35,
        "mergedSST": 20.8,
        "mergedSSS": 35.6,
        "merged_chl": 0.08,
        "no3": 0.12,
        "o2": 231.5,
    },
    {
        "station": "Ducie & Pitcairn Islands",
        "dt": "2016-10-06",
        "lat": -24.67,
        "lon": -124.78,
        "mergedSST": 23.4,
        "mergedSSS": 35.7,
        "merged_chl": 0.09,
        "no3": 0.15,
        "o2": 219.8,
    },
    {
        "station": "Gambier Archipelago (French Polynesia)",
        "dt": "2016-10-20",
        "lat": -23.11,
        "lon": -134.97,
        "mergedSST": 24.8,
        "mergedSSS": 35.6,
        "merged_chl": 0.12,
        "no3": 0.21,
        "o2": 214.2,
    },
    {
        "station": "Moorea & Papeete Port (French Polynesia)",
        "dt": "2016-11-04",
        "lat": -17.53,
        "lon": -149.83,
        "mergedSST": 27.1,
        "mergedSSS": 35.8,
        "merged_chl": 0.14,
        "no3": 0.25,
        "o2": 205.8,
    },
    {
        "station": "Aitutaki & Cook Islands",
        "dt": "2016-11-22",
        "lat": -18.85,
        "lon": -159.78,
        "mergedSST": 27.5,
        "mergedSSS": 35.5,
        "merged_chl": 0.16,
        "no3": 0.32,
        "o2": 203.6,
    },
    {
        "station": "Niue Coral Atoll (South Pacific)",
        "dt": "2016-12-03",
        "lat": -19.05,
        "lon": -169.86,
        "mergedSST": 27.9,
        "mergedSSS": 35.3,
        "merged_chl": 0.18,
        "no3": 0.45,
        "o2": 201.2,
    },
    {
        "station": "Upolu Island & Apia Port (Samoa)",
        "dt": "2016-12-14",
        "lat": -13.83,
        "lon": -171.75,
        "mergedSST": 28.8,
        "mergedSSS": 34.9,
        "merged_chl": 0.22,
        "no3": 0.75,
        "o2": 197.4,
    },
    {
        "station": "Fiji Archipelago & Suva Port",
        "dt": "2017-03-02",
        "lat": -17.71,
        "lon": 178.06,
        "mergedSST": 29.2,
        "mergedSSS": 34.6,
        "merged_chl": 0.31,
        "no3": 1.15,
        "o2": 195.1,
    },
    {
        "station": "Port of Auckland (New Zealand)",
        "dt": "2017-04-02",
        "lat": -36.84,
        "lon": 174.76,
        "mergedSST": 19.4,
        "mergedSSS": 35.4,
        "merged_chl": 0.68,
        "no3": 3.10,
        "o2": 236.5,
    },
    {
        "station": "Nouméa & Chesterfield Reefs (New Caledonia)",
        "dt": "2017-04-28",
        "lat": -20.50,
        "lon": 162.00,
        "mergedSST": 26.2,
        "mergedSSS": 35.2,
        "merged_chl": 0.28,
        "no3": 0.95,
        "o2": 209.4,
    },
    {
        "station": "Great Barrier Reef (Coral Sea, Australia)",
        "dt": "2017-05-19",
        "lat": -18.28,
        "lon": 147.69,
        "mergedSST": 25.9,
        "mergedSSS": 35.2,
        "merged_chl": 0.48,
        "no3": 2.10,
        "o2": 211.0,
    },
    {
        "station": "Kimbe Bay (Papua New Guinea)",
        "dt": "2017-06-05",
        "lat": -5.21,
        "lon": 145.81,
        "mergedSST": 29.7,
        "mergedSSS": 34.1,
        "merged_chl": 0.74,
        "no3": 3.40,
        "o2": 193.0,
    },
    {
        "station": "Guam & Mariana Islands",
        "dt": "2017-06-15",
        "lat": 13.44,
        "lon": 144.79,
        "mergedSST": 28.9,
        "mergedSSS": 34.6,
        "merged_chl": 0.15,
        "no3": 0.30,
        "o2": 196.8,
    },
    {
        "station": "Okinawa & Ryukyu Archipelago (Japan)",
        "dt": "2017-06-25",
        "lat": 26.33,
        "lon": 127.80,
        "mergedSST": 26.8,
        "mergedSSS": 34.5,
        "merged_chl": 0.39,
        "no3": 1.65,
        "o2": 206.9,
    },
    {
        "station": "Palau Rock Islands Sanctuary",
        "dt": "2018-01-22",
        "lat": 7.51,
        "lon": 134.58,
        "mergedSST": 28.5,
        "mergedSSS": 34.2,
        "merged_chl": 0.29,
        "no3": 1.05,
        "o2": 198.8,
    },
    {
        "station": "Oahu & Kaneohe Bay (Hawaii, USA)",
        "dt": "2018-06-11",
        "lat": 21.31,
        "lon": -157.85,
        "mergedSST": 25.7,
        "mergedSSS": 35.0,
        "merged_chl": 0.16,
        "no3": 0.38,
        "o2": 212.3,
    },
]


def clean_val(val, default=None):
  if val is None:
    return default
  try:
    fval = float(val)
    if math.isnan(fval) or math.isinf(fval):
      return default
    return fval
  except (ValueError, TypeError):
    return default


def derive_no3(st, chl, sst, sss):
  for key in ("no3", "NO3", "nitrate", "nitrates", "merged_no3"):
    v = clean_val(st.get(key))
    if v is not None:
      return round(v, 2)
  est = max(0.05, (chl * 4.4) + max(0.0, (25.0 - sst) * 0.08))
  return round(est, 2)


def derive_o2(st, sst, chl):
  for key in ("o2", "O2", "oxygen", "dissolved_oxygen", "merged_o2"):
    v = clean_val(st.get(key))
    if v is not None:
      return round(v, 1)
  est = 324.0 - (4.42 * sst) + (chl * 1.8)
  return round(est, 1)


def load_stations():
  json_path = os.path.join("data", "stations.json")
  if os.path.exists(json_path):
    try:
      with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
      if isinstance(raw_data, dict) and "stations" in raw_data:
        raw_data = raw_data["stations"]
      cleaned = []
      for idx, st in enumerate(raw_data):
        lat = clean_val(st.get("lat"))
        lon = clean_val(st.get("lon"))
        if lat is not None and lon is not None:
          sst = clean_val(st.get("mergedSST"), 27.0)
          sss = clean_val(st.get("mergedSSS"), 34.8)
          chl = clean_val(st.get("merged_chl"), 0.25)
          no3 = derive_no3(st, chl, sst, sss)
          o2 = derive_o2(st, sst, chl)
          cleaned.append({
              "station": str(st.get("station") or f"Station_{idx+1}"),
              "dt": str(st.get("dt") or "2016-2018"),
              "lat": round(lat, 4),
              "lon": round(lon, 4),
              "mergedSST": round(sst, 2),
              "mergedSSS": round(sss, 2),
              "merged_chl": round(chl, 3),
              "no3": no3,
              "o2": o2,
          })
      if len(cleaned) > 0:
        return cleaned
    except Exception as e:
      print("Erreur lecture stations.json, utilisation du fallback :", e)
  return FALLBACK_STATIONS

# permet d'aller chercher fichier HTLM dans dossier templates dès que site utilisé
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stations")
def api_stations():
    """1. Route pour la CARTE : renvoie 22 stations bien espacées (avec Lorient au départ)."""
    stations = load_stations()
    if len(stations) > 22:
        step = max(1, len(stations) // 21)
        sampled = stations[::step][:21]
        # Ajoute toujours Lorient en premier point si le JSON ne commence pas en Bretagne
        if abs(sampled[0]["lat"] - 47.73) > 5:
            sampled.insert(0, FALLBACK_STATIONS[0])
    else:
        sampled = stations
    return jsonify(
        {"count": len(sampled), "total_raw": len(stations), "stations": sampled}
    )


@app.route("/api/all_stations")
def api_all_stations():
    """2. Route pour le GRAPHE : renvoie jusqu'à 150 vraies stations du fichier JSON."""
    stations = load_stations()
    if len(stations) > 150:
        step = max(1, len(stations) // 150)
        sampled = stations[::step]
    else:
        sampled = stations
    return jsonify({"count": len(sampled), "stations": sampled})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)