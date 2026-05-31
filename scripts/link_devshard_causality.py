#!/usr/bin/env python3
"""Link devshard decoded txs to inference and validation rows for case addresses."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


CASE_ADDRESSES = {
    "gonka1wt8sr9jxzpec65j7zkxsgh6edk3m6r8nlf5za4",
    "gonka10079cnl3nuh2k82mhkm04dj0slhtw9kmjewwau",
    "gonka1007g0ut3u4wjkay9hegqfev4pj90qgexwskmcw",
    "gonka1007dchuqgdnute4qam70kmn56j2vfw38mhyrqv",
    "gonka15munkmx6x7k6rqqeexjet4556p7at39ks9qgr5",
    "gonka1ce02jjduga8jvwj8jx39mxn0jr345vgkx7lk2n",
    "gonka16xa2sdc8qe2289nzr4e6vmdyzlke8g8fn8e75s",
}


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path):
    with path.open(errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epoch", type=int, default=272)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--artifacts-dir", default="artifacts")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    artifacts_dir = Path(args.artifacts_dir)
    epoch = args.epoch

    decoded = read_csv(artifacts_dir / f"devshard_epoch_{epoch}_decoded_txs.csv")

    tx_by_key = defaultdict(lambda: {"timeouts": [], "starts": [], "validations": []})
    for row in decoded:
        key = (int(row["escrow_id"]), int(row["inference_id"] or 0))
        if row["kind"] == "timeout_inference":
            tx_by_key[key]["timeouts"].append(row)
        elif row["kind"] == "start_inference":
            tx_by_key[key]["starts"].append(row)
        elif row["kind"] in {"validation", "validation_vote"}:
            tx_by_key[key]["validations"].append(row)

    inference_rows = {}
    epoch_escrows = set()
    for row in iter_jsonl(data_dir / "devshard_inferences.ndjson"):
        if int(row.get("epoch_index") or 0) != epoch:
            continue
        key = (int(row["escrow_id"]), int(row["inference_id"]))
        epoch_escrows.add(int(row["escrow_id"]))
        inference_rows[key] = row

    validations_by_key = defaultdict(list)
    validations_by_case_addr = defaultdict(list)
    for row in iter_jsonl(data_dir / "devshard_validations.ndjson"):
        escrow_id = int(row["escrow_id"])
        if escrow_id not in epoch_escrows:
            continue
        key = (escrow_id, int(row["inference_id"]))
        validations_by_key[key].append(row)
        if row.get("validator_addr") in CASE_ADDRESSES:
            validations_by_case_addr[row["validator_addr"]].append(row)

    linked_case_executor_rows = []
    linked_case_validator_rows = []
    participant_summary = {}
    for addr in CASE_ADDRESSES:
        participant_summary[addr] = Counter()

    for key, inf in inference_rows.items():
        executor = inf.get("executor_address") or ""
        linked = tx_by_key.get(key, {})
        timeouts = linked.get("timeouts", [])
        timeout_reasons = Counter(row["reason"] for row in timeouts)
        validations = validations_by_key.get(key, [])
        valid_false = sum(1 for row in validations if int(row.get("valid") or 0) == 0)
        valid_true = sum(1 for row in validations if int(row.get("valid") or 0) == 1)
        input_length = int(inf.get("input_length_claimed") or 0)

        if executor in CASE_ADDRESSES:
            s = participant_summary[executor]
            s["executed"] += 1
            s["executed_cost"] += int(inf.get("cost") or 0)
            s["executed_with_timeout"] += 1 if timeouts else 0
            s["executed_with_execution_timeout"] += timeout_reasons["TIMEOUT_REASON_EXECUTION"]
            s["executed_with_refusal_timeout"] += timeout_reasons["TIMEOUT_REASON_REFUSED"]
            s["executed_validation_false_rows"] += valid_false
            s["executed_validation_true_rows"] += valid_true
            s["executed_long_input_gt_100k"] += 1 if input_length > 100000 else 0
            s["executed_long_input_gt_500k"] += 1 if input_length > 500000 else 0
            linked_case_executor_rows.append(
                {
                    "participant": executor,
                    "escrow_id": key[0],
                    "inference_id": key[1],
                    "status": inf.get("status", ""),
                    "model": inf.get("model", ""),
                    "input_length_claimed": input_length,
                    "input_tokens_actual": inf.get("input_tokens_actual", ""),
                    "output_tokens": inf.get("output_tokens", ""),
                    "cost": inf.get("cost", ""),
                    "timeout_count": len(timeouts),
                    "timeout_reasons": ";".join(
                        f"{reason}:{count}" for reason, count in sorted(timeout_reasons.items())
                    ),
                    "validation_false_rows_for_inference": valid_false,
                    "validation_true_rows_for_inference": valid_true,
                }
            )

    for addr, rows in validations_by_case_addr.items():
        for row in rows:
            key = (int(row["escrow_id"]), int(row["inference_id"]))
            inf = inference_rows.get(key, {})
            linked = tx_by_key.get(key, {})
            timeouts = linked.get("timeouts", [])
            timeout_reasons = Counter(tx["reason"] for tx in timeouts)
            s = participant_summary[addr]
            s["validator_rows"] += 1
            s["validator_valid_false"] += 1 if int(row.get("valid") or 0) == 0 else 0
            s["validator_valid_true"] += 1 if int(row.get("valid") or 0) == 1 else 0
            s["validator_rows_on_timed_out_inference"] += 1 if timeouts else 0
            input_length = int(inf.get("input_length_claimed") or 0)
            s["validator_long_input_gt_100k"] += 1 if input_length > 100000 else 0
            s["validator_long_input_gt_500k"] += 1 if input_length > 500000 else 0
            linked_case_validator_rows.append(
                {
                    "participant": addr,
                    "escrow_id": key[0],
                    "inference_id": key[1],
                    "validator_slot": row.get("validator_slot", ""),
                    "valid": row.get("valid", ""),
                    "is_vote": row.get("is_vote", ""),
                    "inference_status": inf.get("status", ""),
                    "executor_address": inf.get("executor_address", ""),
                    "model": inf.get("model", ""),
                    "input_length_claimed": input_length,
                    "timeout_count": len(timeouts),
                    "timeout_reasons": ";".join(
                        f"{reason}:{count}" for reason, count in sorted(timeout_reasons.items())
                    ),
                }
            )

    summary_rows = []
    for addr in sorted(CASE_ADDRESSES):
        c = participant_summary[addr]
        summary_rows.append(
            {
                "participant": addr,
                "executed": c["executed"],
                "executed_cost": c["executed_cost"],
                "executed_with_timeout": c["executed_with_timeout"],
                "executed_execution_timeout_count": c["executed_with_execution_timeout"],
                "executed_refusal_timeout_count": c["executed_with_refusal_timeout"],
                "executed_validation_false_rows": c["executed_validation_false_rows"],
                "executed_validation_true_rows": c["executed_validation_true_rows"],
                "executed_long_input_gt_100k": c["executed_long_input_gt_100k"],
                "executed_long_input_gt_500k": c["executed_long_input_gt_500k"],
                "validator_rows": c["validator_rows"],
                "validator_valid_false": c["validator_valid_false"],
                "validator_valid_true": c["validator_valid_true"],
                "validator_rows_on_timed_out_inference": c["validator_rows_on_timed_out_inference"],
                "validator_long_input_gt_100k": c["validator_long_input_gt_100k"],
                "validator_long_input_gt_500k": c["validator_long_input_gt_500k"],
            }
        )

    write_csv(
        artifacts_dir / f"devshard_epoch_{epoch}_case_causality_summary.csv",
        summary_rows,
        list(summary_rows[0].keys()),
    )
    write_csv(
        artifacts_dir / f"devshard_epoch_{epoch}_case_executor_causality.csv",
        linked_case_executor_rows,
        [
            "participant",
            "escrow_id",
            "inference_id",
            "status",
            "model",
            "input_length_claimed",
            "input_tokens_actual",
            "output_tokens",
            "cost",
            "timeout_count",
            "timeout_reasons",
            "validation_false_rows_for_inference",
            "validation_true_rows_for_inference",
        ],
    )
    write_csv(
        artifacts_dir / f"devshard_epoch_{epoch}_case_validator_causality.csv",
        linked_case_validator_rows,
        [
            "participant",
            "escrow_id",
            "inference_id",
            "validator_slot",
            "valid",
            "is_vote",
            "inference_status",
            "executor_address",
            "model",
            "input_length_claimed",
            "timeout_count",
            "timeout_reasons",
        ],
    )
    report = {
        "epoch": epoch,
        "case_summary": summary_rows,
        "case_executor_rows": len(linked_case_executor_rows),
        "case_validator_rows": len(linked_case_validator_rows),
    }
    (artifacts_dir / f"devshard_epoch_{epoch}_case_causality_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
