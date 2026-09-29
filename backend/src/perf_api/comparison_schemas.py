"""Public shapes for comparing one or more normalized performance sweeps."""

from pydantic import BaseModel, ConfigDict

from perf_api.schemas import PerformanceRecord, WorkbookNormalizationResponse


class ConfigurationKey(BaseModel):
    """Dimensions that must match before projected metrics are compared."""

    model_config = ConfigDict(frozen=True)

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
