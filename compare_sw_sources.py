"""
Cross-check the NESO TEC register candidate list against the OSM
(Overpass) substation list, using fuzzy name matching to handle the
fact that the same substation is named differently in each source
(e.g. "Exeter 400kV Substation" vs "Exeter").

Produces three groups:
  1. NESO candidates with a confident OSM match -> high confidence
  2. NESO candidates with NO OSM match -> worth a manual look
  3. OSM substations in the region that don't match any NESO candidate
     -> potential names your original keyword list missed entirely

Usage:
    uv run python compare_sw_sources.py
"""

import csv
import re
import difflib

from find_sw_substations import load_connection_sites, is_candidate

OSM_CSV_PATH = "data/sw_substations_osm.csv"
MATCH_CUTOFF = 0.6  # similarity threshold (0-1); tune if results look off

# Words/patterns that differ between sources but don't represent a real
# difference in *which substation* this is (voltage, generic suffixes).
NOISE_PATTERN = re.compile(
    r"\b(\d+(/\d+)*\s*kv|substation|gsp|grid supply point|switching station|"
    r"offshore|extension|connection node [a-z]|node [a-z]|main)\b",
    re.IGNORECASE,
)


def normalize(name):
    name = NOISE_PATTERN.sub("", name.lower())
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def load_neso_candidates():
    rows = load_connection_sites()
    unique_sites = sorted(set(r["Connection Site"] for r in rows if r.get("Connection Site")))
    return [s for s in unique_sites if is_candidate(s)]


def load_osm_names():
    with open(OSM_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row["name"] for row in reader if row["name"] and row["name"] != "(unnamed)"]


def main():
    neso_candidates = load_neso_candidates()
    osm_names = load_osm_names()

    neso_normalized = {name: normalize(name) for name in neso_candidates}
    osm_normalized = {name: normalize(name) for name in osm_names}
    osm_norm_list = list(osm_normalized.values())
    osm_norm_to_original = {}
    for original, norm in osm_normalized.items():
        osm_norm_to_original.setdefault(norm, []).append(original)

    matched_osm_norms = set()
    confident_matches = []
    no_match = []

    for neso_name, neso_norm in neso_normalized.items():
        best = difflib.get_close_matches(neso_norm, osm_norm_list, n=1, cutoff=MATCH_CUTOFF)
        if best:
            matched_osm_norms.add(best[0])
            osm_originals = osm_norm_to_original[best[0]]
            confident_matches.append((neso_name, osm_originals))
        else:
            no_match.append(neso_name)

    unmatched_osm = [
        original
        for norm, originals in osm_norm_to_original.items()
        if norm not in matched_osm_norms
        for original in originals
    ]

    print(f"=== {len(confident_matches)} confident matches (NESO <-> OSM) ===")
    for neso_name, osm_originals in confident_matches:
        print(f"  - {neso_name}")
        print(f"      matches OSM: {', '.join(osm_originals)}")

    print(f"\n=== {len(no_match)} NESO candidates with NO OSM match (check manually) ===")
    for name in no_match:
        print(f"  - {name}")

    print(f"\n=== {len(unmatched_osm)} OSM substations in the region NOT matched to any NESO candidate ===")
    print("(these might be real South West sites your keyword list missed)")
    for name in sorted(unmatched_osm):
        print(f"  - {name}")

    # Export everything to CSV for easier review than scrolling terminal output
    import os
    os.makedirs("data", exist_ok=True)
    out_path = "data/sw_comparison.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "name", "matched_with"])

        for neso_name, osm_originals in confident_matches:
            writer.writerow(["confident_match", neso_name, "; ".join(osm_originals)])

        for name in no_match:
            writer.writerow(["no_osm_match", name, ""])

        for name in sorted(unmatched_osm):
            writer.writerow(["unmatched_osm", name, ""])

    print(f"\n(Full results also saved to {out_path})")


if __name__ == "__main__":
    main()