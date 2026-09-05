"""
Query OpenStreetMap's Overpass API for electrical substations in the
South West (Cornwall, Devon, Somerset), as an independent cross-check
against the NESO TEC register candidate list.

OpenInfraMap (the site you found) is just a visual layer on top of this
same OpenStreetMap data — this script talks to the actual underlying
API (Overpass) directly, rather than the map website itself, which
doesn't expose a public API of its own.

Note: OSM data is crowd-sourced, so names/completeness may not perfectly
match official NESO/DNO naming — treat this as a third reference point
to cross-check, not ground truth.

Usage:
    uv run python find_sw_substations_osm.py
"""

import requests
import csv

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Rough bounding box covering Cornwall, Devon, and Somerset
# (south, west, north, east) — deliberately a bit generous; better to
# over-capture and manually trim than miss real substations at the edges.
BBOX = (49.9, -5.8, 51.3, -2.2)

QUERY = f"""
[out:json][timeout:60];
(
  node["power"="substation"]{BBOX};
  way["power"="substation"]{BBOX};
  relation["power"="substation"]{BBOX};
);
out center tags;
"""

OUTPUT_PATH = "data/sw_substations_osm.csv"


def main():
    print("Querying Overpass API (this can take 10-30 seconds)...")
    headers = {"User-Agent": "elec_mvp-sw-substation-lookup/0.1 (personal side project)"}
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

        # nodes have lat/lon directly; ways/relations have a "center" instead
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")

        rows.append({
            "name": name,
            "voltage": voltage,
            "operator": operator,
            "lat": lat,
            "lon": lon,
        })

    # Sort so named substations are easiest to skim first
    rows.sort(key=lambda r: (r["name"] == "(unnamed)", r["name"]))

    for r in rows:
        print(f"  - {r['name']}  |  {r['voltage']}  |  operator: {r['operator']}")

    import os
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "voltage", "operator", "lat", "lon"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nAlso saved to {OUTPUT_PATH} for easier cross-referencing.")


if __name__ == "__main__":
    main()