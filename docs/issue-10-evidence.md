# Issue #10 verification evidence

Status: **Backend and frontend automation verified.**
All frontend work is assistant-owned. The learner's completed backend guide is
`../backend/ISSUE_10_BACKEND_GUIDE.md`. Manual OS-dialog/zoom audit remains separate
from automated keyboard evidence and is not claimed complete here.

## Reproduction details

- Tested branch changes: `feature/issue-10-resilience`, based on `b78c1e6`.
- Test date/browser/OS: 2026-10-07, Playwright Chromium on Windows.
- Browser fixture generation: Playwright global setup runs its independent
  `generate_browser_fixtures.py` using backend/.venv Python/openpyxl; succeeds.
- Browser values: shared input/output 100/100, cache 0.5, batches 10/20.
  A capacity 260/400; L capacity 520/800; L per-box 52/80; target capacity 450
  yields A NO GO and L GO. Backend fixtures share input/output 1024/128, cache
  0.5, batches 1/2; A capacity 1000/1800, L capacity 1500/2700. Targets capacity
  2000, generation speed 50, maximum TTFT 250 produce A NO GO and L GO at batch 2.
  A dedicated browser journey uploads these exported backend fixture bytes and
  checks the exact values and sourced engineering metrics.
- `npm run build`: passed; same-origin API routing used.
- Backend: **56 passed, 0 skipped** (eight issue #10 cases). Ruff lint/format and
  strict mypy pass. Existing dependency deprecation warnings remain. Pytest's
  cache-writing warning is an execution permission limitation, not a test failure.
- `npm run test:e2e:built`: **28 passed, 0 skipped**. Preview 4174, real API 8018.
  The managed server rebuilds dist before starting preview. A deliberately
  invalid inherited API URL (`http://127.0.0.1:9`) was overridden successfully;
  all browser tests still used the managed local API.
- `npm run format:check`: passed after frontend edits.

## Acceptance evidence

| Requirement | Test or manual evidence | Result / remaining gap |
|---|---|---|
| Fresh Model L, no application edits | Both fixture factories, exact API/UI values, engineering source rows | Passed |
| Multi-upload through built frontend + real backend | `resilience.spec.ts`, compiled dist through real API | Passed |
| Recoverable malformed-input errors | Missing header, invalid number, empty table, corrupt archive; valid-invalid-valid; mixed batch; connection failure | Passed |
| Comparison + customer + engineering journeys | Distinct metrics/verdicts, normalized L source row 2 | Passed |
| Automated accessibility + manual keyboard | Six axe states and real Tab/Shift+Tab/Enter browser test | Automation passed; full manual audit not claimed |

## Manual keyboard and responsive pass

Automated evidence already covers actual Tab/Shift+Tab order through upload and
audience links, visible upload focus, keyboard sample activation, and arrow-key
scrolling for all five tables at 390px/640px. This is distinct from the remaining
manual OS file-dialog and actual 200% browser zoom observations below. The 640px
viewport exercises a narrow layout but is not a claim about actual browser zoom.

Perform these steps without using the mouse to navigate/activate controls. Native
OS file dialogs may be used through their keyboard controls. Record each result,
what received focus, and any defect. Automation using `.focus()` is useful but
does not prove the real Tab sequence.

| Step | Observation and pass/fail |
|---|---|
| Tab from page start; Shift+Tab reverses order; focus stays visible | TODO |
| Reach file input and sample button; activate with native keyboard behavior | TODO |
| Upload fresh A+L; navigate comparison controls and inspect L | TODO |
| Enter customer targets; submit; reach verdict and its evidence | TODO |
| Reach engineering link, sweep/row selectors and expandable assumptions | TODO |
| Upload malformed file; find understandable error; controls remain reachable | TODO |
| Upload valid L again without reloading; inspect new results | TODO |
| At 390px width, reach all controls and scroll wide tables inside their containers | TODO |
| At 200% browser zoom, repeat navigation; no lost controls or focus traps | TODO |

## Findings and resolution

- Fixed low-contrast muted/green text; all six WCAG-tagged axe state scans pass.
- Fixed engineering definition-list structure: metric explanations now sit in dd.
- Added named, keyboard-focusable table scroll regions with visible focus outlines;
  ArrowRight scrolling passes at both tested widths.
- Fixed substring model-heading locators in existing upload tests to use exact names.
- Fixed the backend factory's unsupported `values=` keyword to `value=`.
- Fixed missing-header mutation to assign `.value = None`, genuinely clearing it.
- Explicit response/case annotations, narrow import ignores and formatting pass.
- Backend assertions now pass; manual audit observations remain pending.
  Local preview does not establish public hosting or separately hosted API/CORS
  correctness; issue #11 does.
