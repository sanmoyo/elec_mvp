"""
Find candidate South West (B13 boundary) substations in the TEC register.

There's no public, structured "which substations sit behind B13" dataset
(see project notes / README) — so this script uses a geographic proxy:
place names associated with Cornwall, Devon, and Somerset (west of
Bridgwater/Hinkley Point, where the B13 boundary's binding constraint
sits). This is an approximation, not a verified topological mapping —
flag matches for manual review rather than trusting them blindly.

"""

import csv

DATA_PATH = "data/tec_register.csv"

# Keywords associated with the South West peninsula (Cornwall, Devon,
# Somerset). Deliberately broad — better to over-match and manually
# review than miss real candidates. Extend this list as you learn more
# from the actual B13 boundary diagram.
SW_KEYWORDS = [
    "cornwall", "devon", "somerset",
    "cornish", "devonshire",
    "truro", "camborne", "redruth", "penzance", "newquay", "bodmin",
    "st austell", "indian queens", "landulph", "launceston",
    "plymouth", "devonport", "exeter", "exmouth", "torbay", "torquay",
    "newton abbot", "barnstaple", "tiverton", "honiton", "axminster",
    "willand", "langage", "alverdiscott",
    "taunton", "bridgwater", "wellington", "yeovil", "wells",
    "minehead", "hinkley", "hinckley", "shurton", "chard", "glastonbury",
]


def load_connection_sites():
    with open(DATA_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def is_candidate(connection_site):
    site_lower = connection_site.lower()
    return any(keyword in site_lower for keyword in SW_KEYWORDS)


def main():
    rows = load_connection_sites()

    # Unique connection sites, so we're not looking at 2000+ duplicate rows
    unique_sites = sorted(set(row["Connection Site"] for row in rows if row.get("Connection Site")))

    candidates = [site for site in unique_sites if is_candidate(site)]
    non_candidates = [site for site in unique_sites if not is_candidate(site)]

    print(f"Total unique connection sites in register: {len(unique_sites)}")
    print(f"\n=== {len(candidates)} candidate South West sites (review these) ===")
    for site in candidates:
        print(f"  - {site}")

    print(f"\n=== {len(non_candidates)} sites NOT matched (skim for anything missed) ===")
    for site in non_candidates:
        print(f"  - {site}")

    print(
        "\nNext step: cross-check the candidate list above against the actual "
        "B13 boundary diagram (view in browser — see README/project notes for link) "
        "and manually confirm/remove entries before treating this as your B13 lookup."
    )


if __name__ == "__main__":
    main()