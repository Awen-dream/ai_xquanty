# Q2 Live Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dual-mode `q2-what-to-buy` notebook that preserves the fixed teaching walkthrough and can also run an out-of-sample validation ending on a configurable date, defaulting to July 29, 2026.

**Architecture:** Keep the existing three-step teaching notebook unchanged in meaning, then append a separate Step 4 for out-of-sample validation. Put all mode/date/freshness controls in one top-level config block so teaching behavior stays deterministic and validation behavior is explicit about stale data fallback.

**Tech Stack:** Jupyter notebook JSON, pytest, open-xquant/oxq local cache, pandas

## Global Constraints

- Preserve the current teaching window and reference results for Steps 1-3.
- Add `NOTEBOOK_MODE = "teaching" | "live_validation"` with `teaching` as the default.
- Add `VALIDATION_END = "2026-07-29"` as the default validation cutoff.
- Add `FRESHNESS_POLICY = "strict" | "allow_stale"`.
- In `strict`, do not report validation results unless cached/downloaded data covers `VALIDATION_END`.
- In `allow_stale`, print that the validation result is stale and include the actual data end date.
- Keep user-facing framework naming as `open-xquant`; do not rename `oxq` imports.

---

### Task 1: Protect the Notebook Contract with Tests

**Files:**
- Modify: `tests/notebooks/test_q2_notebook.py`

**Interfaces:**
- Consumes: `docs/superpowers/specs/course/q2-what-to-buy/notebooks/q2-what-to-buy.ipynb`
- Produces: regression tests that assert the config block and Step 4 validation logic are present

- [ ] Add a failing test asserting the notebook contains `NOTEBOOK_MODE`, `VALIDATION_END`, and `FRESHNESS_POLICY`.
- [ ] Run `./.venv/bin/python -m pytest tests/notebooks/test_q2_notebook.py -q` and confirm it fails for the new test.
- [ ] Add a failing test asserting the notebook includes a live-validation section with strict/stale handling markers.
- [ ] Re-run the same pytest command and confirm the new assertions still fail.

### Task 2: Add Dual-Mode Live Validation to the Notebook

**Files:**
- Modify: `docs/superpowers/specs/course/q2-what-to-buy/notebooks/q2-what-to-buy.ipynb`

**Interfaces:**
- Consumes: existing `refresh_yfinance`, `provider`, and the Step 3 ETF symbols `510300.SS`, `513100.SS`, `518880.SS`
- Produces: top-level config variables plus a new Step 4 code cell that compares single-asset CSI 300 vs equal-weight three-asset validation results

- [ ] Insert a top-level config block defining notebook mode, validation end date, and freshness policy.
- [ ] Append a markdown section for Step 4 explaining that this is an out-of-sample validation ending on `VALIDATION_END`.
- [ ] Append a code cell that fetches or reuses ETF data, checks the actual last bar date, and either raises in `strict` mode or prints a stale-data warning in `allow_stale`.
- [ ] In the same code cell, compute validation-period metrics for `510300.SS` and the equal-weight `510300.SS/513100.SS/518880.SS` basket, then print a compact comparison table.

### Task 3: Verify End-to-End Notebook Behavior

**Files:**
- Modify: `tests/notebooks/test_q2_notebook.py` if any assertions need tightening after implementation

**Interfaces:**
- Consumes: updated notebook and notebook regression tests
- Produces: fresh verification evidence that the notebook contract and live-validation mode are consistent

- [ ] Run `./.venv/bin/python -m pytest tests/notebooks/test_q2_notebook.py -q` and confirm all tests pass.
- [ ] Run a notebook smoke execution with local cache enabled to confirm the new Step 4 cell executes.
- [ ] Check that teaching cells still print the original fixed-window conclusions and that Step 4 reports either strict freshness success or an explicit stale-data warning.
