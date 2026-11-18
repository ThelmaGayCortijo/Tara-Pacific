import json
import math
import os
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Stations de secours pour la carte interactive (non surchargée)
FALLBACK_STATIONS = [
    {
        "station": "TARA_001 (Lorient Departure)",
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
        "station": "TARA_012 (Miami Coral Reefs)",
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
        "station": "TARA_018 (Panama Canal)",
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
        "station": "TARA_034 (Las Perlas, Panama)",
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
        "station": "TARA_052 (Easter Island / Rapa Nui)",
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
        "station": "TARA_068 (Moorea, French Polynesia)",
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
        "station": "TARA_085 (Samoa Archipelago)",
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
        "station": "TARA_102 (Fiji Islands)",
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
        "station": "TARA_124 (Great Barrier Reef)",
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
        "station": "TARA_145 (Okinawa, Japan)",
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
        "station": "TARA_168 (Papua New Guinea)",
        "dt": "2017-09-10",
        "lat": -5.21,
        "lon": 145.81,
        "mergedSST": 29.7,
        "mergedSSS": 34.1,
        "merged_chl": 0.74,
        "no3": 3.40,
        "o2": 193.0,
    },
    {
        "station": "TARA_192 (Palau Coral Sanctuary)",
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
        "station": "TARA_215 (Hawaii Archipelago)",
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


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/api/stations")
def api_stations():
  """Retourne les stations échantillonnées pour la carte interactive (max 45 pour ne pas surcharger)."""
  stations = load_stations()
  if len(stations) > 45:
    step = max(1, len(stations) // 45)
    sampled = stations[::step]
  else:
    sampled = stations
  return jsonify(
      {"count": len(sampled), "total_raw": len(stations), "stations": sampled}
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port, debug=False)