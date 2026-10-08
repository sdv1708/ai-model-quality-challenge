# Performance Studio frontend

This React and TypeScript frontend accepts one or more local `.xlsx` workbooks or loads the bundled Model A sample. Both paths send the files to `POST /api/v1/comparisons/workbooks` under the repeated `workbooks` multipart field. The response shows matching configurations across models, coverage gaps, upload diagnostics, and one selected sweep for deeper inspection. The customer decision form sends that sweep, explicit targets, and optional assumptions to `POST /api/v1/decisions/evaluate`.

The comparison view aligns rows with the same profile, input length, output length, cache share, and batch size. Customer-facing metrics include total capacity, generation speed per user, and time to first token; engineering metrics include per-box and cache-sensitive throughput. A missing row is shown as a coverage gap, not a zero. For multiple models in one profile, the customer decision form requires a specific scenario and applies the same targets and assumptions to each model. It shows the resulting go, no-go, or needs-data verdicts side by side, with detailed evidence for the selected sweep. Empty target fields are not checked; an absent supported context window or box-hour price stays unknown when the relevant limit needs it. The hardware cost estimate assumes sustained projected capacity and is not a customer price.

The engineering view sends every normalized workbook to `POST /api/v1/engineering/analyze`. Select a sweep and configuration to inspect sourced aggregate, per-box, cached, uncached, latency, and speed metrics. Controlled batch and cache trends come from the API; when a matching pair is absent, the view says so. Review flags link to the normalized rows and rule explanations that produced them. The row number is an index in normalized records, not an Excel sheet row. The view keeps the API's analysis limitations visible in an expandable section. A failed engineering request leaves the customer and comparison flows available.

## Prerequisites

- Node.js 20 or newer
- Python 3.12 and [uv](https://docs.astral.sh/uv/) for the backend

## Run locally

Start the API in one terminal:

```powershell
cd backend
uv sync
uv run uvicorn perf_api.main:app --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to `http://127.0.0.1:8000`, so local uploads use the real backend. The sample workbook is served from `frontend/public/sample/` and goes through the same upload API as a local file.

## Verify

```powershell
cd frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

The browser tests start both servers and cover single and multiple uploads, an unseen model name, validation recovery, customer decisions, engineering trends and flag evidence, missing cost assumptions, and a narrow viewport. Python API tests remain in `backend/`.

## Built-frontend verification (Issue #10)

```powershell
npm run build
npm run test:e2e:built
```

Playwright generates fresh synthetic A/L workbooks and malformed variants using
the backend virtual environment's openpyxl installation. This browser-only
factory is independent of the learner's backend fixtures. Global setup also
exports those backend fixtures and a dedicated browser journey uploads their
exact bytes. Tests verify exact
metrics, different customer verdicts, engineering source rows, error recovery,
mixed-batch warnings, keyboard navigation, contained table scrolling at
390px/640px, and axe scans across six rendered states. Generated files stay in
`tests/fixtures/browser-generated/`, outside public assets. The built suite uses
preview port 4174 and API port 8018 with a same-origin proxy. The built-suite
server runs `prepreview:e2e` to rebuild dist before preview starts, so the
separate build command above is optional for this suite.

## Deployment configuration

The frontend builds to `frontend/dist/` using `npm run build`. Its browser code
calls `/api/v1/...` on the same origin. The root `vercel.json` deploys it alongside
the FastAPI backend as two services in one Vercel project. Vercel routes API
requests to the backend and assets, samples, and page requests to the frontend.
Standalone Vite development and preview use `VITE_DEV_API_TARGET` for their local
proxy; it defaults to `http://127.0.0.1:8000`.

No frontend function calls the backend, so there is no service binding. Runtime
binding URLs cannot be used in this static browser bundle. `VITE_API_BASE_URL`
is no longer used; remove any previously configured value from Vercel settings.
See [`../docs/vercel-deployment.md`](../docs/vercel-deployment.md) for the
`vercel dev --local` workflow and production smoke checks.

With `vercel dev --local --listen 3000` running from the repository root, run
`npm run test:e2e:services` in this directory to exercise the existing browser
suite through Vercel's service routing instead of Vite's standalone proxy.
