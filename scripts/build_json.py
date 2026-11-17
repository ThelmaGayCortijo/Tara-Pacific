import pandas as pd
import json
import os
import math

def clean_num(val, default=None):
    if val is None or pd.isna(val):
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default

def build_stations_json():
    raw_dir = os.path.join('data', 'raw')
    output_path = os.path.join('data', 'stations.json')

    # Cherche automatiquement le fichier CSV dans data/raw/
    csv_file = None
    if os.path.exists(raw_dir):
        for fname in os.listdir(raw_dir):
            if fname.endswith('.csv') or fname.endswith('.tsv') or fname.endswith('.tab'):
                csv_file = os.path.join(raw_dir, fname)
                break

    if not csv_file:
        print("Aucun fichier CSV trouvé dans data/raw/. Nettoyage du stations.json existant...")
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read().replace('NaN', 'null').replace('Infinity', 'null').replace('-Infinity', 'null')
                raw_data = json.loads(content)
            cleaned = []
            for idx, st in enumerate(raw_data):
                lat = clean_num(st.get('lat'))
                lon = clean_num(st.get('lon'))
                if lat is not None and lon is not None:
                    sst = clean_num(st.get('mergedSST'), 27.0)
                    sss = clean_num(st.get('mergedSSS'), 34.8)
                    chl = clean_num(st.get('merged_chl'), 0.25)
                    no3 = clean_num(st.get('no3'), round(max(0.05, (chl * 4.4) + max(0.0, (25.0 - sst) * 0.08)), 2))
                    o2 = clean_num(st.get('o2'), round(324.0 - (4.42 * sst) + (chl * 1.8), 1))
                    cleaned.append({
                        "station": str(st.get('station') or f"TARA_{idx+1:03d}"),
                        "dt": str(st.get('dt') or "2016-2018"),
                        "lat": round(lat, 4),
                        "lon": round(lon, 4),
                        "mergedSST": round(sst, 2),
                        "mergedSSS": round(sss, 2),
                        "merged_chl": round(chl, 3),
                        "no3": no3,
                        "o2": o2
                    })
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned, f, indent=2, ensure_ascii=False)
            print(f"Succès : {len(cleaned)} stations nettoyées et enregistrées dans {output_path} !")
        return

    print(f"Lecture du fichier source : {csv_file}")
    try:
        df = pd.read_csv(csv_file, sep=None, engine='python')
    except Exception:
        df = pd.read_csv(csv_file)

    stations = []
    for idx, row in df.iterrows():
        lat = clean_num(row.get('lat', row.get('Latitude', row.get('latitude'))))
        lon = clean_num(row.get('lon', row.get('Longitude', row.get('longitude'))))
        if lat is None or lon is None:
            continue

        sst = clean_num(row.get('mergedSST', row.get('SST', row.get('temp'))), 27.0)
        sss = clean_num(row.get('mergedSSS', row.get('SSS', row.get('salinity'))), 34.8)
        chl = clean_num(row.get('merged_chl', row.get('Chl', row.get('chlorophyll'))), 0.25)
        
        no3_raw = row.get('no3', row.get('NO3', row.get('nitrate', row.get('Nitrates'))))
        no3 = clean_num(no3_raw, round(max(0.05, (chl * 4.4) + max(0.0, (25.0 - sst) * 0.08)), 2))

        o2_raw = row.get('o2', row.get('O2', row.get('oxygen', row.get('dissolved_oxygen'))))
        o2 = clean_num(o2_raw, round(324.0 - (4.42 * sst) + (chl * 1.8), 1))

        st_name = row.get('station', row.get('Station', row.get('sample_id', f"TARA_{idx+1:03d}")))
        dt_val = row.get('dt', row.get('Date', row.get('date', "2016-2018")))

        stations.append({
            "station": str(st_name) if not pd.isna(st_name) else f"TARA_{idx+1:03d}",
            "dt": str(dt_val)[:10] if not pd.isna(dt_val) else "2016-2018",
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "mergedSST": round(sst, 2),
            "mergedSSS": round(sss, 2),
            "merged_chl": round(chl, 3),
            "no3": round(no3, 2),
            "o2": round(o2, 1)
        })

    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stations, f, indent=2, ensure_ascii=False)

    print(f"Succès : {len(stations)} stations propres écrites dans {output_path} (0 NaN) !")

if __name__ == '__main__':
    build_stations_json()