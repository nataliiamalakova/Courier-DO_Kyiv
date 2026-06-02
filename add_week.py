"""Append a new week (from a Looker CSV) to the existing merged report_data.json.

Re-uses the bucketing logic from build_from_csv.py.

Usage:
    python3 add_week.py /path/to/Courier\ Performance.csv
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from build_from_csv import (
    AR_BUCKET_ORDER,
    DO_BUCKET_ORDER,
    DO_SUMMARY_BUCKET_ORDER,
    ar_bucket,
    do_bucket,
    do_summary_bucket,
    empty_bucket_dict,
)

REPORT_PATH = Path(__file__).parent / "report_data.json"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def weekday(date_str: str) -> str:
    return WEEKDAYS[datetime.strptime(date_str, "%Y-%m-%d").weekday()]


def process_csv(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path, index_col=0, low_memory=False)
    df = df[df["City Name"] == "Kyiv"].copy()

    df["date"] = df["Report Time (dynamic)"].astype(str)
    df["online_hours"] = pd.to_numeric(df["Courier Total Online Hours, :"], errors="coerce").fillna(0)
    df["delivered"] = pd.to_numeric(df["Courier Delivered Orders Count, #"], errors="coerce").fillna(0)
    df["proposed"] = pd.to_numeric(df["Courier Proposed Orders Count, #"], errors="coerce").fillna(0)
    df["ar_pct"] = (
        df["Courier Acceptance Rate, %"]
        .astype(str)
        .str.rstrip("%")
        .replace({"nan": None, "": None})
        .astype(float)
    )

    active = df[df["online_hours"] > 0].copy()
    dates = sorted(active["date"].unique())

    daily_totals, do_daily, ar_daily = {}, {}, {}
    for d in dates:
        sub = active[active["date"] == d]
        daily_totals[d] = {
            "active_couriers": int(sub["Courier ID"].nunique()),
            "couriers_with_offers": int(sub[sub["proposed"] > 0]["Courier ID"].nunique()),
            "total_delivered": float(sub["delivered"].sum()),
            "total_accepted": float((sub["ar_pct"].fillna(0) / 100 * sub["proposed"]).sum()),
            "total_proposed": float(sub["proposed"].sum()),
        }

        do_b = empty_bucket_dict(DO_BUCKET_ORDER)
        for v in sub["delivered"]:
            do_b[do_bucket(v)] += 1
        do_daily[d] = do_b

        ar_b = empty_bucket_dict(AR_BUCKET_ORDER)
        sub_o = sub[(sub["proposed"] > 0) & (sub["ar_pct"].notna())]
        for v in sub_o["ar_pct"]:
            ar_b[ar_bucket(v)] += 1
        ar_daily[d] = ar_b

    per_courier = active.groupby("Courier ID").agg(
        total_delivered=("delivered", "sum"),
        total_proposed=("proposed", "sum"),
    )
    accepted_calc = active.groupby("Courier ID").apply(
        lambda g: ((g["ar_pct"].fillna(0) / 100.0) * g["proposed"]).sum()
    )
    per_courier["total_accepted"] = accepted_calc
    per_courier["ar_pct_period"] = (
        per_courier["total_accepted"]
        / per_courier["total_proposed"].where(per_courier["total_proposed"] > 0)
        * 100.0
    )

    do_summary = empty_bucket_dict(DO_SUMMARY_BUCKET_ORDER)
    for v in per_courier["total_delivered"]:
        do_summary[do_summary_bucket(v)] += 1
    ar_summary = empty_bucket_dict(AR_BUCKET_ORDER)
    for v in per_courier["ar_pct_period"].dropna():
        ar_summary[ar_bucket(v)] += 1

    return {
        "dates": dates,
        "daily_totals": daily_totals,
        "do_daily": do_daily,
        "ar_daily": ar_daily,
        "do_summary": do_summary,
        "ar_summary": ar_summary,
    }


def fmt_range(dates):
    a = datetime.strptime(dates[0], "%Y-%m-%d").strftime("%-d")
    b = datetime.strptime(dates[-1], "%Y-%m-%d").strftime("%-d %b")
    return f"{a}-{b}"


def main():
    csv = Path(sys.argv[1])
    new = process_csv(csv)
    existing = json.loads(REPORT_PATH.read_text())

    new_dates = set(new["dates"])
    existing_weeks_dates = set()
    for w in existing["weeks"]:
        existing_weeks_dates.update(w["dates"])

    if new_dates & existing_weeks_dates:
        overlap = sorted(new_dates & existing_weeks_dates)
        raise SystemExit(f"Refusing to add — overlapping dates: {overlap}")

    existing["dates"] = sorted(set(existing["dates"]) | new_dates)
    existing["daily_totals"].update(new["daily_totals"])
    existing["do_daily"].update(new["do_daily"])
    existing["ar_daily"].update(new["ar_daily"])
    existing["weekday_map"] = {d: weekday(d) for d in existing["dates"]}
    existing["date_range"] = {"start": existing["dates"][0], "end": existing["dates"][-1]}

    week_entry = {
        "id": f"w-{new['dates'][0]}",
        "label": f"Week · {fmt_range(new['dates'])}",
        "dates": new["dates"],
        "do_summary": new["do_summary"],
        "ar_summary": new["ar_summary"],
    }
    existing["weeks"].append(week_entry)
    existing["weeks"].sort(key=lambda w: w["dates"][0])

    REPORT_PATH.write_text(json.dumps(existing, indent=2, default=str))
    print(f"Added {len(new_dates)} days from {csv.name}")
    for d in new["dates"]:
        t = new["daily_totals"][d]
        ar = t["total_accepted"] / t["total_proposed"] * 100 if t["total_proposed"] else 0
        print(
            f"  {weekday(d)} {d}: active={t['active_couriers']:>4}  "
            f"DO={t['total_delivered']:>5.0f}  AR={ar:5.1f}%"
        )
    print(f"\nFinal weeks ({len(existing['weeks'])}):")
    for w in existing["weeks"]:
        print(f"  {w['label']}: {w['dates'][0]} → {w['dates'][-1]}")


if __name__ == "__main__":
    main()
