"""Validate the canonical dataset and export reproducible train/val/test files.

The value in ``data/processed/dataset_all.csv`` is the single source of truth.
This script never reassigns a sample: it validates the existing ``split`` and
``group_id`` columns, then derives the three files in ``data/splits``.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_COLUMNS = {
    "payload_id",
    "payload",
    "label",
    "category",
    "source",
    "group_id",
    "split",
}
OUTPUT_COLUMNS = [
    "payload_id",
    "input_text",
    "label",
    "source",
    "category",
    "group_id",
    "notes",
]
VALID_LABELS = {"0", "1"}
VALID_SPLITS = ("train", "val", "test")

SOURCE_MAP = {
    "command-injection-commix": "commix",
    "command_exec": "payloadsallthethings",
    "command-execution-unix": "payloadsallthethings",
    "csic2010": "csic",
    "faker": "handwritten",
    "goodqueries_sample": "handwritten",
    "benign_special_chars": "handwritten",
    "manual_bulk_draft": "handwritten",
}


def fail(message: str) -> None:
    raise ValueError(message)


def read_dataset(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            fail("Dataset does not contain a header row")
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            fail(f"Missing required columns: {', '.join(sorted(missing))}")
        return list(reader), list(reader.fieldnames)


def validate(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        fail("Dataset is empty")

    ids: set[str] = set()
    payload_labels: dict[str, set[str]] = defaultdict(set)
    payload_splits: dict[str, set[str]] = defaultdict(set)
    group_splits: dict[str, set[str]] = defaultdict(set)
    counts: Counter[tuple[str, str]] = Counter()

    for line_number, row in enumerate(rows, start=2):
        payload_id = row["payload_id"].strip()
        payload = row["payload"]
        label = row["label"].strip()
        group_id = row["group_id"].strip()
        split = row["split"].strip()

        if not payload_id:
            fail(f"Line {line_number}: empty payload_id")
        if payload_id in ids:
            fail(f"Line {line_number}: duplicate payload_id {payload_id!r}")
        ids.add(payload_id)

        if not payload.strip():
            fail(f"Line {line_number}: empty payload")
        if label not in VALID_LABELS:
            fail(f"Line {line_number}: invalid label {label!r}")
        if not group_id:
            fail(f"Line {line_number}: empty group_id")
        if split not in VALID_SPLITS:
            fail(f"Line {line_number}: invalid split {split!r}")

        payload_labels[payload.strip()].add(label)
        payload_splits[payload.strip()].add(split)
        group_splits[group_id].add(split)
        counts[(split, label)] += 1

    conflicts = [payload for payload, labels in payload_labels.items() if len(labels) > 1]
    if conflicts:
        fail(f"Payloads with conflicting labels: {len(conflicts)}")

    leaking_payloads = [
        payload for payload, splits in payload_splits.items() if len(splits) > 1
    ]
    if leaking_payloads:
        fail(f"Exact payload values assigned to multiple splits: {len(leaking_payloads)}")

    leaking_groups = [group for group, splits in group_splits.items() if len(splits) > 1]
    if leaking_groups:
        fail(f"group_id values assigned to multiple splits: {len(leaking_groups)}")

    lines = [
        f"Dataset rows: {len(rows)}",
        f"Unique payload_id: {len(ids)}",
        f"Unique group_id: {len(group_splits)}",
        "Label conflicts: 0",
        "Exact payload leakage: 0",
        "Group leakage: 0",
        "",
        "Split summary:",
    ]
    for split in VALID_SPLITS:
        benign = counts[(split, "0")]
        malicious = counts[(split, "1")]
        lines.append(
            f"- {split}: {benign + malicious} rows "
            f"(benign={benign}, malicious={malicious})"
        )
    lines.extend(["", "RESULT: PASS"])
    return lines


def to_base_row(row: dict[str, str]) -> dict[str, str]:
    original_source = row["source"].strip()
    source = SOURCE_MAP.get(original_source)
    if source is None:
        fail(f"Source {original_source!r} has no mapping to the base schema")

    details = []
    if original_source != source:
        details.append(f"original_source={original_source}")
    for column in ("context", "technique", "family"):
        value = row.get(column, "").strip()
        if value:
            details.append(f"{column}={value}")

    return {
        "payload_id": row["payload_id"].strip(),
        "input_text": row["payload"],
        "label": row["label"].strip(),
        "source": source,
        "category": row["category"].strip(),
        "group_id": row["group_id"].strip(),
        "notes": "; ".join(details),
    }


def export(rows: list[dict[str, str]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in VALID_SPLITS:
        output_path = output_dir / f"{split}.csv"
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(
                to_base_row(row) for row in rows if row["split"].strip() == split
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/dataset_all.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/splits"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/week2_dataset_validation.txt"),
    )
    args = parser.parse_args()

    rows, _ = read_dataset(args.input)
    report_lines = validate(rows)
    export(rows, args.output_dir)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
