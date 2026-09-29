"""Pure comparison logic for issue #6; no HTTP or workbook byte handling here."""

from collections.abc import Sequence

from perf_api.comparison_schemas import (
    AlignedConfiguration,
    ComparisonDiagnostic,
    ComparisonResponse,
    ConfigurationKey,
    ModelConfiguration,
)
from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse


def configuration_key(profile_id: str, record: PerformanceRecord) -> ConfigurationKey:
    """Use the same cache precision for duplicate detection and model alignment."""
    return ConfigurationKey(
        profile_id=profile_id,
        input_length=record.input_length,
        output_length=record.output_length,
        cache_percentage=round(record.cache_percentage, 4),
        batch_size=record.batch_size,
    )


def compare_workbooks(
    workbooks: Sequence[WorkbookNormalizationResponse],
    initial_diagnostics: Sequence[ComparisonDiagnostic] = (),
) -> ComparisonResponse:
    """Align normalized sweeps, independent of upload order."""
    diagnostics: list[ComparisonDiagnostic] = list(initial_diagnostics)

    sweeps: dict[tuple[str, str], list[WorkbookNormalizationResponse]] = {}
    for workbook in workbooks:
        sweeps.setdefault((workbook.model_name, workbook.profile_id), []).append(workbook)

    valid_workbooks: list[WorkbookNormalizationResponse] = []
    for (model_name, profile_id), copies in sorted(sweeps.items()):
        if len(copies) > 1:
            conflicting = len({copy.model_dump_json() for copy in copies}) > 1
            diagnostics.append(
                ComparisonDiagnostic(
                    code="CONFLICTING_SWEEP" if conflicting else "DUPLICATE_SWEEP",
                    message=(
                        f"{len(copies)} uploads claim model '{model_name}' and profile "
                        f"'{profile_id}'. "
                        + (
                            "Their projections differ, so none were compared."
                            if conflicting
                            else "Identical copies were compared once."
                        )
                    ),
                    model_name=model_name,
                    profile_id=profile_id,
                )
            )
            if conflicting:
                continue
        valid_workbooks.append(copies[0])

    usable_workbooks: list[WorkbookNormalizationResponse] = []
    grouped_members: dict[ConfigurationKey, list[ModelConfiguration]] = {}

    for workbook in valid_workbooks:
        rows_by_key: dict[ConfigurationKey, list[PerformanceRecord]] = {}
        for record in workbook.records:
            key = configuration_key(workbook.profile_id, record)
            rows_by_key.setdefault(key, []).append(record)

        duplicates = [(key, rows) for key, rows in rows_by_key.items() if len(rows) > 1]
        for key, rows in duplicates:
            diagnostics.append(
                ComparisonDiagnostic(
                    code="DUPLICATE_CONFIGURATION",
                    message=(
                        f"{len(rows)} rows have the same configuration "
                        f"(input={key.input_length}, output={key.output_length}, "
                        f"cache={key.cache_percentage}, batch={key.batch_size}) for "
                        f"model '{workbook.model_name}' and profile '{workbook.profile_id}'; "
                        "the sweep was excluded."
                    ),
                    model_name=workbook.model_name,
                    profile_id=workbook.profile_id,
                )
            )
        if duplicates:
            continue

        usable_workbooks.append(workbook)
        for key, rows in rows_by_key.items():
            grouped_members.setdefault(key, []).append(
                ModelConfiguration(model_name=workbook.model_name, record=rows[0])
            )

    sorted_models = sorted({workbook.model_name for workbook in usable_workbooks})
    # 4. Build AlignedConfigurations
    aligned_configurations: list[AlignedConfiguration] = []
    for key, members in grouped_members.items():
        sorted_members = sorted(members, key=lambda m: m.model_name)
        present_models = {m.model_name for m in sorted_members}
        missing_models = [m for m in sorted_models if m not in present_models]
        is_comparable = len(present_models) >= 2

        aligned_configurations.append(
            AlignedConfiguration(
                key=key,
                members=sorted_members,
                missing_models=missing_models,
                is_comparable=is_comparable,
            )
        )

    # 5. Deterministic sorting for upload order independence
    aligned_configurations.sort(
        key=lambda c: (
            c.key.profile_id,
            c.key.input_length,
            c.key.output_length,
            c.key.cache_percentage,
            c.key.batch_size,
        )
    )

    sorted_workbooks = sorted(usable_workbooks, key=lambda w: (w.model_name, w.profile_id))

    sorted_diagnostics = sorted(
        diagnostics,
        key=lambda d: (
            d.code,
            d.filename or "",
            d.model_name or "",
            d.profile_id or "",
            d.message,
        ),
    )

    return ComparisonResponse(
        workbooks=sorted_workbooks,
        models=sorted_models,
        configurations=aligned_configurations,
        diagnostics=sorted_diagnostics,
    )
