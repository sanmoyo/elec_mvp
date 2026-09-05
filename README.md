# TEC Register Watch

NESO's grid connection queue (the TEC register) updates twice a week, but there's no way to see what actually changed between updates, just a snapshot that gets silently overwritten. So I built something to track it, and then used it to answer a real question: how oversubscribed is the queue in the South West, actually?

## How it works

A scheduled job fetches the register daily and commits it to this repo whenever it changes, so the commit history becomes the change log. A second script diffs each new snapshot against the last one and picks out anything that actually matters (a project progressing a gate, a status change, a capacity change), ignoring noise like formatting differences.

## Latest changes

<!-- LATEST_REPORT_START -->
*No report yet — check back after NESO's next update (Tuesdays/Fridays).*
<!-- LATEST_REPORT_END -->

## What I found for the South West (B13)

NESO caps this boundary at 2.9 GW. There's no public list of which substations count toward it, so I built one, cross-checking the register's naming against OpenStreetMap data, then joined it back to live queue data.

Turns out:
- **1.14 GW (39%) is already built** — that's real usage against the limit.
- That leaves **~1.76 GW of actual headroom**.
- The pipeline still trying to connect wants **~27.7 GW** — about **16x** what's left.
- None of it has reached a firm connection offer yet (Gate 2). It's all still speculative.

(A naive queued-vs-limit calculation says 995%, but that double-counts what's already built. Headroom is the number that actually means something.)

## Data sources

- [NESO TEC Register](https://www.neso.energy/data-portal/transmission-entry-capacity-tec-register/tec_register)
- [NESO ETYS — South Wales & South England boundaries](https://www.neso.energy/publications/electricity-ten-year-statement-etys/electricity-transmission-network-requirements/south-wales-and-south-england-boundaries)
- OpenStreetMap (via Overpass API), for cross-checking substation names

## Status

Early-stage side project. Built fast, not polished. Next: try the same substation-mapping approach on another constrained boundary.

---

Built by Michael Southall (with Claude of course)
