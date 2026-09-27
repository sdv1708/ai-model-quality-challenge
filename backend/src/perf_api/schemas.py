from pydantic import BaseModel, ConfigDict, Field


class PerformanceRecord(BaseModel):
    """Normalized performance metrics for a single row in a sweep."""

    model_config = ConfigDict(populate_by_name=True)

    input_length: int = Field(..., validation_alias="Input Length")
    output_length: int = Field(..., validation_alias="Output Length")
    cache_percentage: float = Field(..., validation_alias="Cache %")
    batch_size: int = Field(..., validation_alias="Batch Size")
    max_ms: float = Field(..., validation_alias="Max number of milliseconds")
    target_max_ms: float = Field(..., validation_alias="Target Max number of milliseconds")
    prompt_throughput: float = Field(..., validation_alias="Prompt only Throughput (t/s)")
    gen_throughput: float = Field(..., validation_alias="Gen only Throughput (t/s)")
    throughput: float = Field(..., validation_alias="Throughput (t/s)")
    throughput_per_box: float = Field(..., validation_alias="Throughput / box (t/s/hardware)")
    uncached_throughput: float = Field(..., validation_alias="Uncached Throughput (t/s)")
    uncached_throughput_per_box: float = Field(
        ..., validation_alias="Uncached Throughput / box (t/s/hardware)"
    )
    cached_throughput: float = Field(..., validation_alias="Cached Throughput (t/s)")
    cached_throughput_per_box: float = Field(
        ..., validation_alias="Cached Throughput / box (t/s/hardware)"
    )
    ttft_ms: float = Field(..., validation_alias="TTFT (ms)")
    real_prompt_speed: float = Field(..., validation_alias="Real Prompt Speed (t/s/user)")
    prompt_speed_queued: float = Field(
        ..., validation_alias="Prompt Speed with Queueing (t/s/user)"
    )
    gen_speed: float = Field(..., validation_alias="Gen Speed (t/s/user)")
    rpm: float = Field(..., validation_alias="RPM")


class WorkbookNormalizationResponse(BaseModel):
    """Response wrapper for a normalized performance workbook."""

    model_name: str
    profile_id: str
    record_count: int
    records: list[PerformanceRecord]
