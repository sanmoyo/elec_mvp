"""
B13 (South West England) boundary capacity report.

Filters the TEC register down to projects connecting at substations
confirmed to sit behind the B13 boundary (see project notes for how this
list was derived: cross-checked NESO register naming against OSM data),
sums their queued capacity, and compares it against B13's published
transfer capability limit.

Source for the 2.9 GW limit: NESO Electricity Ten Year Statement (ETYS),
South Wales and South England boundaries — the binding constraint is a
voltage limit triggered by a fault on the Hinkley Point-Shurton 400kV
double circuit.

Usage:
    uv run python b13_report.py
"""

import csv

DATA_PATH = "data/tec_register.csv"
OUTPUT_PATH = "data/b13_queue.csv"

# Confirmed via cross-referencing NESO TEC register naming against OSM
# substation data (Devonside excluded - false positive, actually in
# Clackmannanshire, Scotland, not Devon).
B13_SUBSTATIONS = {
    "Alverdiscott 400kV Substation",
    "Axminster 132kV Substation",
    "Axminster 400kV Substation",
    "Bridgwater 400/132kV Substation",
    "Bridgwater GSP",
    "Exeter 132kV Substation",
    "Exeter 400kV Substation",
    "Exeter GSP",
    "Exeter Main 400kV Substation",
    "Hinkley Point 400kV Substation",
    "Indian Queens 400kV Substation",
    "Landulph 400kV Substation",
    "Landulph GSP",
    "Langage 400kV Substation",
    "Shurton 400kV Substation",
    "Taunton 400kV Substation",
    "Taunton GSP",
}

B13_LIMIT_MW = 2900  # 2.9 GW, per ETYS


def load_register():
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def to_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def main():
    rows = load_register()
    b13_rows = [r for r in rows if r.get("Connection Site") in B13_SUBSTATIONS]

    print(f"Total rows in register: {len(rows)}")
    print(f"Rows at confirmed B13 substations: {len(b13_rows)}\n")

    total_mw = sum(to_float(r.get("Cumulative Total Capacity (MW)")) for r in b13_rows)

    print("=== Projects queued behind B13 ===")
    for r in sorted(b13_rows, key=lambda r: -to_float(r.get("Cumulative Total Capacity (MW)"))):
        print(
            f"  - {r.get('Project Name', '?')} ({r.get('Customer Name', '?')}) "
            f"@ {r.get('Connection Site', '?')} — "
            f"{r.get('Cumulative Total Capacity (MW)', '?')} MW, "
            f"Stage: {r.get('Stage', '?')}, Gate: {r.get('Gate', '?')}, "
            f"Status: {r.get('Project Status', '?')}"
        )

    pct_of_limit = (total_mw / B13_LIMIT_MW * 100) if B13_LIMIT_MW else 0

    print(f"\n=== Summary ===")
    print(f"Total queued capacity behind B13: {total_mw:,.1f} MW")
    print(f"B13 boundary limit (ETYS): {B13_LIMIT_MW:,.0f} MW")
    print(f"Queued capacity as % of boundary limit: {pct_of_limit:.0f}%")
    print(
        "\nNote: this is a naive sum of everything in the queue at these "
        "substations, regardless of stage/status - it doesn't net off "
        "withdrawn projects or account for projects already built and "
        "energised. Useful as a first read, not a precise headroom figure."
    )

    # Save the filtered project list for reference / further analysis
    if b13_rows:
        fieldnames = list(b13_rows[0].keys())
        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(b13_rows)
        print(f"\n(Full filtered project list saved to {OUTPUT_PATH})")


if __name__ == "__main__":
    main()