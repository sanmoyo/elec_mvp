"""
Find candidate South Wales (SW1 boundary) substations in the TEC register.

Deliberately independent of find_sw_substations.py (that script covers
"SW" = South West / B13; this one covers South Wales / SW1 - different
boundary, different region, kept separate to avoid naming confusion).

Same approach as the South West version: no public "which substations
sit behind SW1" dataset exists, so this uses a geographic proxy (Welsh
place names) as a starting candidate list, then cross-checks against
OSM before treating it as final.

SW1's binding constraint is a thermal limit on the Cowley-Walham 400kV
circuit - Cowley and Walham are technically on the English side of the
boundary crossing point, but are included here since they define the
boundary itself (same logic as including Hinkley Point/Shurton in the
B13 list).

Usage:
    uv run python find_wales_substations.py
"""

import csv

DATA_PATH = "data/tec_register.csv"

WALES_KEYWORDS = [
    "wales", "welsh", "glamorgan", "gwent", "dyfed", "powys",
    "cardiff", "swansea", "newport", "pembroke", "pembrokeshire",
    "carmarthen", "neath", "port talbot", "bridgend", "llanelli",
    "merthyr", "caerphilly", "barry", "aberdare", "pontypridd",
    "llandyfaelog", "llanteg", "rassau", "margam", "cilfynydd",
    "upper boat", "upperboat", "uskmouth", "rhigos", "whitson",
    "imperial park", "south wales",
    # The boundary's named binding constraint circuit (technically just
    # over the English side, but defines the SW1 boundary itself):
    "cowley", "walham",
]


def load_connection_sites():
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def is_candidate(connection_site):
    site_lower = connection_site.lower()
    return any(keyword in site_lower for keyword in WALES_KEYWORDS)


def main():
    rows = load_connection_sites()
    unique_sites = sorted(set(row["Connection Site"] for row in rows if row.get("Connection Site")))

    candidates = [site for site in unique_sites if is_candidate(site)]
    non_candidates = [site for site in unique_sites if not is_candidate(site)]

    print(f"Total unique connection sites in register: {len(unique_sites)}")
    print(f"\n=== {len(candidates)} candidate South Wales (SW1) sites (review these) ===")
    for site in candidates:
        print(f"  - {site}")

    print(f"\n=== {len(non_candidates)} sites NOT matched (skim for anything missed) ===")
    for site in non_candidates:
        print(f"  - {site}")

    print(
        "\nNext step: cross-check the candidate list above against the actual "
        "SW1 boundary diagram (view in browser) and against an OSM cross-check "
        "(see find_wales_substations_osm.py) before treating this as final."
    )


if __name__ == "__main__":
    main()