"""
Ongoing snapshot fetcher for the NESO TEC register.

Unlike the earlier explore script, this always saves to the SAME path
(data/tec_register.csv). That means each time this runs and the file has
changed, git creates a new commit — which becomes our "git log of the
grid queue." No custom versioning needed; git already does it.

Intended to be run on a schedule via GitHub Actions (see
.github/workflows/scrape.yml), but you can also run it manually anytime:
    uv run python fetch_tec_register.py
"""

import requests
import os

DATASET_ID = "transmission-entry-capacity-tec-register"
API_URL = "https://api.neso.energy/api/3/action/package_show"
OUTPUT_PATH = "data/tec_register.csv"


def main():
    resp = requests.get(API_URL, params={"id": DATASET_ID}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"NESO API call failed: {data}")

    resources = data["result"].get("resources", [])
    if not resources:
        raise RuntimeError("No resources found for this dataset.")

    # There's currently only one live resource (it gets overwritten on
    # each NESO update), so just grab the first one.
    csv_url = resources[0]["url"]
    print(f"Fetching: {csv_url}")

    csv_resp = requests.get(csv_url, timeout=30)
    csv_resp.raise_for_status()

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "wb") as f:
        f.write(csv_resp.content)

    print(f"Saved to {OUTPUT_PATH} ({len(csv_resp.content)} bytes)")


if __name__ == "__main__":
    main()