# FastAPI + Pytest + Coverage + Agentic Workflow

This project demonstrates a complete loop:

- FastAPI API app (`/health`, `/items`)
- Pytest tests using `TestClient`
- Coverage reporting with `pytest-cov`
- Standard CI workflow for every push/PR
- Optional agentic workflow that proposes test-only coverage improvements via draft PRs

## What is inside

- API code: `app/main.py`, `app/api.py`
- Tests: `tests/test_health.py`, `tests/test_items.py`
- Pytest + coverage config: `pyproject.toml`
- Standard CI: `.github/workflows/tests.yml`
- Agentic source workflow (editable): `.github/workflows/coverage-agent.md`
- Compiled/locked workflow (runs in Actions): `.github/workflows/coverage-agent.lock.yml`
- Optional reusable coverage action: `.github/actions/daily-test-improver/coverage-steps/action.yml`

## How it works

### 1) API behavior

- `GET /health` returns `{"status": "ok"}`
- `POST /items` accepts `{name, price}` and rejects non-positive price with `400`
- `GET /items/{item_id}` returns data for `1`; otherwise `404`

### 2) Tests and coverage

- `pytest` runs tests in `tests/`
- Coverage tracks the `app` package and writes `coverage.xml`
- `--cov-fail-under=85` in `pyproject.toml` fails the run if total coverage drops below 85%

### 3) Standard CI workflow

`.github/workflows/tests.yml` runs on `push` and `pull_request`:

1. Checkout
2. Setup Python 3.11
3. Install dependencies
4. Run `pytest`
5. Upload `coverage.xml` artifact

### 4) Agentic workflow flow

You edit `.github/workflows/coverage-agent.md`, then compile it with `gh aw compile`.
That generates `.github/workflows/coverage-agent.lock.yml` (the executable workflow).

At runtime, the agentic workflow:

1. Runs tests and collects coverage
2. On first run, creates a coverage plan issue
3. On later runs, adds focused tests for low-coverage areas
4. Opens a **draft PR** with coverage before/after

Guardrails are enforced via safe outputs (issue/comment/draft-PR limits).

## Run locally

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### macOS/Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Health endpoint: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs

Run tests + coverage:

```bash
pytest
```

## Enable agentic workflow on GitHub (optional)

1. Add one repo secret in **Settings → Secrets and variables → Actions**:
	- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `COPILOT_GITHUB_TOKEN`
2. Install GitHub CLI and `gh-aw`
3. Compile and push

```bash
gh extension install github/gh-aw
gh aw init
gh aw compile
git add .
git commit -m "Compile agentic workflow"
git push
```

Then open **Actions** and run **AI Coverage Improver** manually (or wait for the schedule).
