"""
Summarise meaningful changes in the TEC register between two snapshots.

"Meaningful" = a change in one of the WATCHED_COLUMNS below (stage/status/
gate/capacity progressing), rather than noise like a date field shifting.

Usage:
    Compare two specific files:
        uv run python summarise_changes.py data/tec_oldest.csv data/tec_newest.csv

    Compare the current committed snapshot against the PREVIOUS git commit
    (this is what you'll use day-to-day once real updates start rolling in):
        uv run python summarise_changes.py --git

Each run also saves a dated report to changes/YYYY-MM-DD.md, so over time
you build up a readable timeline of the grid queue changing — the actual
point of this whole project.
"""

import sys
import io
import subprocess
from datetime import date

from csv_diff import load_csv, compare

KEY_COLUMN = "Project ID"

# Only these columns count as a "meaningful" change for now. Everything
# else (e.g. minor date shifts) is treated as noise and hidden by default.
WATCHED_COLUMNS = {
    "Stage",
    "Project Status",
    "Gate",
    "MW Increase / Decrease",
    "Cumulative Total Capacity (MW)",
}

DATA_PATH = "data/tec_register.csv"

def is_real_change(old_val, new_val):
    """Ignore differences that are just numeric formatting (e.g. '0.00' vs '0')."""
    try:
        return float(old_val) != float(new_val)
    except (ValueError, TypeError):
        return old_val != new_val  # not numeric, compare as plain text




def get_git_previous_version(path):
    """Return the file's contents as they were in the previous commit."""
    result = subprocess.run(
        ["git", "show", f"HEAD~1:{path}"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def load(source):
    """source is either a file path (str) or raw CSV text content."""
    if isinstance(source, str) and "\n" not in source:
        with open(source, newline="") as f:
            return load_csv(f, key=KEY_COLUMN)
    else:
        return load_csv(io.StringIO(source), key=KEY_COLUMN)


def build_report(diff, new_lookup):
    lines = ["# TEC Register changes", ""]

    added = diff["added"]
    removed = diff["removed"]
    changed = diff["changed"]

    if added:
        lines.append(f"## {len(added)} new project(s)")
        for row in added:
            lines.append(
                f"- **{row.get('Project Name', '?')}** "
                f"({row.get('Customer Name', '?')}) — "
                f"{row.get('Cumulative Total Capacity (MW)', '?')} MW, "
                f"Stage: {row.get('Stage', '?')}, Gate: {row.get('Gate', '?')}"
            )
        lines.append("")

    if removed:
        lines.append(f"## {len(removed)} project(s) dropped")
        for row in removed:
            lines.append(
                f"- **{row.get('Project Name', '?')}** "
                f"({row.get('Customer Name', '?')})"
            )
        lines.append("")

    meaningful = []
    for entry in changed:
        watched = {
            col: vals for col, vals in entry["changes"].items()
            if col in WATCHED_COLUMNS
        }
        if watched:
            meaningful.append((entry["key"], watched))

    if meaningful:
        lines.append(f"## {len(meaningful)} project(s) with meaningful changes")
        for key, watched in meaningful:
            name = new_lookup.get(key, {}).get("Project Name", key)
            lines.append(f"- **{name}**")
            for col, vals in watched.items():
                lines.append(f"    - {col}: {vals[0]} → {vals[1]}")
        lines.append("")

    noise_count = len(changed) - len(meaningful)
    if noise_count:
        lines.append(
            f"_(plus {noise_count} project(s) with only minor/date changes, hidden)_"
        )
        lines.append("")

    if not added and not removed and not meaningful:
        lines.append("No meaningful changes detected.")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--git":
        old_content = get_git_previous_version(DATA_PATH)
        old = load(old_content)
        new = load(DATA_PATH)
    elif len(sys.argv) == 3:
        old = load(sys.argv[1])
        new = load(sys.argv[2])
    else:
        print("Usage:")
        print("  uv run python summarise_changes.py <old_csv> <new_csv>")
        print("  uv run python summarise_changes.py --git")
        sys.exit(1)

    diff = compare(old, new)
    report = build_report(diff, new)

    print(report)

    import os
    os.makedirs("changes", exist_ok=True)
    out_path = f"changes/{date.today().isoformat()}.md"
    with open(out_path, "w") as f:
        f.write(report)
    print(f"\n(Report also saved to {out_path})")


if __name__ == "__main__":
    main()