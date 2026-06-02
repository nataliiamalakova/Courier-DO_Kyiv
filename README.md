# Courier DO_Kyiv

Interactive dashboard showing courier **DO** (delivered orders) and **AR%** (acceptance rate) distribution in Kyiv, week of **25-31 May 2026**.

**Live dashboard:** https://nataliiamalakova.github.io/Courier-DO_Kyiv/

## What's inside

- `index.html` — the dashboard (Chart.js, no build step)
- `report_data.json` — the underlying data
- `build_from_csv.py` — script that converts the Looker CSV export into `report_data.json`

## Buckets

**DO per courier (daily):** `0`, `1-5`, `6-10`, `11-17`, `18-20`, `21-25`, `26+`

**AR% per courier (daily):** `0%`, `1-20%`, `21-40%`, `41-60%`, `61-80%`, `81-99%`, `100%`

**DO 7-day summary:** `0`, `1-20`, `21-30`, `31-40`, `41-50`, `51-60`, `60+`

## Definitions

- **Active courier** = courier with `online hours > 0` for that day
- **DO** = `Courier Delivered Orders Count, #`
- **AR%** = `Courier Acceptance Rate, %` (only computed for couriers who received at least one offer)
- **Period AR%** = `sum(accepted) / sum(proposed)` per courier across the 7 days

## Refresh

```bash
python3 build_from_csv.py "/path/to/Courier Performance _ Report Time.csv"
```

Then re-embed `report_data.json` inside the `<script id="report-data">` block of `index.html`.
