# Specs Execution Assessment (2026-07-28)

## Purpose

Assess newly added spec documents for:

1. whether they are directly executable;
2. whether they should first be lightly revised;
3. whether they are execution specs or only review/insight documents.

---

## Overall Conclusion

- `docs/superpowers/specs/course/how-to-profit/specs/spec-01..07.md`:
  executable as a coherent notebook-driven learning track.
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-01..07.md`:
  not executable specs; these are critique/improvement notes for the paired specs.
- `docs/superpowers/specs/course/env-setup/spec-01-env-setup-mac.md`:
  executable, but should be lightly revised before being treated as a stable course spec.

---

## Triage

### A. Directly executable

These can be executed now with only low operational risk:

- `docs/superpowers/specs/course/how-to-profit/specs/spec-01-get-data.md`
- `docs/superpowers/specs/course/how-to-profit/specs/spec-03-benchmark.md`
- `docs/superpowers/specs/course/how-to-profit/specs/spec-04-ma-visual.md`

Why:

- clear four-part structure;
- concrete notebook tasks;
- low ambiguity in required outputs;
- limited hidden state coupling.

### B. Executable after light revision

These are basically sound, but should be tightened before formal execution:

- `docs/superpowers/specs/course/how-to-profit/specs/spec-02-dca-backtest.md`
- `docs/superpowers/specs/course/how-to-profit/specs/spec-05-ma-timing.md`
- `docs/superpowers/specs/course/how-to-profit/specs/spec-06-param-scan.md`
- `docs/superpowers/specs/course/how-to-profit/specs/spec-07-overfitting.md`
- `docs/superpowers/specs/course/env-setup/spec-01-env-setup-mac.md`

Why:

- some contracts are still implicit (index type, split boundaries, validation expectations);
- some course-critical reproducibility details should be locked down;
- environment setup spec is useful but structurally inconsistent with the rest.

### C. Do not execute directly

- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-01.md`
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-02.md`
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-03.md`
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-04.md`
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-05.md`
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-06.md`
- `docs/superpowers/specs/course/how-to-profit/insights/insight-spec-07.md`
- `docs/superpowers/specs/course/env-setup/insight-spec-01-mac.md`

Why:

- they are review/analysis artifacts;
- they explain what to improve in the paired specs;
- they are not framed as execution instructions for notebook or environment work.

---

## Minimal Revision Checklist

### 1. `spec-01-env-setup-mac.md`

Must-fix before broad use:

- lock dependency versions;
- lock `open-xquant` to a tag or commit;
- convert outer structure to `上下文 / 任务 / 要求 / 结果呈现`;
- preferably move `check_env.py` into a referenced artifact or shared script.

### 2. `spec-02-dca-backtest.md`

Light fixes:

- state the returned index type explicitly;
- add 1-2 validation assertions for result shape and cumulative cost;
- tighten formatting expectations for printed outputs.

### 3. `spec-05-ma-timing.md`

Light fixes:

- rewrite the zero-cost return handling in a more direct, executable way;
- clarify that no-signal months keep shares/cost unchanged;
- optionally specify expected `signal` column semantics more explicitly.

### 4. `spec-06-param-scan.md`

Light fixes:

- add a small validation contract (`24` params scanned, best parameter in range);
- optionally make the scan result structure explicit (`scan_df`);
- preserve the current “don’t reveal the overfitting twist too early” teaching intent.

### 5. `spec-07-overfitting.md`

Must-fix before formal execution:

- make train/test split boundary unambiguous;
- require non-overlapping time slices;
- add simple leakage-prevention assertions;
- keep the current 60/40 narrative, but encode it more precisely.

---

## Recommended Execution Order

### Track 1: spec polishing

1. revise `spec-01-env-setup-mac.md`
2. revise `spec-02`, `spec-05`, `spec-06`, `spec-07`
3. keep insight docs as design notes, not runnable inputs

### Track 2: notebook execution

After the light revisions above:

1. `spec-01-get-data`
2. `spec-02-dca-backtest`
3. `spec-03-benchmark`
4. `spec-04-ma-visual`
5. `spec-05-ma-timing`
6. `spec-06-param-scan`
7. `spec-07-overfitting`

---

## Recommendation

Best next move:

- treat `how-to-profit/spec-01..07` as a separate notebook subproject;
- do one light spec-tightening pass first;
- then execute them in order as a clean teaching/demo workflow.

Do not mix this notebook track directly into the current `ai_xquanty` package implementation flow without an explicit decision to do so.
