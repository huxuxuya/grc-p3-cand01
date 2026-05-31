#!/usr/bin/env python3
"""Summarize devshard settlement event rows for the case epochs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_ndjson(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def read_epoch_ranges(raw_dir: Path, epochs: list[int]) -> dict[int, dict]:
    ranges = {}
    for epoch in epochs:
        payload = json.loads((raw_dir / f"epoch_{epoch}_group_data.json").read_text())
        group = payload["epoch_group_data"]
        ranges[epoch] = {
            "poc_start_block_height": int(group["poc_start_block_height"]),
            "effective_block_height": int(group["effective_block_height"]),
            "last_block_height": int(group["last_block_height"]),
        }
    return ranges


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/devshard_settlements.ndjson")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--out-dir", default="artifacts")
    parser.add_argument("--epochs", nargs="*", type=int, default=[269, 270, 271, 272])
    args = parser.parse_args()

    rows = read_ndjson(Path(args.input))
    ranges = read_epoch_ranges(Path(args.raw_dir), args.epochs)
    tagged_rows = []
    summary = []

    for row in rows:
        height = int(row["block_height"])
        matched_epoch = None
        for epoch, bounds in ranges.items():
            if bounds["poc_start_block_height"] <= height <= bounds["last_block_height"]:
                matched_epoch = epoch
                break
        tagged = dict(row)
        tagged["epoch"] = matched_epoch or ""
        tagged_rows.append(tagged)

    for epoch in args.epochs:
        epoch_rows = [row for row in tagged_rows if row["epoch"] == epoch]
        summary.append(
            {
                "epoch": epoch,
                "settlement_event_count": len(epoch_rows),
                "escrow_id_min": min((int(row["escrow_id"]) for row in epoch_rows), default=""),
                "escrow_id_max": max((int(row["escrow_id"]) for row in epoch_rows), default=""),
                "block_height_min": min((int(row["block_height"]) for row in epoch_rows), default=""),
                "block_height_max": max((int(row["block_height"]) for row in epoch_rows), default=""),
                "total_payout_sum": sum(int(row.get("total_payout") or 0) for row in epoch_rows),
                "remainder_sum": sum(int(row.get("remainder") or 0) for row in epoch_rows),
                "settlers": ",".join(sorted({row.get("settler", "") for row in epoch_rows})),
                "versions": ",".join(sorted({row.get("version", "") for row in epoch_rows})),
            }
        )

    fields = [
        "epoch",
        "escrow_id",
        "block_height",
        "block_time",
        "settler",
        "version",
        "total_payout",
        "total_fees",
        "remainder",
        "tx_hash",
        "inserted_at",
    ]
    write_csv(Path(args.out_dir) / "devshard_settlement_events_tagged.csv", tagged_rows, fields)
    write_csv(
        Path(args.out_dir) / "devshard_settlement_events_summary.csv",
        summary,
        [
            "epoch",
            "settlement_event_count",
            "escrow_id_min",
            "escrow_id_max",
            "block_height_min",
            "block_height_max",
            "total_payout_sum",
            "remainder_sum",
            "settlers",
            "versions",
        ],
    )
    (Path(args.out_dir) / "devshard_settlement_events_summary.json").write_text(
        json.dumps({"summary": summary}, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
