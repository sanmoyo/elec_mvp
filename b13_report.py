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


def compute_breakdown(rows, field):
    """Group rows by `field`, return dict of key -> summed capacity (MW)."""
    totals = {}
    for r in rows:
        key = r.get(field) or "(blank)"
        totals[key] = totals.get(key, 0.0) + to_float(r.get("Cumulative Total Capacity (MW)"))
    return totals


def print_breakdown(totals):
    """Print a totals dict (from compute_breakdown), sorted by size."""
    for key, mw in sorted(totals.items(), key=lambda kv: -kv[1]):
        pct = (mw / B13_LIMIT_MW * 100) if B13_LIMIT_MW else 0
        print(f"  - {key}: {mw:,.1f} MW ({pct:.0f}% of B13 limit)")


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

    status_totals = compute_breakdown(b13_rows, "Project Status")
    built_mw = status_totals.get("Built", 0.0)
    remaining_headroom_mw = B13_LIMIT_MW - built_mw
    pipeline_mw = total_mw - built_mw
    oversubscription_ratio = (
        pipeline_mw / remaining_headroom_mw if remaining_headroom_mw > 0 else float("inf")
    )

    print(f"\n=== Summary ===")
    print(f"B13 boundary limit (ETYS): {B13_LIMIT_MW:,.0f} MW")
    print(f"Already built and connected: {built_mw:,.1f} MW ({built_mw / B13_LIMIT_MW * 100:.0f}% of limit)")
    print(f"Remaining headroom: {remaining_headroom_mw:,.1f} MW")
    print(f"Pipeline requesting that headroom (everything not yet built): {pipeline_mw:,.1f} MW")
    print(f"-> Pipeline is ~{oversubscription_ratio:.1f}x the capacity actually still available")
    print(
        f"\n(For reference, gross queued capacity as a naive % of the total boundary limit "
        f"would be {total_mw / B13_LIMIT_MW * 100:.0f}% - but that figure double-counts capacity "
        f"already used by built projects, so the headroom comparison above is more meaningful.)"
    )

    # Breakdown by Gate and Project Status: supporting detail behind the
    # headline figures above.
    print(f"\n=== Breakdown by Gate ===")
    print_breakdown(compute_breakdown(b13_rows, "Gate"))

    print(f"\n=== Breakdown by Project Status ===")
    print_breakdown(status_totals)

    gate2_plus_mw = sum(
        to_float(r.get("Cumulative Total Capacity (MW)"))
        for r in b13_rows
        if to_float(r.get("Gate"), default=-1) >= 2
    )
    gate2_pct = (gate2_plus_mw / B13_LIMIT_MW * 100) if B13_LIMIT_MW else 0
    print(
        f"\nOf the total, Gate 2+ (more committed) capacity: "
        f"{gate2_plus_mw:,.1f} MW ({gate2_pct:.0f}% of B13 limit)"
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