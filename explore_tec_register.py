"""
Step 1: Explore the NESO TEC register dataset.

This script lists every historical snapshot of the TEC register available
on the NESO Data Portal, then downloads the OLDEST and NEWEST ones so we
can compare them.

Run this first and share the printed output (especially the column names
at the bottom) before we write the diff logic — we don't want to guess
the schema.
"""

import requests
import pandas as pd
import os

# NESO's data portal uses a CKAN-style API. We try a couple of likely
# dataset IDs since the exact slug isn't confirmed yet.
CANDIDATE_IDS = ["tec_register", "transmission-entry-capacity-tec-register", "tec-register"]

API_BASE = "https://api.neso.energy/api/3/action/package_show"


def find_dataset():
    for dataset_id in CANDIDATE_IDS:
        try:
            resp = requests.get(API_BASE, params={"id": dataset_id}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    print(f"✅ Found dataset using id: '{dataset_id}'")
                    return data["result"]
        except requests.RequestException as e:
            print(f"Failed trying '{dataset_id}': {e}")
    raise RuntimeError(
        "Could not find the TEC register dataset with the candidate IDs. "
        "Go to https://www.neso.energy/data-portal/transmission-entry-capacity-tec-register/tec_register "
        "in your browser, view page source or network tab, and find the real dataset id, "
        "then add it to CANDIDATE_IDS above."
    )


def main():
    dataset = find_dataset()
    resources = dataset.get("resources", [])

    if not resources:
        print("No resources found in this dataset.")
        return

    print(f"\nFound {len(resources)} historical files:\n")
    for r in resources:
        print(f"  - {r.get('name')}  |  created: {r.get('created')}  |  url: {r.get('url')}")

    # Sort by creation date so we can grab oldest + newest
    resources_sorted = sorted(resources, key=lambda r: r.get("created", ""))
    oldest = resources_sorted[0]
    newest = resources_sorted[-1]

    os.makedirs("data", exist_ok=True)

    for label, resource in [("oldest", oldest), ("newest", newest)]:
        url = resource["url"]
        filename = f"data/tec_{label}.csv"
        print(f"\nDownloading {label} snapshot from {url} ...")
        r = requests.get(url, timeout=30)
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"Saved to {filename}")

    # Peek at the structure of the newest file
    print("\n--- Columns in newest snapshot ---")
    df = pd.read_csv("data/tec_newest.csv")
    print(df.columns.tolist())
    print("\n--- First 3 rows ---")
    print(df.head(3).to_string())
    print(f"\nTotal rows: {len(df)}")


if __name__ == "__main__":
    main()