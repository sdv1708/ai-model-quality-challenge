"""Reproduce Task 1 documentation evidence from the supplied workbook archive.

Run from backend/: uv run python ../docs/scripts/summarize_task1.py
Uses the installed application parser; creates no changes to uploaded source data.
"""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from statistics import median
from zipfile import ZipFile

from perf_api.engineering import analyze_engineering
from perf_api.parser import parse_and_normalize_workbook


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    archive = root / "perf_data.zip"
    output = root / "docs" / "data"
    output.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as bundle:
        workbooks = [
            (
                name,
                parse_and_normalize_workbook(
                    bundle.read(name), PurePosixPath(name).name
                ),
            )
            for name in sorted(bundle.namelist())
            if name.endswith(".xlsx")
        ]

    models = sorted({wb.model_name for _, wb in workbooks})
    profiles = sorted({wb.profile_id for _, wb in workbooks}, key=int)
    if models != [f"Model {letter}" for letter in "ABCDEFGHIJK"] or profiles != list(
        "1234567"
    ):
        raise ValueError("Documentation expects the original A-K, profile 1-7 archive")

    rows = []
    indexed = {}
    for name, wb in workbooks:
        for index, record in enumerate(wb.records):
            key = (
                wb.profile_id,
                record.input_length,
                record.output_length,
                record.cache_percentage,
                record.batch_size,
            )
            model_key = (wb.model_name, key)
            if model_key in indexed:
                raise ValueError(f"Duplicate model/configuration: {model_key}")
            indexed[model_key] = record
            rows.append(
                {
                    "workbook_path": name,
                    "summary_excel_row": index + 3,
                    "model_name": wb.model_name,
                    "profile_id": wb.profile_id,
                    **record.model_dump(),
                }
            )

    with (output / "task1-projections.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    reference_keys = sorted(key for model, key in indexed if model == "Model A")
    summaries = []
    for model in models:
        keys = sorted(key for row_model, key in indexed if row_model == model)
        if keys != reference_keys:
            raise ValueError(
                f"Unmatched coverage for {model}; revise the comparison method"
            )
        relative = []
        capacity_ratios = []
        ranks = []
        for key in keys:
            record = indexed[model, key]
            reference = indexed["Model A", key]
            relative.append(reference.throughput_per_box / record.throughput_per_box)
            capacity_ratios.append(record.throughput / record.throughput_per_box)
            ranks.append(
                1
                + sum(
                    indexed[peer, key].throughput_per_box > record.throughput_per_box
                    for peer in models
                )
            )
        baseline = indexed[model, ("1", 10000, 333, 0.5, 10)]
        summaries.append(
            {
                "model": model,
                "matched_configuration_count": len(keys),
                "profile1_batch10_throughput_per_box": baseline.throughput_per_box,
                "profile1_batch10_generation_speed": baseline.gen_speed,
                "aggregate_to_per_box_ratio_range": [
                    min(capacity_ratios),
                    max(capacity_ratios),
                ],
                "per_box_throughput_rank_range": [min(ranks), max(ranks)],
                "inverse_per_box_ratio_to_A_median": median(relative),
                "inverse_per_box_ratio_to_A_range": [min(relative), max(relative)],
                "conditional_dense_equivalent_B_if_A_70B": 70 * median(relative),
                "anchor_sensitivity_B_if_A_30_to_100B": [
                    30 * median(relative),
                    100 * median(relative),
                ],
            }
        )

    profile_summaries = []
    for profile in profiles:
        records = [r for (model, key), r in indexed.items() if key[0] == profile]
        scenarios = sorted(
            {(r.input_length, r.output_length, r.cache_percentage) for r in records}
        )
        profile_summaries.append(
            {
                "profile": profile,
                "scenarios_input_output_cache": scenarios,
                "batch_sizes": sorted({r.batch_size for r in records}),
                "record_count": len(records),
            }
        )

    engineering = analyze_engineering([wb for _, wb in workbooks])
    evidence = {
        "source": "perf_data.zip",
        "source_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "workbook_count": len(workbooks),
        "record_count": len(rows),
        "method": "Median A/model per-box throughput ratio over all matching configurations",
        "size_assumption": "Illustrative dense-equivalent proxy, NOT identified parameter counts",
        "models": summaries,
        "profiles": profile_summaries,
        "engineering_flag_counts": dict(
            sorted(Counter(f.code for f in engineering.anomalies).items())
        ),
        "engineering_flags": [flag.model_dump() for flag in engineering.anomalies],
    }
    (output / "task1-summary.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Summarized {len(workbooks)} workbooks / {len(rows)} rows into {output}")


if __name__ == "__main__":
    main()
