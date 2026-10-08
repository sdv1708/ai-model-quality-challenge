# Issue #12: documentation and clean-clone evidence

Verification date: **2026-10-08 (America/Los_Angeles)**.
Application baseline: `3adc36d` on `main`; issue #12 adds documentation and a
reproducible evidence script, with no application behavior changes.

## Acceptance mapping

| Issue requirement                                       | Deliverable / verification                                                                                                                                                                  |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Live URL prominently in root documentation              | First link in [README](../README.md) points to the public Task 1 app                                                                                                                        |
| A clean clone can install and launch                    | Root README gives prerequisites, locked installs, two-terminal startup, sample/multi-upload usage, and verification commands; fresh-clone results below                                     |
| Framework choice and rejected alternatives              | [Design analysis](task1-analysis.md) explains React/TypeScript/Vite, FastAPI/openpyxl, Vercel, and alternatives with their trade-offs                                                       |
| More data, production measurements, and more time       | Separate actions and resulting decision improvements in the design analysis                                                                                                                 |
| All model A–K estimates and profile 1–7 interpretations | [Model/profile analysis](task1-models-and-profiles.md) covers every letter and profile, matched metrics, explicit conditional numerical size hypotheses, confidence limits, and source rows |

Model parameter counts are absent from the supplied source. The numerical
estimates are explicitly conditional dense-equivalent hypotheses, not identified
model sizes. This evidence establishes reproducibility and complete coverage;
it cannot establish the true hidden parameter counts. The write-up supports
the subsequent video issue #13, but does not create or claim a recorded video.

## Fresh-clone procedure and results

Created a separate local clone at
`D:\ai-model-quality-challenge-main\issue-12-clean-clone` with `git clone
--no-hardlinks --no-checkout`, then checked out `3adc36d`. No existing
`backend/.venv`, `frontend/node_modules`, build output, or generated fixtures
were copied. Task 2's Git LFS smudge/process was disabled for this Task 1-only
checkout; its evaluation files remain pointers. Task 1's `perf_data.zip` and
public sample are ordinary tracked files and were available in the clone.

The source was cloned locally, rather than downloading the private repository
from GitHub. Existing machine Python, package caches, and browser installations
could be reused by the installers; this was a fresh project environment, not a
fresh operating system. Verification used Windows, Python **3.12.8**, uv
**0.11.0**, Node **24.15.0**, and npm **11.12.1**.

| Command / check in the new clone                                                                    | Result                                                                                                                                          |
| --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `uv sync --locked` in backend                                                                       | Passed; created a new virtual environment and installed the locked project and dependencies                                                     |
| `npm ci` in frontend                                                                                | Passed; installed 77 packages; reported one high-severity dependency advisory, detailed below                                                   |
| `npm run build`                                                                                     | Passed; TypeScript check and Vite production build completed                                                                                    |
| `uv run pytest`                                                                                     | **56 passed**; four existing dependency deprecation warnings                                                                                    |
| `uv run ruff check .`                                                                               | Passed                                                                                                                                          |
| `uv run ruff format --check .`                                                                      | Passed; 29 files already formatted                                                                                                              |
| `uv run mypy`                                                                                       | Passed; 24 source files checked                                                                                                                 |
| `npx playwright install chromium`                                                                   | Passed with normal host permissions; required browser was available                                                                             |
| `npm run test:e2e:built`                                                                            | **32 passed**, 0 skipped; built frontend and real API, fresh generated fixtures, A/L uploads, both audiences, recovery, keyboard and axe states |
| Exact README backend launch command on port 8000                                                    | Started successfully; `/health` and `/docs` both HTTP 200                                                                                       |
| Exact README frontend launch command on port 5173                                                   | Started successfully; `/` HTTP 200                                                                                                              |
| Two supplied A/C workbooks uploaded through the Vite `/api` proxy                                   | HTTP 200; both sweeps returned in the comparison response                                                                                       |
| README scenario: 10,000 input, 333 output, 50% cache; 400,000 capacity, 1,200 generation, 10ms TTFT | A **GO**, selected batch 20; C **NO GO**, representative batch 10                                                                               |
| Engineering through the same development proxy                                                      | HTTP 200 with all eight supplied A/C configurations                                                                                             |

The development smoke used HTTP requests, not a new manual UI audit. The 32
browser journeys exercised the compiled UI separately on preview port 4174 and
API port 8018. These local checks do not re-establish production hosting;
[issue #11 evidence](vercel-deployment.md) records that verification.

The restricted Windows execution sandbox initially prevented Git helper
processes, uv cache writes, Vite file resolution, and browser-download DNS.
The same commands succeeded with normal host permissions. No application code
or dependency versions were changed to work around those restrictions.

## Reproducible analysis checks

The analysis script reads all 77 source workbooks through the installed parser,
checks matching model/configuration keys, and records 275 normalized rows.
Each model has 25 matched configurations; the seven profile definitions match
across all eleven models. The supplied archive SHA-256 is:

```text
3ac805477fa4f0308bfd259707f340241a41937807b9caa8a232db9f5ae2a7e7
```

Generated [CSV](data/task1-projections.csv) and [JSON](data/task1-summary.json)
include the observed metrics and the derived values used by the documentation.
Running the script again with the fresh clone's installed environment reproduced
both files byte-for-byte. All relative links in the changed documentation were
checked against the filesystem, and the script passed Ruff lint/format checks.
The source's contiguous Summary data rows make `normalized index + 3` an Excel
row reference for these workbooks. The application itself exposes normalized
record references, not worksheet row provenance for arbitrary uploads.

## Remaining maintenance finding

`npm audit --json` reported one high-severity transitive advisory for
`source-map-js` **1.2.1**:
[GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q), concerning
event-loop denial of service from indexed source-map section offsets. The
reported affected range is below 1.2.2. Dependency maintenance should update
the lockfile and rerun the build/browser checks. This documentation task leaves
the locked dependencies unchanged and does not claim a clean security audit.

Actual 200% zoom and a screen-reader audit remain outside the existing
accessibility evidence. The five-minute recorded walkthrough and final
submission/access checks belong to later issues.
