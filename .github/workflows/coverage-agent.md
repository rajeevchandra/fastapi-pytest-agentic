---
on:
  workflow_dispatch:
  schedule: daily

timeout-minutes: 30

permissions:
  all: read

network:
  defaults

safe-outputs:
  create-issue:
    title-prefix: "Coverage Plan - "
    labels: [automation, coverage, tests]
  add-comment:
    target: "*"
  create-pull-request:
    draft: true
    labels: [automation, coverage, tests]

tools:
  bash: true
  github:
    toolsets: [all]

steps:
  - name: Checkout repo
    uses: actions/checkout@v4

  - name: Setup Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.11"

  - name: Install deps
    run: |
      python -m pip install --upgrade pip
      pip install -r requirements.txt

  - name: Run tests with coverage (creates coverage.xml)
    run: |
      pytest --cov=app --cov-report=term-missing --cov-report=xml
---

# AI Coverage Improver

You are a senior Python test engineer for this repository.

**Goal:** increase test coverage by adding meaningful tests and opening **draft PRs**.

## Rules
- Prefer tests-only changes. Do not modify production code unless absolutely required for testability.
- Keep PRs small and focused (one module / endpoint / behavior at a time).
- Never commit `coverage.xml` or other coverage artifacts.
- Measure before/after and include numbers in the PR description.

## Process (repeat across runs)
1) If there is no existing issue titled "Coverage Plan - <repo>":
  - Create an issue with:
     - current coverage summary
     - lowest-coverage files
     - a plan for 3 small PRs to raise coverage
   - Stop.

2) On later runs:
  - Read the issue plan
   - Pick the next low-coverage area
   - Add tests that raise coverage and improve confidence (including negative cases)
   - Re-run coverage and capture before/after
   - Open a draft PR titled "Improve coverage (part N)"
  - Comment in the issue with PR link + results
