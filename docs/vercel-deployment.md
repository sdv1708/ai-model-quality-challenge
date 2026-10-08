# Task 1 on Vercel Services

Production: <https://ai-model-quality-challenge-rho.vercel.app>
Vercel project: `sdv1708s-projects/ai-model-quality-challenge` (Hobby).

The repository-root `vercel.json` defines one project with two independently
built services. Use the repository root as the Vercel project Root Directory,
not `frontend/` or `backend/`.

| Service    | Root       | Framework | Public paths                                                 |
| ---------- | ---------- | --------- | ------------------------------------------------------------ |
| `backend`  | `backend`  | FastAPI   | `/api/*`, `/health`                                          |
| `frontend` | `frontend` | Vite      | All remaining paths, including `/`, `/assets/*`, `/sample/*` |

The backend entrypoint is `src.perf_api.main:app`. The frontend installs with
`npm ci`, builds with `npm run build`, and publishes `dist/`. Build settings live
on each service, while public rewrites live at the top level.

## Routing and bindings

Vercel passes the original request path to each service. `/api/v1/...` therefore
matches the existing FastAPI router prefixes without stripping or adding `/api`.
The final catch-all routes all remaining traffic to the frontend. Unknown API
routes return the backend's 404 rather than the frontend's HTML.

The browser calls same-origin `/api/v1/...` URLs. The frontend is a static SPA,
and the backend does not call other services. There are no function-to-function
calls requiring bindings, and no service is internal-only in this configuration.
Do not add a runtime binding URL to the static bundle or manually define a
binding environment variable. If a future server-side caller is added, declare
its binding on that calling service and read the generated URL inside a function.

`/health` is public for smoke checks. FastAPI's `/docs`, `/redoc`, and
`/openapi.json` are available through the standalone local API; the shared-domain
configuration does not expose those paths to the backend.

## Local verification

Prerequisites: Node.js 20 or newer, Python 3.12, `uv`, and a current Vercel CLI
with Services support. Verification used CLI 63.1.0.

Install dependencies once:

```powershell
cd backend
uv sync --locked
cd ../frontend
npm ci
cd ..
```

Run both services with the public routing configuration:

```powershell
vercel dev --local --listen 3000
```

`--local` runs without linking or authenticating to Vercel Cloud. A linked
project can instead use `vercel dev`. Open <http://localhost:3000> and perform
the smoke checks below using that origin. Standalone `npm run dev` still uses
the Vite localhost proxy, but it does not validate the Vercel service rewrites.

On Windows, CLI 63.1.0 can fail when the `uv.exe` path contains spaces (such as
`C:\Users\Sanjay DV\...`). If it reports that it cannot run `uv --version`,
use an ignored temporary copy from the repository root, whose path contains
no spaces:

```powershell
$taskUvSource = (Get-Command uv).Source
$taskUvDirectory = Join-Path (Get-Location) '.vercel/tools'
New-Item -ItemType Directory -Force -Path $taskUvDirectory | Out-Null
Copy-Item -LiteralPath $taskUvSource -Destination (Join-Path $taskUvDirectory 'uv.exe')
$env:PATH = $taskUvDirectory + [IO.Path]::PathSeparator + $env:PATH
vercel dev --local --listen 3000
```

This changes PATH only for the current terminal session. It is a local CLI
workaround; production deployment does not use the copied binary.

With Vercel's server running, run the existing browser suite in another terminal:

```powershell
cd frontend
npm run test:e2e:services
```

This configuration targets port 3000 and starts no standalone Vite/API servers,
so uploads, decisions, engineering, errors, and accessibility are checked through
Vercel's real service rewrites.

To run the same checks against production without logging in:

```powershell
cd frontend
$env:PLAYWRIGHT_BASE_URL = 'https://ai-model-quality-challenge-rho.vercel.app'
npm run test:e2e:services
Remove-Item Env:PLAYWRIGHT_BASE_URL
```

Existing frontend regression checks:

```powershell
cd frontend
npm run build
npm run test:e2e:built
```

## Project settings

1. Connect the private GitHub repository to one Vercel project.
2. Keep the project Root Directory at the repository root. Let `vercel.json`
   supply the service frameworks and build settings.
3. Leave `VITE_API_BASE_URL` unset; the browser uses relative URLs. There are no
   binding variables to configure. No API keys or storage services are required.
4. Use Node.js 24.x for the frontend and the Python 3.12 requirement declared in
   the backend manifest. Keep the committed lockfiles.
5. Ensure the production URL is publicly accessible without Deployment
   Protection sign-in, as required by the challenge.
6. After service names and public routes are confirmed, deploy and record the
   verified production URL at the top of the root README and in the submission.

`.vercelignore` excludes Task 2's evaluation data and `perf_data.zip` from uploads.
The small workbook in `frontend/public/sample/` remains available to the UI.
Local dependencies and generated verification output are also excluded.

## Live smoke procedure

Use the same procedure against `vercel dev --local` and the production origin:

1. Open `/` without signing in. Check that scripts, styles, and the sample load.
2. Request `/health`; expect `200` and
   `{"status":"ok","service":"perf-api"}`.
3. Load the bundled sample. Verify comparison, customer decisions, and engineering
   diagnostics through the real API.
4. Upload one workbook, then multiple A/L fixtures. Verify model comparison and
   both audience views without rebuilding.
5. Upload an invalid workbook, then a valid one. Verify useful diagnostics and
   recovery; also exercise mixed valid/invalid multi-upload.
6. Request `/api/v1/does-not-exist`; expect a JSON 404 from FastAPI, not HTML.
7. Check the Network panel: API requests use the page's origin and retain
   `/api/v1/...`; no requests target localhost or another deployment.

Vercel Functions enforce platform request and response size limits. The 4.5 MB
payload limit applies to the entire multipart request and to JSON responses,
not independently to each workbook. Test larger batches and avoid claiming
unlimited uploads. Application-level upload limits are separate issue #11 work.

## References

- [Services](https://vercel.com/docs/services)
- [Service routing](https://vercel.com/docs/services/routing)
- [Service bindings](https://vercel.com/docs/services/bindings)
- [Configuration reference](https://vercel.com/docs/services/config-reference)
- [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi)
- [Function limits](https://vercel.com/docs/functions/limitations)
