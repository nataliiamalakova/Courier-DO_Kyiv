"""Build a multi-city report file (Kyiv + Zaporizhia) focused on DO only.

Reads:
- Existing report_data.json — to inherit Kyiv daily breakdown for 18-31 May
  (those days originally came from a DB query; we keep the per-day buckets as-is)
- Kyiv CSV (10-16 May) — for Kyiv week 1
- Zaporizhia CSV (06.04 - 31.05) — full 8 weeks

Outputs report_data.json with structure:
{
  "cities": [
    {
      "name": "Kyiv",
      "dates": [...],
      "weekday_map": {date: weekday},
      "weeks": [{id, label, dates, do_summary, total_do, total_active_courier_days}],
      "daily_totals": {date: {active_couriers, total_delivered}},
      "do_daily": {date: {bucket: count}}
    },
    {"name": "Zaporizhia", ...}
  ],
  "do_buckets": [...],
  "do_summary_buckets": [...]
}
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DO_BUCKET_ORDER = ["0", "1-5", "6-10", "11-17", "18-20", "21-25", "26+"]
DO_SUMMARY_BUCKET_ORDER = ["0", "1-20", "21-30", "31-40", "41-50", "51-60", "60+"]

ZAP_CSV = Path("/Users/nataliia.malakovabolt.eu/Downloads/Courier Performance _ Report Time (1).csv")
OUT = Path(__file__).parent / "report_data.json"

# Inherit Kyiv 21-day data from the previous merged backup
EXISTING_REPORT = Path(__file__).parent / "report_data.backup.json"


def weekday(date_str: str) -> str:
    return WEEKDAYS[datetime.strptime(date_str, "%Y-%m-%d").weekday()]


def do_bucket(v: float) -> str:
    v = int(round(v))
    if v == 0: return "0"
    if v <= 5: return "1-5"
    if v <= 10: return "6-10"
    if v <= 17: return "11-17"
    if v <= 20: return "18-20"
    if v <= 25: return "21-25"
    return "26+"


def do_summary_bucket(v: float) -> str:
    v = int(round(v))
    if v == 0: return "0"
    if v <= 20: return "1-20"
    if v <= 30: return "21-30"
    if v <= 40: return "31-40"
    if v <= 50: return "41-50"
    if v <= 60: return "51-60"
    return "60+"


def fmt_range(dates):
    a = datetime.strptime(dates[0], "%Y-%m-%d")
    b = datetime.strptime(dates[-1], "%Y-%m-%d")
    if a.month == b.month:
        return f"{a.strftime('%-d')}-{b.strftime('%-d %b')}"
    return f"{a.strftime('%-d %b')} - {b.strftime('%-d %b')}"


def load_csv(path: Path, city_filter: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, low_memory=False)
    df = df[df["City Name"].str.contains(city_filter, case=False, na=False)].copy()
    df["date"] = df["Report Time (dynamic)"].astype(str)
    df["online_hours"] = pd.to_numeric(df["Courier Total Online Hours, :"], errors="coerce").fillna(0)
    df["delivered"] = pd.to_numeric(df["Courier Delivered Orders Count, #"], errors="coerce").fillna(0)
    return df[df["online_hours"] > 0].copy()


def daily_from_csv(df: pd.DataFrame):
    """Returns (daily_totals, do_daily, per_day_courier_orders) for date-bucketed compute."""
    daily_totals, do_daily = {}, {}
    for d, sub in df.groupby("date"):
        daily_totals[d] = {
            "active_couriers": int(sub["Courier ID"].nunique()),
            "total_delivered": float(sub["delivered"].sum()),
        }
        b = {x: 0 for x in DO_BUCKET_ORDER}
        for v in sub["delivered"]:
            b[do_bucket(v)] += 1
        do_daily[d] = b
    return daily_totals, do_daily


def split_into_weeks(dates):
    """Split sorted dates into Mon-Sun weeks (or Sun-Sat if needed)."""
    weeks = []
    current = []
    for d in dates:
        if not current:
            current = [d]
            continue
        prev = datetime.strptime(current[-1], "%Y-%m-%d")
        cur = datetime.strptime(d, "%Y-%m-%d")
        if cur == prev + timedelta(days=1) and len(current) < 7 and weekday(d) != "Mon":
            current.append(d)
        else:
            # Start a new week if non-consecutive OR new Monday
            if weekday(d) == "Mon":
                weeks.append(current)
                current = [d]
            elif cur != prev + timedelta(days=1):
                weeks.append(current)
                current = [d]
            else:
                current.append(d)
    if current:
        weeks.append(current)
    return weeks


def per_courier_do_summary(df: pd.DataFrame, week_dates):
    sub = df[df["date"].isin(week_dates)]
    per_courier = sub.groupby("Courier ID")["delivered"].sum()
    counts = {x: 0 for x in DO_SUMMARY_BUCKET_ORDER}
    for v in per_courier:
        counts[do_summary_bucket(v)] += 1
    return counts, int(per_courier.shape[0]), float(per_courier.sum())


def build_city(name: str, df: pd.DataFrame):
    daily_totals, do_daily = daily_from_csv(df)
    dates = sorted(daily_totals.keys())
    week_groups = split_into_weeks(dates)

    weeks = []
    for i, wd in enumerate(week_groups, 1):
        do_summary, n_couriers, total_do = per_courier_do_summary(df, wd)
        weeks.append({
            "id": f"{name.lower()}-w{i}",
            "label": f"Week {i} · {fmt_range(wd)}",
            "dates": wd,
            "do_summary": do_summary,
            "n_couriers": n_couriers,
            "total_do": total_do,
            "total_active_couriers": sum(daily_totals[d]["active_couriers"] for d in wd),
        })

    return {
        "name": name,
        "dates": dates,
        "weekday_map": {d: weekday(d) for d in dates},
        "weeks": weeks,
        "daily_totals": daily_totals,
        "do_daily": do_daily,
    }


def build_kyiv():
    """Kyiv: inherit the previously-merged 21-day data (10-31 May)."""
    existing = json.loads(EXISTING_REPORT.read_text())
    dates = sorted(existing["dates"])

    daily_totals = {
        d: {
            "active_couriers": existing["daily_totals"][d]["active_couriers"],
            "total_delivered": existing["daily_totals"][d]["total_delivered"],
        }
        for d in dates
    }
    do_daily = {d: existing["do_daily"][d] for d in dates}

    weeks = []
    for i, w in enumerate(existing.get("weeks", []), 1):
        wd = w["dates"]
        do_summary = w["do_summary"]
        n_couriers = sum(do_summary.values())
        total_do = sum(daily_totals[d]["total_delivered"] for d in wd)
        weeks.append({
            "id": f"kyiv-w{i}",
            "label": f"Week {i} · {fmt_range(wd)}",
            "dates": wd,
            "do_summary": do_summary,
            "n_couriers": n_couriers,
            "total_do": total_do,
            "total_active_couriers": sum(daily_totals[d]["active_couriers"] for d in wd),
        })

    return {
        "name": "Kyiv",
        "dates": dates,
        "weekday_map": {d: weekday(d) for d in dates},
        "weeks": weeks,
        "daily_totals": daily_totals,
        "do_daily": do_daily,
    }


def main():
    kyiv = build_kyiv()
    zap_df = load_csv(ZAP_CSV, "Zapor")
    zap = build_city("Zaporizhia", zap_df)

    out = {
        "do_buckets": DO_BUCKET_ORDER,
        "do_summary_buckets": DO_SUMMARY_BUCKET_ORDER,
        "cities": [kyiv, zap],
    }
    OUT.write_text(json.dumps(out, indent=2, default=str))

    print(f"Saved {OUT}")
    for city in out["cities"]:
        print(f"\n=== {city['name']} · {len(city['dates'])} days, {len(city['weeks'])} weeks ===")
        for w in city["weeks"]:
            print(
                f"  {w['label']:<32s}  total_DO={w['total_do']:>6.0f}  "
                f"unique_couriers={w['n_couriers']:>4}  active_courier_days={w['total_active_couriers']:>5}"
            )


if __name__ == "__main__":
    main()
