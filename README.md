# MED13 Resource Library (Phase 0)

Python-based FastAPI service that powers the MED13 Resource Library. The project targets Google Cloud Run with Cloud SQL (PostgreSQL) and uses GitHub Actions for CI/CD.

## Getting Started

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API locally:
   ```bash
   uvicorn main:app --reload
   ```

## Testing

```bash
pytest
```

## Deployment

The `.github/workflows/deploy.yml` workflow runs tests, performs a dependency security audit, and deploys to Cloud Run on merged pull requests (staging) or published releases (production). Cloud Run source deployments expect a `Procfile` entry pointing to `main:app`.

Refer to `docs/infra.md` for detailed infrastructure guidance.
