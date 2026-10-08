# Task 1: model-size hypotheses and traffic-profile interpretations

This analysis uses all **77 workbooks / 275 rows** in `perf_data.zip`:
11 anonymized models × 7 traffic profiles. Each model has the same 25 scenario
and batch combinations. Profile 2 contributes one batch; each other profile
contributes four. The workbooks describe projections, not measured performance.

The [normalized CSV](data/task1-projections.csv) preserves workbook paths and
Summary worksheet row numbers. The [summary JSON](data/task1-summary.json)
records the archive SHA-256, comparison calculations, and engineering flags.
Reproduce both from the repository root:

```powershell
cd backend
uv sync --locked
uv run python ../docs/scripts/summarize_task1.py
```

The script uses the application's parser, reads the archive without extracting
or changing it, verifies identical model coverage, and writes deterministic
evidence files. Interpretation remains separate from the generated metrics.

## What can be inferred about model size

My working hypothesis is that **I and G are relatively small/efficient, E is
efficient but atypical, A/H/K are intermediate, F/J are heavier, and B/D/C are
the largest or most expensive to serve**. This is a ranking of effective
serving burden under matched workloads. Exact parameter counts and model
identities are not identifiable from these files.

Aggregate capacity alone would give a misleading size ordering: models have
different aggregate-to-per-box ratios. I instead compare reported throughput
per box for identical profile, input/output, cache, and batch configurations.
For each model, define a relative burden proxy:

```text
r_model = median over 25 matching configurations of
          (Model A throughput_per_box / model throughput_per_box)
```

For numerical size hypotheses, suppose Model A were a **70B dense model** and
all models had comparable hardware, precision, utilization, and approximately
inverse size-to-per-box-throughput scaling. Then a dense-equivalent estimate
would be `70B * r_model`. The 70B anchor is an illustrative assumption, not a
fact supplied by the challenge. The final column varies that assumed anchor
from 30B to 100B; it is sensitivity analysis, **not a confidence interval**.
These numbers quantify the hypothesis, not verified parameter counts. Unknown
hardware, mixture-of-experts architecture, quantization, or bottlenecks could
invalidate the mapping completely.

The table's observed metrics are profile 1 / batch 10 / input 10,000 / output
333 / cache 50%, from Summary row 3 of each corresponding workbook. Rank ranges
and the burden proxy use all 25 matched configurations. Rank 1 is highest
per-box throughput. All values are rounded for readability; JSON retains the
calculation precision.

| Model | Per-box throughput (t/s) | Generation (t/s/user) | Per-box rank range | Burden vs A | Conditional size if A=70B | Sensitivity if A=30–100B |
| ----- | -----------------------: | --------------------: | ------------------ | ----------: | ------------------------: | ------------------------ |
| A     |                   37,374 |                 1,354 | 4–9                |       1.000 |                       70B | 30–100B                  |
| B     |                    9,325 |                   865 | 8–9                |       4.189 |                      293B | 126–419B                 |
| C     |                    3,210 |                   451 | 11–11              |      11.352 |                      795B | 341–1,135B               |
| D     |                    4,821 |                   890 | 10–10              |       7.884 |                      552B | 237–788B                 |
| E     |                   46,107 |                 1,395 | 2–7                |       0.652 |                       46B | 20–65B                   |
| F     |                   23,950 |                 1,207 | 5–8                |       1.408 |                       99B | 42–141B                  |
| G     |                   69,008 |                 1,737 | 2–3                |       0.484 |                       34B | 15–48B                   |
| H     |                   34,337 |                 1,313 | 3–5                |       0.974 |                       68B | 29–97B                   |
| I     |                   90,066 |                 1,512 | 1–1                |       0.351 |                       25B | 11–35B                   |
| J     |                   19,328 |                 1,217 | 6–8                |       1.648 |                      115B | 49–165B                  |
| K     |                   30,823 |                 1,419 | 4–6                |       1.095 |                       77B | 33–110B                  |

### Per-model interpretation and counter-evidence

- **A:** intermediate baseline. Aggregate/per-box stays near 7, but profile 6
  capacity is nearly flat as batch rises. Its effective burden varies by
  workload, making it an imperfect size anchor.
- **B:** a large/heavy candidate. Its generation speed is below A and per-box
  rank is consistently 8–9. The aggregate/per-box ratio is near 24; that is
  allocation evidence rather than proof that it has 24 physical boxes.
- **C:** strongest candidate for the largest/heaviest model: consistently last
  in per-box throughput, with only 451 t/s/user at the baseline. The very large
  conditional dense-equivalent number could instead indicate poor utilization,
  a different architecture, or a serving bottleneck; it does not identify an 800B model.
- **D:** second-heaviest per-box candidate, consistently rank 10. It generates
  slightly faster than B at baseline but has roughly half B's per-box capacity,
  so decode speed and normalized capacity do not yield the same size ordering.
- **E:** efficient and anomalous. Profile 1 generation remains about 1,391–1,395
  t/s/user from batch 10 to 40 while capacity rises almost fourfold. This could
  reflect a different bottleneck or projection assumption. Its conditional 46B
  value should be treated especially cautiously.
- **F:** heavier than A in the median, with lower baseline generation speed and
  per-box capacity. At profile 6 it becomes much more efficient than A, so
  a single universal size-to-throughput conversion is inadequate.
- **G:** small/efficient candidate, consistently rank 2–3 per box and the fastest
  baseline generation speed. The ratio near 4 and strong capacity reinforce
  the efficiency hypothesis, without specifying its architecture.
- **H:** A-like median burden but ranks 3–5, better than A across much of the
  workload set. Its profile 6 throughput is especially strong relative to A.
  A similar parameter scale is plausible under the stated assumptions.
- **I:** smallest/most efficient per-box candidate, rank 1 in every matched
  configuration and ratio near 3. G generates faster per user, demonstrating
  that best per-box capacity does not imply best single-user speed.
- **J:** medium-large serving burden, between F and B in median efficiency,
  with an aggregate/per-box ratio near 13. Generation speed is close to F;
  capacity suggests a larger resource burden under the chosen proxy.
- **K:** near A/H's intermediate group by median burden, with rank 4–6 and
  baseline generation faster than A. Its ratio near 9 is consistent with a
  different allocation, not a direct parameter-count measurement.

### Why the numerical estimates have low confidence

The model/A burden ratio varies substantially with profile and batch: G ranges
from 0.114 to 0.545 and C from 1.697 to 17.692. Even the assumed proportionality
is unstable. The summary JSON includes these ranges for every model.
High confidence attaches to the observed per-box rankings, conditional on
the supplied projections. Confidence in converting them to parameter counts
is low. A model manifest containing parameter count, active parameters for MoE,
weight precision, hardware type/allocation, and serving settings would resolve
more uncertainty than another guessed letter-to-brand mapping.

External reference points reinforce that caution: Cerebras reported 450
t/s/user for Llama 3.1 70B at its August 2024 launch and 2,100 t/s/user for the
same parameter scale after its October 2024 serving-stack update. Its update
describes optimized kernels and speculative decoding. Thus even a known
parameter count does not determine a fixed speed; these historical numbers
must not be used to label the anonymized sweeps. Sources:
[launch announcement](https://www.cerebras.ai/blog/introducing-cerebras-inference-ai-at-instant-speed)
and [October update](https://www.cerebras.ai/blog/cerebras-inference-3x-faster).

## Profile 1–7: traffic shapes and likely use cases

All eleven models share each profile's input/output/cache shape. Cache values
are workbook settings, not measured hit rates. Batch sizes are 10/20/30/40
except profile 2, which contains only batch 10.

| Profile | Input tokens | Output tokens | Cache | Likely use case                                                               | Reasoning and key decision metric                                                                                                                         |
| ------- | -----------: | ------------: | ----: | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       |       10,000 |           333 |   50% | Document/RAG question answering or short summarization                        | Long prompt with a short answer and some reusable context. Prioritize TTFT and request capacity; generation length is relatively small                    |
| 2       |       10,000 |         4,000 |    0% | One-off long report, synthesis, or code generation from a fresh specification | Long fresh input and substantial new output. Decode speed and complete-response time matter; there is no cache benefit or batch trend to infer            |
| 3       |        3,200 |           400 |   50% | Customer-support chat, FAQ, or a compact RAG assistant                        | Moderate prompt and concise reply with reused instructions/context. Interactive TTFT, generation speed, and concurrency matter                            |
| 4       |        1,000 |         1,000 |   50% | Short-prompt drafting, rewriting, translation, or code completion             | Output is as long as input, so generation contributes strongly to turnaround. Examine per-user speed and batch saturation                                 |
| 5       |        8,000 |         1,000 |   50% | Multi-document summarization or grounded analytical answers                   | Substantial context and a medium answer. Balance prefill/TTFT against generation speed and per-box capacity                                               |
| 6       |       60,000 |           200 |   90% | Repeated questions or extraction over a large shared document/repository      | Very long reusable context and a brief answer. Validate actual reuse and context support; reported total tokens may exaggerate new work per request       |
| 7       |       17,000 |         3,500 |   70% | Long-form analysis, detailed code generation, or repeated agent workflows     | Both substantial context and long output, with reusable prefix material. Balance cache assumptions, generation duration, and capacity at the chosen batch |

These are workload interpretations, not labels present in the source files.
Token counts do not uniquely distinguish summarization from coding, and cache
fractions do not establish how the cache works. In particular, nothing in these
workbooks proves the multimodal or image-processing capability of any model.

## Practical conclusions supported by the projections

**Compare complete configurations.** For Model A profile 1, batch 10 provides
261,616 total t/s, 1,354 t/s/user, and TTFT 11ms. At batch 20 these become
404,149 t/s, 1,220 t/s/user, and 8.33ms. For targets 400,000 t/s, 1,200 t/s/user,
and TTFT ≤10ms, batch 20 passes while batch 10 fails. At batch 40 capacity
reaches 563,874 t/s, but generation falls to 982 t/s/user and fails that speed
target. Picking the largest capacity row alone would give the wrong answer.

**Do not assume monotonic batch scaling.** Model I profile 4 peaks at batch 20
at 69,613 t/s/box, then declines to 66,957 and 62,736 at batches 30 and 40.
Model A profile 6 stays around 62,580–62,593 t/s/box while generation drops
from 1,202 to 795 t/s/user. Larger batches can add latency or reduce per-user
speed without useful capacity gains.

**Review zero latency.** Model E profile 4, batch 40, Summary row 6 reports
TTFT **0ms**. The engineering endpoint flags this as a nonpositive metric.
Across the whole archive it also emits 15 >5% throughput-drop-on-scaling flags
and no decomposition mismatch flags at its current tolerance. This is rule
output, not proof that every unflagged projection is accurate.

**Keep request capacity and billed/new-token capacity distinct.** At 90% cache
and 60,000 input tokens, profile 6's total token rate includes substantial
reusable context. Its raw throughput cannot be interpreted as new output
tokens/s or used as a cross-profile quality ranking. The UI preserves cached
and uncached components for engineering inspection.

**Require production evidence before an SLA or size claim.** Validate tail
latency, achieved cache behavior, resource allocation, and model quality
separately. The current application deliberately makes its decisions from
projected rows and explicit caller assumptions.
