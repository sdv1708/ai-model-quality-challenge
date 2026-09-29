# Performance Studio frontend

This React and TypeScript frontend accepts one or more local `.xlsx` workbooks or loads the bundled Model A sample. Both paths send the files to `POST /api/v1/comparisons/workbooks` under the repeated `workbooks` multipart field. The response shows matching configurations across models, coverage gaps, upload diagnostics, and one selected sweep for deeper inspection. The customer decision form sends that sweep, explicit targets, and optional assumptions to `POST /api/v1/decisions/evaluate`.

The comparison view aligns rows with the same profile, input length, output length, cache share, and batch size. Customer-facing metrics include total capacity, generation speed per user, and time to first token; engineering metrics include per-box and cache-sensitive throughput. A missing row is shown as a coverage gap, not a zero. For multiple models in one profile, the customer decision form requires a specific scenario and applies the same targets and assumptions to each model. It shows the resulting go, no-go, or needs-data verdicts side by side, with detailed evidence for the selected sweep. Empty target fields are not checked; an absent supported context window or box-hour price stays unknown when the relevant limit needs it. The hardware cost estimate assumes sustained projected capacity and is not a customer price.

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

The browser tests start both servers and cover single and multiple uploads, an unseen model name, validation recovery, customer decisions, missing cost assumptions, and a narrow viewport. Python API tests remain in `backend/`.

## Deployment configuration

The frontend builds to `frontend/dist/` using `npm run build`. By default it calls `/api/v1/comparisons/workbooks` on the same origin. For a separately deployed API, set `VITE_API_BASE_URL` to the API origin at build time and configure the API to permit the frontend origin through CORS. The current backend does not yet provide that production CORS configuration; local development uses Vite's proxy.
