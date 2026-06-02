"""Merge old (18-24) and new (25-31) report_data into a single 14-day file
with weekday labels and per-week summaries.
"""
import json
from datetime import datetime
from pathlib import Path

OLD = Path("/Users/nataliia.malakovabolt.eu/Downloads/Session with Jakub H./report_data.json")
NEW = Path(__file__).parent / "report_data.json"
OUT = Path(__file__).parent / "report_data.json"

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def weekday(date_str: str) -> str:
    return WEEKDAYS[datetime.strptime(date_str, "%Y-%m-%d").weekday()]


def main():
    old = json.loads(OLD.read_text())
    new = json.loads(NEW.read_text())

    dates = sorted(set(old["dates"]) | set(new["dates"]))

    daily_totals = {**old["daily_totals"], **new["daily_totals"]}
    do_daily = {**old["do_daily"], **new["do_daily"]}
    ar_daily = {**old["ar_daily"], **new["ar_daily"]}

    weekday_map = {d: weekday(d) for d in dates}

    weeks = [
        {
            "id": "w1",
            "label": "Week 1 · 18-24 May",
            "dates": old["dates"],
            "do_summary": old["do_summary"],
            "ar_summary": old["ar_summary"],
        },
        {
            "id": "w2",
            "label": "Week 2 · 25-31 May",
            "dates": new["dates"],
            "do_summary": new["do_summary"],
            "ar_summary": new["ar_summary"],
        },
    ]

    data = {
        "city": "Kyiv",
        "city_id": 158,
        "date_range": {"start": dates[0], "end": dates[-1]},
        "dates": dates,
        "weekday_map": weekday_map,
        "weeks": weeks,
        "daily_totals": daily_totals,
        "do_buckets": new["do_buckets"],
        "ar_buckets": new["ar_buckets"],
        "do_summary_buckets": new["do_summary_buckets"],
        "do_daily": do_daily,
        "ar_daily": ar_daily,
    }

    OUT.write_text(json.dumps(data, indent=2, default=str))
    print(f"Saved {OUT}, {len(dates)} days")
    for d in dates:
        t = daily_totals[d]
        ar = t["total_accepted"] / t["total_proposed"] * 100 if t["total_proposed"] else 0
        print(
            f"  {weekday_map[d]} {d}: active={t['active_couriers']:>4}  "
            f"DO={t['total_delivered']:>5.0f}  AR={ar:5.1f}%"
        )


if __name__ == "__main__":
    main()
