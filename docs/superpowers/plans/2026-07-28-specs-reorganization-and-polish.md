# Specs Reorganization And Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the new course/project spec assets into a clearer directory structure and lightly tighten the agreed spec files without changing their teaching intent.

**Architecture:** Treat the work as documentation infrastructure, not product-code work. First separate project specs from course specs, then separate runnable course specs from insight/review notes, then apply minimal edits only to the agreed target specs so execution clarity improves while scope and pedagogy stay unchanged.

**Tech Stack:** Markdown, git-aware file moves, repository documentation conventions

## Global Constraints

- 不修改 `tests/data/test_loaders.py` 这份已有未提交改动
- 只做目录重排与轻修，不改教学意图、不扩展范围
- `insight` 文档只作为修订依据，不作为执行 spec
- 保持 `how-to-profit/spec-01..07` 作为一条可顺序执行的 notebook 教学链
- 仅补可复现性、边界清晰度、可执行性，不重写整套课程内容

---

### Task 1: Reorganize The Spec Directories

**Files:**
- Create: `docs/superpowers/specs/project/ai_xquanty/`
- Create: `docs/superpowers/specs/course/env-setup/`
- Create: `docs/superpowers/specs/course/how-to-profit/specs/`
- Create: `docs/superpowers/specs/course/how-to-profit/insights/`
- Move: `docs/superpowers/specs/2026-07-26-a-share-core-satellite-quant-design.md`
- Move: `docs/superpowers/specs/2026-07-28-spec-execution-assessment.md`
- Move: `docs/superpowers/specs/spec-01-env-setup-mac.md`
- Move: `docs/superpowers/specs/insight-spec-01-mac.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-01-get-data.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-02-dca-backtest.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-03-benchmark.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-04-ma-visual.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-05-ma-timing.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-06-param-scan.md`
- Move: `docs/superpowers/specs/how-to-profit/spec-07-overfitting.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-01.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-02.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-03.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-04.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-05.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-06.md`
- Move: `docs/superpowers/specs/how-to-profit/insight-spec-07.md`

**Interfaces:**
- Consumes: existing `docs/superpowers/specs/` files
- Produces: grouped `project/` and `course/` spec directories with separate runnable-spec and insight folders

- [ ] **Step 1: Create the target directories**

Run:
`mkdir -p docs/superpowers/specs/project/ai_xquanty docs/superpowers/specs/course/env-setup docs/superpowers/specs/course/how-to-profit/specs docs/superpowers/specs/course/how-to-profit/insights`

Expected: directories exist with no content changes yet

- [ ] **Step 2: Move project and course files into the new layout**

Run git-aware move commands for each file so history follows the move.

Expected: no spec content changes yet, only new paths

- [ ] **Step 3: Verify the new directory tree**

Run:
`find docs/superpowers/specs -maxdepth 4 -type f | sort`

Expected: project specs under `project/ai_xquanty/`, runnable course specs under `course/.../specs/`, and review notes under `course/.../insights/`

### Task 2: Lightly Tighten The Environment Setup Spec

**Files:**
- Modify: `docs/superpowers/specs/course/env-setup/spec-01-env-setup-mac.md`

**Interfaces:**
- Consumes: current mac environment setup spec plus the agreed revision scope
- Produces: a still-runnable course environment spec with clearer structure and better reproducibility

- [ ] **Step 1: Rewrite the outer structure to `上下文 / 任务 / 要求 / 结果呈现`**

The existing step-by-step body stays, but the top-level structure becomes consistent with the rest of the course specs.

- [ ] **Step 2: Lock dependency versions and the `open-xquant` install target**

Use concrete versions or a concrete tag/commit to improve reproducibility.

- [ ] **Step 3: Keep the check script workflow but tighten expectations**

Preserve the validation-script approach while making expected outputs and success conditions clearer.

- [ ] **Step 4: Review for scope creep**

Expected: still only environment setup, no expansion into unrelated onboarding content

### Task 3: Lightly Tighten The Agreed How-To-Profit Specs

**Files:**
- Modify: `docs/superpowers/specs/course/how-to-profit/specs/spec-02-dca-backtest.md`
- Modify: `docs/superpowers/specs/course/how-to-profit/specs/spec-05-ma-timing.md`
- Modify: `docs/superpowers/specs/course/how-to-profit/specs/spec-06-param-scan.md`
- Modify: `docs/superpowers/specs/course/how-to-profit/specs/spec-07-overfitting.md`
- Modify: `docs/superpowers/specs/project/ai_xquanty/2026-07-28-spec-execution-assessment.md`

**Interfaces:**
- Consumes: existing course specs plus the previously approved “light revision” targets
- Produces: tighter runnable specs without changing course narrative or learning sequence

- [ ] **Step 1: Tighten `spec-02-dca-backtest.md`**

Add the missing explicit contract items: returned index type and minimal validation expectations.

- [ ] **Step 2: Tighten `spec-05-ma-timing.md`**

Clarify zero-cost return handling and the behavior of skipped buy months.

- [ ] **Step 3: Tighten `spec-06-param-scan.md`**

Add small execution-validating expectations without spoiling the teaching “overfitting reveal” sequence.

- [ ] **Step 4: Tighten `spec-07-overfitting.md`**

Make train/test split boundaries explicit and non-overlapping, and add simple leakage-prevention expectations.

- [ ] **Step 5: Refresh the assessment doc paths and recommendations**

Update any path references made stale by the directory move.

### Task 4: Validate And Summarize

**Files:**
- Verify: moved and edited spec files above

**Interfaces:**
- Consumes: final directory structure and edited docs
- Produces: a validated documentation result ready for the next execution phase

- [ ] **Step 1: Re-run structural verification**

Run:
`find docs/superpowers/specs -maxdepth 4 -type f | sort`

Expected: all files are under the intended layout

- [ ] **Step 2: Sanity-check the edited files**

Run focused reads on the revised files to ensure headings, paths, and key instructions remain coherent.

- [ ] **Step 3: Review git status**

Run:
`git status --short`

Expected: only intended doc moves/edits appear, plus the pre-existing untouched `tests/data/test_loaders.py`
