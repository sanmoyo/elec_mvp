# TEC Register Watch

A small tool that treats NESO's Transmission Entry Capacity (TEC) register — the public queue of every project waiting for a grid connection in Great Britain — the way software teams treat code: as something with a version history worth actually reading.

## Why this exists

The grid effectively already has "commits." NESO's TEC register updates twice a week — projects join the queue, drop out, progress through connection gates, or have their capacity revised — but there's no readable history of *what changed and when*, only a snapshot that gets silently overwritten each time.

This project [git-scrapes](https://simonwillison.net/2020/Oct/9/git-scraping/) the register on a schedule, lets git's own commit history double as the change log, and filters the diff down to changes that actually matter (stage progression, status changes, capacity changes) rather than row-by-row noise.

## How it works

1. A scheduled GitHub Action fetches NESO's public TEC register CSV daily.
2. If the file has changed since the last fetch, git records a new commit — the register's version history, essentially for free.
3. A diff script compares the new snapshot against the previous commit, filters out noise, and writes a plain-language summary of what moved.

## Latest register changes

<!-- LATEST_REPORT_START -->
*No report yet — check back after NESO's next scheduled update (published Tuesdays and Fridays).*
<!-- LATEST_REPORT_END -->

*(This section updates automatically — no manual editing needed.)*

## Data source

[NESO Data Portal — TEC Register](https://www.neso.energy/data-portal/transmission-entry-capacity-tec-register/tec_register)

## Status

Early-stage side project exploring whether git-scraping — a technique data journalists use for tracking public data over time — is a useful lens for grid connection data. Built as a fast prototype rather than a finished product.

Possible next steps: extend the same pattern to other public registers (e.g. DNO-level embedded connections), and a lighter-weight view than raw markdown reports once there's enough history to make one worthwhile.

---

Built by Michael Southall