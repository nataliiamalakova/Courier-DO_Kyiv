# Courier DO · Kyiv & Zaporizhia

Interactive dashboard showing courier **DO** (delivered orders) distribution per day and per week across multiple cities.

**Live dashboard:** https://nataliiamalakova.github.io/Courier-DO_Kyiv/

## Coverage

| City | Period | Days | Weeks |
|---|---|---|---|
| **Kyiv** | 10 - 31 May 2026 | 21 | 3 |
| **Zaporizhia** | 6 Apr - 31 May 2026 | 56 | 8 |

(Active courier = courier with online hours > 0 that day. AR is intentionally not part of this dashboard.)

## Features

- **City tabs at top** — switch between Kyiv and Zaporizhia
- **Weekly comparison** (per city)
  - Click any week card to add/remove from the comparison
  - Quick filters: `All weeks`, `Last 3`, `Last 2`, `Clear`
  - Two synced charts: weekly DO totals (one bar per week) + per-courier DO bucket distribution side-by-side
- **Daily multi-select compare**
  - Click any KPI card or day tab to toggle a day
  - Quick filters: `All days`, `Week N only`, `Compare Mon/Tue/Wed/Thu/Fri/Sat/Sun` — picks all occurrences of that weekday across the city's full window (e.g. all 8 Tuesdays in Zaporizhia)
- **Stacked share** — every day on one bar chart, weekday + date label, normalized to 100%

## Buckets

**DO per courier (daily):** `0`, `1-5`, `6-10`, `11-17`, `18-20`, `21-25`, `26+`

**DO total per courier per week (weekly summary):** `0`, `1-20`, `21-30`, `31-40`, `41-50`, `51-60`, `60+`

## Files

- `index.html` — the dashboard (Chart.js, no build step)
- `report_data.json` — multi-city merged data
- `build_cities.py` — current pipeline that produces `report_data.json` from the Looker CSVs

The earlier per-week scripts (`build_from_csv.py`, `merge_data.py`, `add_week.py`) are kept for history; the current source of truth is `build_cities.py`.

## Refresh / add another city or week

1. Drop the new Looker CSV in `~/Downloads`
2. Edit `build_cities.py` to point at the right path / city filter
3. Run:
   ```bash
   python3 build_cities.py
   ```
4. Re-embed `report_data.json` into the `<script id="report-data">` block of `index.html`
5. `git commit -am "Refresh data" && git push`
