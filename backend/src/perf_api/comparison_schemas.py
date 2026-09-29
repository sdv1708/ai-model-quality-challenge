"""Public shapes for comparing one or more normalized performance sweeps.

These are starter contracts for issue #6. The learner should revise them when
the comparison rules are settled, before implementing the HTTP endpoint.
"""

from pydantic import BaseModel

from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse


class ConfigurationKey(BaseModel):
    """Dimensions that must match before projected metrics are compared.

    TODO(issue #6, step 1): Confirm this exact-match policy against the supplied
    workbooks. Define how cache fractions are canonicalized and whether a profile
    identifier alone is sufficient to describe the same traffic scenario.
    """

    profile_id: str
    input_length: int
    output_length: int
    cache_percentage: float
    batch_size: int


class ModelConfiguration(BaseModel):
    """A model's projected row in an aligned configuration."""

    model_name: str
    record: PerformanceRecord


class AlignedConfiguration(BaseModel):
    """Rows sharing a comparison key, with coverage made explicit."""

    key: ConfigurationKey
    members: list[ModelConfiguration]
    missing_models: list[str]
    is_comparable: bool


class ComparisonDiagnostic(BaseModel):
    """A file or alignment problem that a caller can act on."""

    code: str
    message: str
    filename: str | None = None
    model_name: str | None = None
    profile_id: str | None = None


class ComparisonResponse(BaseModel):
    """One or many uploads after the same normalization and alignment path."""

    workbooks: list[WorkbookNormalizationResponse]
    models: list[str]
    configurations: list[AlignedConfiguration]
    diagnostics: list[ComparisonDiagnostic]
