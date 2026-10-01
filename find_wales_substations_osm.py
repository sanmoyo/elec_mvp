"""
Query OpenStreetMap's Overpass API for electrical substations in South
Wales, as an independent cross-check against the NESO TEC register
candidate list (find_wales_substations.py).

Usage:
    uv run python find_wales_substations_osm.py
"""

import requests
import csv
import os

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Rough bounding box covering South Wales (Pembrokeshire in the west to
# Newport/Monmouthshire in the east) - (south, west, north, east).
BBOX = (51.3, -5.3, 51.9, -2.6)

QUERY = f"""
[out:json][timeout:60];
(
  node["power"="substation"]{BBOX};
  way["power"="substation"]{BBOX};
  relation["power"="substation"]{BBOX};
);
out center tags;
"""

OUTPUT_PATH = "data/wales_substations_osm.csv"


def main():
    print("Querying Overpass API (this can take 10-30 seconds)...")
    headers = {"User-Agent": "elec_mvp-wales-substation-lookup/0.1 (personal side project)"}
    resp = requests.post(OVERPASS_URL, data={"data": QUERY}, headers=headers, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    elements = data.get("elements", [])
    print(f"Found {len(elements)} tagged substations in the bounding box.\n")

    rows = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "(unnamed)")
        voltage = tags.get("voltage", "")
        operator = tags.get("operator", "")

        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")

        rows.append({
            "name": name,
            "voltage": voltage,
            "operator": operator,
            "lat": lat,
            "lon": lon,
        })

    rows.sort(key=lambda r: (r["name"] == "(unnamed)", r["name"]))

    for r in rows:
        print(f"  - {r['name']}  |  {r['voltage']}  |  operator: {r['operator']}")

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "voltage", "operator", "lat", "lon"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nAlso saved to {OUTPUT_PATH} for easier cross-referencing.")


if __name__ == "__main__":
    main()