# Courier DO_Kyiv

Interactive dashboard showing courier **DO** (delivered orders) and **AR%** (acceptance rate) distribution in Kyiv across 14 days: **18 - 31 May 2026** (2 full weeks).

**Live dashboard:** https://nataliiamalakova.github.io/Courier-DO_Kyiv/

## Features

- **Weekday + date** labels everywhere
- **Multi-select day comparison** — click any day card / tab to toggle. Multiple selected days are rendered as grouped bars on the same chart, plus a wide comparison table
- **Quick filters**:
  - `All 14 days`, `Week 1 only`, `Week 2 only`
  - `Compare Mon`, `Compare Tue`, … `Compare Sun` — picks both occurrences of that weekday across the two weeks
  - `Clear`
- **Per-week summaries** — DO total + AR% over the full week per courier
- **All-14-days stacked share** — one bar per day, weekday label included

## Files

- `index.html` — the dashboard (Chart.js, no build step)
- `report_data.json` — merged 14-day data
- `build_from_csv.py` — converts the Looker `Courier Performance` CSV into a 7-day `report_data.json`
- `merge_data.py` — merges the previous-week data with the current-week CSV-derived data into the unified 14-day file

## Buckets

**DO per courier (daily):** `0`, `1-5`, `6-10`, `11-17`, `18-20`, `21-25`, `26+`

**AR% per courier (daily):** `0%`, `1-20%`, `21-40%`, `41-60%`, `61-80%`, `81-99%`, `100%`

**DO 7-day summary:** `0`, `1-20`, `21-30`, `31-40`, `41-50`, `51-60`, `60+`

## Definitions

- **Active courier** = courier with `online hours > 0` for that day
- **DO** = `Courier Delivered Orders Count, #`
- **AR%** = `Courier Acceptance Rate, %` (only for couriers who received at least one offer)
- **Weekly AR%** = `sum(accepted) / sum(proposed)` per courier across the week

## Refresh next week

1. Drop the new Looker CSV next to the script
2. Run:
   ```bash
   python3 build_from_csv.py "/path/to/Courier Performance _ Report Time.csv"
   python3 merge_data.py
   ```
3. Re-embed `report_data.json` between the `<script id="report-data">` markers in `index.html`
4. `git commit -am "Refresh data" && git push`
