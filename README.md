# Courier DO_Kyiv

Interactive dashboard showing courier **DO** (delivered orders) and **AR%** (acceptance rate) distribution in Kyiv.

**Live dashboard:** https://nataliiamalakova.github.io/Courier-DO_Kyiv/

Currently covers **3 weeks · 21 days** · 10 - 31 May 2026:

- **Week 1** · 10-16 May (Sun-Sat)
- **Week 2** · 18-24 May (Mon-Sun)
- **Week 3** · 25-31 May (Mon-Sun)

Note: 17 May is missing because the source export starts on 18 May for that week.

## Features

- **Weekday + date** labels on every chart, table and selector
- **Multi-select day comparison** — click any KPI card / day tab to toggle. Multiple selected days are rendered as grouped bars + a wide comparison table
- **Quick filters**:
  - `All days`, `Week 1 only`, `Week 2 only`, `Week 3 only`
  - `Compare Mon`, `Compare Tue`, … `Compare Sun` — pick all occurrences of that weekday across all weeks (e.g. 3 Tuesdays at once)
  - `Clear`
- **Per-week summaries** — DO total + AR% over the week per courier, one card per week
- **All days stacked share** — every day on one bar chart, weekday labels included

## Files

- `index.html` — the dashboard (Chart.js, no build step)
- `report_data.json` — merged 21-day data
- `build_from_csv.py` — converts a Looker `Courier Performance` CSV into a 7-day JSON
- `merge_data.py` — initial merge of the previous-week DB-derived JSON with a CSV-derived week
- `add_week.py` — appends another week (from a Looker CSV) to the existing `report_data.json`

## Buckets

**DO per courier (daily):** `0`, `1-5`, `6-10`, `11-17`, `18-20`, `21-25`, `26+`

**AR% per courier (daily):** `0%`, `1-20%`, `21-40%`, `41-60%`, `61-80%`, `81-99%`, `100%`

**DO 7-day summary:** `0`, `1-20`, `21-30`, `31-40`, `41-50`, `51-60`, `60+`

## Definitions

- **Active courier** = courier with `online hours > 0` for that day
- **DO** = `Courier Delivered Orders Count, #`
- **AR%** = `Courier Acceptance Rate, %` (only for couriers who received at least one offer)
- **Weekly AR%** = `sum(accepted) / sum(proposed)` per courier across the week

## Refresh / add another week

```bash
python3 add_week.py "/path/to/Courier Performance _ Report Time (N).csv"
```

Then re-embed `report_data.json` into the `<script id="report-data">` block of `index.html` and `git push`.
