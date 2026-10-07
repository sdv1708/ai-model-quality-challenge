# Issue #10 verification evidence

Status: **Backend/frontend automation and an interactive browser keyboard pass verified.**
All frontend work is assistant-owned. The learner's completed backend guide is
`../backend/ISSUE_10_BACKEND_GUIDE.md`. The interactive keyboard pass below was
agent-driven in the Codex in-app browser on Windows. Keyboard selection inside
the native OS file dialog and actual 200% browser zoom remain unverified.

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
- `npm run test:e2e:built`: **31 passed, 0 skipped**. Preview 4174, real API 8018.
  The managed server rebuilds dist before starting preview. A deliberately
  invalid inherited API URL (`http://127.0.0.1:9`) was overridden successfully;
  the original 28 browser tests still used the managed local API. After the
  interactive audit found focus loss during requests, the expanded 31-test suite
  passed with focus restoration, failure recovery, and no focus stealing covered.
- `npm run format:check`: passed after frontend edits.

## Acceptance evidence

| Requirement | Test or manual evidence | Result / remaining gap |
|---|---|---|
| Fresh Model L, no application edits | Both fixture factories, exact API/UI values, engineering source rows | Passed |
| Multi-upload through built frontend + real backend | `resilience.spec.ts`, compiled dist through real API | Passed |
| Recoverable malformed-input errors | Missing header, invalid number, empty table, corrupt archive; valid-invalid-valid; mixed batch; connection failure | Passed |
| Comparison + customer + engineering journeys | Distinct metrics/verdicts, normalized L source row 2 | Passed |
| Automated accessibility + manual keyboard | Six axe states, regression tests, and the interactive keyboard observations below | Passed within the documented browser scope |

## Manual keyboard and responsive pass

On 2026-10-07 the assistant navigated and activated the app interactively using
Tab, Shift+Tab, Enter, and arrow keys, observing browser focus and screenshots
between actions. These observations supplement the scripted Playwright suite;
they are not a human audit or screen-reader certification. Enter opened the
file chooser, and the browser's chooser API supplied generated test files.
The 390px/640px layout checks are not a substitute for actual browser zoom.

| Step | Observation and pass/fail |
|---|---|
| Tab from page start; Shift+Tab reverses order; focus stays visible | Passed: home → upload input → sample; reverse returns to upload. Visible outlines observed. |
| Reach file input and sample button; activate with native keyboard behavior | Passed in app: Enter loads sample and opens the multi-file chooser. Focus returns to the initiating control after loading. |
| Upload fresh A+L; navigate comparison controls and inspect L | Passed: chooser supplied A+L; Tab reached profile/configuration selectors and both tables; Down selected batch 20 and Model L. |
| Enter customer targets; submit; reach verdict and its evidence | Passed: selected workload, typed 450, tabbed through all target/assumption fields and submitted with Enter. A NO GO / L GO appeared; submit retained visible focus. |
| Reach engineering link, sweep/row selectors and expandable assumptions | Passed: Enter on engineering link reached its section; next Tab reached sweep selector. Selected L/row 2 and expanded assumptions with Enter. |
| Upload malformed file; find understandable error; controls remain reachable | Passed: missing-column.xlsx reported missing Batch Size; upload remained focused; sample and Dismiss error remained reachable with Tab. |
| Upload valid L again without reloading; inspect new results | Passed: same picker loaded L, error disappeared, normalized row 2 showed L metrics 800 total / 80 per box. |
| At 390px width, reach all controls and scroll wide tables inside their containers | Passed: complete Tab cycle reached all controls. All five table regions had solid focus outlines and ArrowRight advanced scrollLeft by 40px. Page width 375px within 390px viewport. |
| Supplemental: keyboard selection inside Windows file dialog | Unverified: files were supplied through the browser chooser API. |
| Supplemental: actual 200% browser zoom | Unverified: in-app browser ignored Ctrl+Plus; viewport width/devicePixelRatio stayed 968px/1. |

## Findings and resolution

- Fixed low-contrast muted/green text; all six WCAG-tagged axe state scans pass.
- Fixed engineering definition-list structure: metric explanations now sit in dd.
- Added named, keyboard-focusable table scroll regions with visible focus outlines;
  ArrowRight scrolling passes at both tested widths.
- Fixed substring model-heading locators in existing upload tests to use exact names.
- Fixed the backend factory's unsupported `values=` keyword to `value=`.
- Fixed missing-header mutation to assign `.value = None`, genuinely clearing it.
- Explicit response/case annotations, narrow import ignores and formatting pass.
- Interactive audit found that disabling controls during upload/customer requests
  dropped focus to the document body. Added `usePendingFocus` to restore the
  initiating control after React re-enables it, without moving focus if the user
  navigated elsewhere. Success/failure and non-stealing regression checks pass.
- Backend assertions and the scoped interactive keyboard pass now pass.
  Local preview does not establish public hosting or separately hosted API/CORS
  correctness; issue #11 does.
