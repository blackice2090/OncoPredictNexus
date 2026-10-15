# Deployment and browser-private records

## Runtime

- **Frontend:** React with Vite, built as static assets and served by Vercel.
- **API:** FastAPI ASGI application in `api/index.py`, running in a Python function.
- **Model:** the original verified Ridge artifact with matching pinned statistical libraries.
- **History:** up to 30 records in this browser's local storage. No database or storage credential is required.

The public entrypoint sets `public_demo=True`. It never creates the local run directory, never writes visitor records to it, and returns 404 for server-side `/runs` routes. Prediction profiles are transmitted to the API for calculation. Application code does not persist them on the server. Infrastructure operators may still maintain normal access and operational logs.

The frontend saves the result in browser storage before presenting it as saved. It handles history and report/CSV/JSON export locally. Each saved record includes its frozen model metadata and source fingerprints. Another browser, browser profile, origin or device does not receive that history.

## Local setup

Use Python 3.12 and Node.js 24. From the repository root:

```bash
python -m venv .venv
# Activate .venv for your shell.
python -m pip install -r requirements.txt
npm run setup
npm run build
python -m uvicorn api.index:app --host 127.0.0.1 --port 8766
```

Open `http://127.0.0.1:8766/`. The build must exist before opening the interface.

The older `python -m app.research_predictor.api` entrypoint retains optional local-file development behavior for reproducibility. **Use `api.index:app` for the browser-private public mode.** Do not expose the file-backed development mode as a public multiuser service.

## Vercel configuration

Import `blackice2090/OncoPredictNexus` with the repository root as Root Directory. The checked-in `vercel.json` defines:

| Setting | Value |
| --- | --- |
| Framework override | Other / `null` |
| Install command | `npm ci --prefix app/research_predictor/frontend` |
| Build command | `npm run build --prefix app/research_predictor/frontend` |
| Output directory | `app/research_predictor/frontend/dist` |
| Python entrypoint | `api/index.py` |
| Python version | 3.12 |

The API assets are included in the function bundle. Notebooks, documentation screenshots, test files, dependency directories and local records are excluded from deployment. Vercel installs the Python runtime dependencies from root `requirements.txt`.

Standard deployment, branch and production hostnames are read from Vercel's environment. For a custom hostname, set `ONCOPREDICT_ALLOWED_HOSTS`, for example `research.example.org`. Do not include a scheme or path. Cross-origin prediction POST requests are rejected.

```bash
npx vercel link --project oncopredictnexus
npx vercel deploy
# After checking the preview:
npx vercel deploy --prod
```

Link the repository through Vercel's Git settings to enable builds from future pushes. A CLI deployment alone does not imply that Git integration has been configured.

## Acceptance checks

1. `/health` reports `ready` and the frozen model version.
2. Load the documented TCGA example or synthetic demo and calculate all three estimates.
3. Check that base value plus all eight SHAP contributions equals each LN_IC50 output.
4. Reload the page and reopen the saved experiment from this browser's history.
5. Open a separate browser context and verify its history is empty.
6. Verify `/runs` and `/runs/<id>` return 404 in public mode.
7. Export JSON and CSV and open the printable report. Numeric values must match the displayed result, including provenance and limitations.
8. Switch between English and Arabic without changing inputs or scientific values.

## Boundaries

Browser storage is local and unencrypted. Clearing site data removes saved experiments. Export results that need to be retained. A serverless deployment does not provide a central archive, account system, shared history, cross-device synchronization or clinical data storage.

This hosting configuration does not retrain the model, modify scientific metrics, validate patient-level use, or establish sensitive/resistant thresholds.
