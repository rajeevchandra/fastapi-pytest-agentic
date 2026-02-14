# FastAPI + Pytest + Coverage + Agentic Workflow (GitHub-ready)

This repo is a minimal working example that supports:

- FastAPI app (`/health`, `/items`)
- pytest tests using FastAPI TestClient
- Coverage reporting via `pytest-cov`
- Standard GitHub Actions CI (`tests.yml`)
- **GitHub Agentic Workflows** example (`coverage-agent.md`) that can draft PRs to improve coverage (guardrails via safe-outputs)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

## Run tests + coverage

```bash
pytest
```

This will generate `coverage.xml` (not committed).

## Standard CI

GitHub Actions workflow: `.github/workflows/tests.yml`

## Agentic Coverage Improver (Optional)

Prereqs:
- Install the `gh-aw` extension
- Add ONE provider secret in repo settings (e.g., `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `COPILOT_GITHUB_TOKEN`)
- Compile the markdown workflow into a locked GitHub Actions workflow

Commands:

```bash
gh extension install github/gh-aw
gh aw init
gh aw compile
git add .
git commit -m "Enable agentic coverage workflow"
git push
```

The agentic workflow is: `.github/workflows/coverage-agent.md`

First run creates a plan discussion. Next runs add tests and open a **draft PR** with before/after coverage numbers.
