"""Build courier DO/AR distribution JSON from the Looker CSV export.

Input:  Courier Performance _ Report Time (1).csv
Output: report_data.json (consumed by index.html)
"""
import json
import sys
from pathlib import Path

import pandas as pd

CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/Users/nataliia.malakovabolt.eu/Downloads/Courier Performance _ Report Time (1).csv"
)
OUT_PATH = Path(__file__).parent / "report_data.json"

CITY = "Kyiv"

DO_BUCKET_ORDER = ["0", "1-5", "6-10", "11-17", "18-20", "21-25", "26+"]
AR_BUCKET_ORDER = ["0%", "1-20%", "21-40%", "41-60%", "61-80%", "81-99%", "100%"]
DO_SUMMARY_BUCKET_ORDER = ["0", "1-20", "21-30", "31-40", "41-50", "51-60", "60+"]


def do_bucket(v: float) -> str:
    v = int(round(v))
    if v == 0:
        return "0"
    if v <= 5:
        return "1-5"
    if v <= 10:
        return "6-10"
    if v <= 17:
        return "11-17"
    if v <= 20:
        return "18-20"
    if v <= 25:
        return "21-25"
    return "26+"


def ar_bucket(v: float) -> str:
    if v == 0:
        return "0%"
    if v <= 20:
        return "1-20%"
    if v <= 40:
        return "21-40%"
    if v <= 60:
        return "41-60%"
    if v <= 80:
        return "61-80%"
    if v < 100:
        return "81-99%"
    return "100%"


def do_summary_bucket(v: float) -> str:
    v = int(round(v))
    if v == 0:
        return "0"
    if v <= 20:
        return "1-20"
    if v <= 30:
        return "21-30"
    if v <= 40:
        return "31-40"
    if v <= 50:
        return "41-50"
    if v <= 60:
        return "51-60"
    return "60+"


def empty_bucket_dict(order):
    return {b: 0 for b in order}


def main():
    df = pd.read_csv(CSV_PATH, index_col=0, low_memory=False)
    df = df[df["City Name"] == CITY].copy()

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

    daily_totals = {}
    do_daily = {}
    ar_daily = {}

    for d in dates:
        sub = active[active["date"] == d]
        active_couriers = sub["Courier ID"].nunique()
        with_offers = sub[sub["proposed"] > 0]["Courier ID"].nunique()
        daily_totals[d] = {
            "active_couriers": int(active_couriers),
            "couriers_with_offers": int(with_offers),
            "total_delivered": float(sub["delivered"].sum()),
            "total_accepted": float((sub["ar_pct"].fillna(0) / 100.0 * sub["proposed"]).sum()),
            "total_proposed": float(sub["proposed"].sum()),
        }

        do_buckets = empty_bucket_dict(DO_BUCKET_ORDER)
        for v in sub["delivered"]:
            do_buckets[do_bucket(v)] += 1
        do_daily[d] = do_buckets

        ar_buckets = empty_bucket_dict(AR_BUCKET_ORDER)
        sub_with_offers = sub[(sub["proposed"] > 0) & (sub["ar_pct"].notna())]
        for v in sub_with_offers["ar_pct"]:
            ar_buckets[ar_bucket(v)] += 1
        ar_daily[d] = ar_buckets

    per_courier = active.groupby("Courier ID").agg(
        total_delivered=("delivered", "sum"),
        total_proposed=("proposed", "sum"),
        total_accepted=("delivered", "sum"),
    )
    accepted_calc = active.groupby("Courier ID").apply(
        lambda g: ((g["ar_pct"].fillna(0) / 100.0) * g["proposed"]).sum()
    )
    per_courier["total_accepted"] = accepted_calc
    per_courier["ar_pct_period"] = (
        per_courier["total_accepted"] / per_courier["total_proposed"].where(per_courier["total_proposed"] > 0) * 100.0
    )

    do_summary = empty_bucket_dict(DO_SUMMARY_BUCKET_ORDER)
    for v in per_courier["total_delivered"]:
        do_summary[do_summary_bucket(v)] += 1

    ar_summary = empty_bucket_dict(AR_BUCKET_ORDER)
    for v in per_courier["ar_pct_period"].dropna():
        ar_summary[ar_bucket(v)] += 1

    data = {
        "city": CITY,
        "city_id": 158,
        "date_range": {"start": dates[0], "end": dates[-1]},
        "dates": dates,
        "daily_totals": daily_totals,
        "do_buckets": DO_BUCKET_ORDER,
        "ar_buckets": AR_BUCKET_ORDER,
        "do_summary_buckets": DO_SUMMARY_BUCKET_ORDER,
        "do_daily": do_daily,
        "ar_daily": ar_daily,
        "do_summary": do_summary,
        "ar_summary": ar_summary,
    }

    OUT_PATH.write_text(json.dumps(data, indent=2, default=str))
    print(f"Saved {OUT_PATH}")
    print("Dates:", dates)
    print("Daily totals:")
    for d in dates:
        t = daily_totals[d]
        ar = t["total_accepted"] / t["total_proposed"] * 100 if t["total_proposed"] else 0
        print(
            f"  {d}: active={t['active_couriers']}  with_offers={t['couriers_with_offers']}  "
            f"DO={t['total_delivered']:.0f}  AR={ar:.1f}%"
        )


if __name__ == "__main__":
    main()
