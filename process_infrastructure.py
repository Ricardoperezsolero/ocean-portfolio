#!/usr/bin/env python3
"""
GFW Fixed Infrastructure CSV → infrastructure.geojson
======================================================
Source dataset : public-fixed-infrastructure:v1.1 (SAR variant)
Dataset URL    : https://globalfishingwatch.org/data-download/datasets/public-fixed-infrastructure:v1.1
License        : CC BY-NC 4.0 — Global Fishing Watch
Used in        : https://ocean.ricardoperezsolero.com/

OUTPUT FILTERS APPLIED
----------------------
  - One detection per structure_id (latest date — structures are static)
  - Labels kept  : oil, wind  (noise / unknown / lake_maracaibo discarded)
  - Confidence   : high only  (removes ~35% of structures, keeps verified detections)
  - Regions      : three bounding boxes matching the portfolio's career geography:
      · Europe / Mediterranean  lon(-15, 42)  lat(25, 65)
      · Southeast Asia           lon(90, 145)  lat(-15, 25)
      · South America / Chile    lon(-85, -60) lat(-60, -15)

RESULT
------
  Input  : ~5M rows, ~800MB CSV (one monthly file)
  Output : ~14,600 unique structures, ~2.3MB GeoJSON

HOW TO REGENERATE
-----------------
  1. Download any monthly CSV from the dataset URL above (free GFW account required).
     One month is enough — structures don't move.
  2. Run:
       python3 process_infrastructure.py <filename>.csv
  3. Replace infrastructure.geojson and redeploy.

EXPECTED CSV COLUMNS
--------------------
  detection_id, detection_date, structure_id, lon, lat,
  structure_start_date, structure_end_date, label, label_confidence
"""

import csv
import json
import sys
import os
from collections import Counter

# ── filters ──────────────────────────────────────────────────────────────────
KEEP_LABELS      = {'oil', 'wind'}
KEEP_CONFIDENCE  = {'high'}
SKIP_LABELS      = {'lake_maracaibo', 'unknown', 'noise'}

REGIONS = [
    {'name': 'Europe / Mediterranean', 'lon': (-15, 42),  'lat': (25, 65)},
    {'name': 'Southeast Asia',          'lon': (90, 145),  'lat': (-15, 25)},
    {'name': 'South America / Chile',   'lon': (-85, -60), 'lat': (-60, -15)},
]

def in_region(lon, lat):
    return any(
        r['lon'][0] <= lon <= r['lon'][1] and r['lat'][0] <= lat <= r['lat'][1]
        for r in REGIONS
    )

# ── helpers ───────────────────────────────────────────────────────────────────
def find_csv():
    candidates = sorted(
        [f for f in os.listdir('.') if f.endswith('.csv')],
        key=os.path.getmtime, reverse=True
    )
    infra = [f for f in candidates if 'infra' in f.lower() or 'fixed' in f.lower()]
    return infra[0] if infra else (candidates[0] if candidates else None)


def main():
    csv_path = sys.argv[1] if len(sys.argv) >= 2 else find_csv()
    if not csv_path:
        print('Usage: python3 process_infrastructure.py <file>.csv')
        sys.exit(1)
    if not os.path.exists(csv_path):
        print(f'Error: {csv_path} not found')
        sys.exit(1)

    print(f'Reading {csv_path}  ({os.path.getsize(csv_path)/1024/1024:.0f} MB) …')

    # ── deduplicate: keep latest detection per structure_id ───────────────────
    structures = {}
    total = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if total % 500_000 == 0:
                print(f'  {total/1_000_000:.1f}M rows — {len(structures):,} unique structures …', end='\r')

            label      = (row.get('label') or '').strip()
            confidence = (row.get('label_confidence') or '').strip()

            if label not in KEEP_LABELS:
                continue
            if confidence not in KEEP_CONFIDENCE:
                continue

            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
            except (ValueError, TypeError):
                continue

            if not in_region(lon, lat):
                continue

            sid  = (row.get('structure_id') or row.get('det_id') or row.get('id') or str(total)).strip()
            date = (row.get('detection_date') or row.get('composite_date') or '').strip()

            if sid not in structures or date > structures[sid]['date']:
                structures[sid] = {'lat': lat, 'lon': lon, 'label': label,
                                   'date': date, 'confidence': confidence}

    print(f'\nTotal rows read  : {total:,}')
    print(f'Unique structures: {len(structures):,}')

    # ── build GeoJSON ─────────────────────────────────────────────────────────
    features, skipped = [], 0

    for sid, s in structures.items():
        if not (-90 <= s['lat'] <= 90 and -180 <= s['lon'] <= 180):
            skipped += 1
            continue
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [round(s['lon'], 5), round(s['lat'], 5)]},
            'properties': {'id': sid, 'label': s['label'],
                           'date': s['date'], 'confidence': s['confidence']}
        })

    print(f'Features output  : {len(features):,}  (skipped {skipped} invalid coords)')

    # ── breakdown ─────────────────────────────────────────────────────────────
    print('\nBy region:')
    for r in REGIONS:
        count  = sum(1 for f in features
                     if r['lon'][0] <= f['geometry']['coordinates'][0] <= r['lon'][1]
                     and r['lat'][0] <= f['geometry']['coordinates'][1] <= r['lat'][1])
        labels = Counter(f['properties']['label'] for f in features
                         if r['lon'][0] <= f['geometry']['coordinates'][0] <= r['lon'][1]
                         and r['lat'][0] <= f['geometry']['coordinates'][1] <= r['lat'][1])
        print(f'  {r["name"]:<30} {count:>6,}  {dict(labels)}')

    # ── write ─────────────────────────────────────────────────────────────────
    out = 'infrastructure.geojson'
    with open(out, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': features}, f, separators=(',', ':'))

    size_mb = os.path.getsize(out) / 1024 / 1024
    print(f'\nSaved → {out}  ({size_mb:.1f} MB, {len(features):,} points)')


if __name__ == '__main__':
    main()
