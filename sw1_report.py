"""
SW1 (South Wales) boundary capacity report.

Filters the TEC register down to projects connecting at substations
confirmed to sit behind the SW1 boundary (see find_wales_substations.py,
find_wales_substations_osm.py, and compare_wales_sources.py for how this
list was derived and manually verified).

Source for the 3.8 GW limit: NESO Electricity Ten Year Statement (ETYS),
South Wales and South England boundaries — the binding constraint is a
thermal limit on the Cowley-Walham 400kV circuit. Note: Cowley itself is
excluded from the substation list below — verified via search to be near
Oxford, England, nowhere near Wales, despite naming the boundary circuit.
Walham (Gloucestershire) is kept, confirmed as the actual asset linking
South Wales generation to English demand.

Also excluded: "Mid Wales" / "North Wales" connection node entries that
matched via keyword search but belong to a different ETYS boundary
entirely (confirmed via cross-referencing during manual review).

Usage:
    uv run python sw1_report.py
"""

import csv

DATA_PATH = "data/tec_register.csv"
OUTPUT_PATH = "data/sw1_queue.csv"

SW1_SUBSTATIONS = {
    "Cilfynydd 400kV Substation",
    "Future Swansea North 132kV",
    "Imperial Park 400kV Substation",
    "Imperial Park B 400kV Substation",
    "Llandyfaelog 132kV Substation",
    "Llandyfaelog 400/132kV Substation",
    "Llanteg 400kV Substation",
    "Margam 275kV Substation",
    "Margam B 400kV Substation",
    "Pembroke 132kV Substation",
    "Pembroke 400kV Substation",
    "Rassau 400kV Substation",
    "Rassau GSP",
    "Rhigos 400kV Substation",
    "Rhigos B 400kV Substation",
    "SOUTH WALES WEST CONNECTION NODE A 132KV SUBSTATION",
    "South Wales East Connection Node A 275kV Substation",
    "South Wales East Connection Node B 400kV",
    "South Wales East Node A 275kV Substation",
    "South Wales West Connection Node A 400kV Substation",
    "South Wales West Connection Node B 400kV Substation",
    "South Wales West Connection Node C 400kV",
    "Swansea North 132kV Substation",
    "Swansea North 400kV Substation",
    "Upper Boat 275kV Substation",
    "Upperboat 132kV Substation",
    "Uskmouth 132kV Substation",
    "Uskmouth 275kV Substation",
    "Walham 400kV Substation",
    "Whitson 275kV Substation",
}

SW1_LIMIT_MW = 3800  # 3.8 GW, per ETYS


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
    totals = {}
    for r in rows:
        key = r.get(field) or "(blank)"
        totals[key] = totals.get(key, 0.0) + to_float(r.get("Cumulative Total Capacity (MW)"))
    return totals


def print_breakdown(totals):
    for key, mw in sorted(totals.items(), key=lambda kv: -kv[1]):
        pct = (mw / SW1_LIMIT_MW * 100) if SW1_LIMIT_MW else 0
        print(f"  - {key}: {mw:,.1f} MW ({pct:.0f}% of SW1 limit)")


def main():
    rows = load_register()
    sw1_rows = [r for r in rows if r.get("Connection Site") in SW1_SUBSTATIONS]

    print(f"Total rows in register: {len(rows)}")
    print(f"Rows at confirmed SW1 substations: {len(sw1_rows)}\n")

    total_mw = sum(to_float(r.get("Cumulative Total Capacity (MW)")) for r in sw1_rows)

    print("=== Projects queued behind SW1 ===")
    for r in sorted(sw1_rows, key=lambda r: -to_float(r.get("Cumulative Total Capacity (MW)"))):
        print(
            f"  - {r.get('Project Name', '?')} ({r.get('Customer Name', '?')}) "
            f"@ {r.get('Connection Site', '?')} — "
            f"{r.get('Cumulative Total Capacity (MW)', '?')} MW, "
            f"Stage: {r.get('Stage', '?')}, Gate: {r.get('Gate', '?')}, "
            f"Status: {r.get('Project Status', '?')}"
        )

    status_totals = compute_breakdown(sw1_rows, "Project Status")
    built_mw = status_totals.get("Built", 0.0)
    remaining_headroom_mw = SW1_LIMIT_MW - built_mw
    pipeline_mw = total_mw - built_mw
    oversubscription_ratio = (
        pipeline_mw / remaining_headroom_mw if remaining_headroom_mw > 0 else float("inf")
    )

    print(f"\n=== Summary ===")
    print(f"SW1 boundary limit (ETYS): {SW1_LIMIT_MW:,.0f} MW")
    print(f"Already built and connected: {built_mw:,.1f} MW ({built_mw / SW1_LIMIT_MW * 100:.0f}% of limit)")
    print(f"Remaining headroom: {remaining_headroom_mw:,.1f} MW")
    print(f"Pipeline requesting that headroom (everything not yet built): {pipeline_mw:,.1f} MW")
    print(f"-> Pipeline is ~{oversubscription_ratio:.1f}x the capacity actually still available")
    print(
        f"\n(For reference, gross queued capacity as a naive % of the total boundary limit "
        f"would be {total_mw / SW1_LIMIT_MW * 100:.0f}% - but that figure double-counts capacity "
        f"already used by built projects, so the headroom comparison above is more meaningful.)"
    )

    print(f"\n=== Breakdown by Gate ===")
    print_breakdown(compute_breakdown(sw1_rows, "Gate"))

    print(f"\n=== Breakdown by Project Status ===")
    print_breakdown(status_totals)

    gate2_plus_mw = sum(
        to_float(r.get("Cumulative Total Capacity (MW)"))
        for r in sw1_rows
        if to_float(r.get("Gate"), default=-1) >= 2
    )
    gate2_pct = (gate2_plus_mw / SW1_LIMIT_MW * 100) if SW1_LIMIT_MW else 0
    print(
        f"\nOf the total, Gate 2+ (more committed) capacity: "
        f"{gate2_plus_mw:,.1f} MW ({gate2_pct:.0f}% of SW1 limit)"
    )

    # Save a dated snapshot for tracking over time, same pattern as B13
    import os
    from datetime import date
    os.makedirs("sw1_reports", exist_ok=True)
    report_path = f"sw1_reports/{date.today().isoformat()}.md"
    with open(report_path, "w") as f:
        f.write(f"# SW1 headroom report — {date.today().isoformat()}\n\n")
        f.write(f"- SW1 boundary limit: {SW1_LIMIT_MW:,.0f} MW\n")
        f.write(f"- Already built: {built_mw:,.1f} MW ({built_mw / SW1_LIMIT_MW * 100:.0f}%)\n")
        f.write(f"- Remaining headroom: {remaining_headroom_mw:,.1f} MW\n")
        f.write(f"- Pipeline requesting headroom: {pipeline_mw:,.1f} MW\n")
        f.write(f"- Oversubscription ratio: ~{oversubscription_ratio:.1f}x\n")
    print(f"\n(Dated snapshot saved to {report_path})")

    if sw1_rows:
        fieldnames = list(sw1_rows[0].keys())
        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sw1_rows)
        print(f"\n(Full filtered project list saved to {OUTPUT_PATH})")


if __name__ == "__main__":
    main()