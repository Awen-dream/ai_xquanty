# Q1 Notebook Delivery Design

## Context

We now have a cleaned-up course spec set under `docs/superpowers/specs/course/q1-how-to-profit/specs/` and paired review notes under `.../insights/`. The next goal is to actually deliver the Q1 teaching artifact as a runnable notebook chain, while keeping it isolated from the main `ai_xquanty` package implementation line.

This delivery should follow the teaching specs closely instead of reusing the package backtest engine. The notebook is meant to be a course-facing learning artifact, not an internal engineering wrapper around existing package code.

## Goal

Create a standalone Q1 notebook workspace inside the repository that:

- stays cleanly separated from the `ai_xquanty` package code;
- implements the `spec-01..07` teaching chain for `q1-how-to-profit` in order;
- can be run top-to-bottom as a coherent chapter notebook;
- preserves the teaching intent of the specs, including the staged reveal around parameter scanning and overfitting.

## Proposed Delivery Shape

Use the existing course spec directory with one notebook as the chapter’s primary artifact:

```text
docs/superpowers/specs/course/
  q1-how-to-profit/
    README.md
    notebooks/
      q1-strategy.ipynb
```

Why this shape:

- one notebook matches the spec chain’s strong sequential dependency;
- keeping the runnable artifact beside the specs removes cross-directory drift;
- `README.md` gives a small execution contract without mixing it into package docs;
- future Q2/Q3 chapters can extend the same structure naturally.

## Scope Boundaries

### In scope

- one Q1 notebook that implements the seven teaching specs in order;
- a local readme explaining how to run the notebook and what it contains;
- light notebook-facing setup needed to keep the chapter runnable inside this repository.

### Out of scope

- refactoring `ai_xquanty` package code to support the notebook;
- forcing the notebook to call package internals;
- turning the course notebook into a reusable production research framework;
- expanding beyond the Q1 chapter flow.

## Implementation Approach

### Approach A — Recommended

Build a standalone notebook implementation under `docs/superpowers/specs/course/q1-how-to-profit/`, following the course specs directly.

Trade-offs:

- Pros:
  - closest to the teaching specs;
  - avoids coupling course pedagogy to package internals;
  - easiest to reason about as a learning artifact;
  - cleanest long-term separation between “course demo” and “product/engine”.
- Cons:
  - some logic will overlap conceptually with package code;
  - notebook cells will intentionally reimplement simpler educational versions.

### Approach B

Build the notebook but silently reuse `ai_xquanty` package functions wherever possible.

Trade-offs:

- Pros:
  - less duplicated logic;
  - faster if engineering reuse is the main goal.
- Cons:
  - drifts away from the course specs;
  - makes the notebook harder for learners to understand;
  - entangles course artifacts with engineering constraints.

### Approach C

Split Q1 into multiple notebooks, one per spec or one per subsection.

Trade-offs:

- Pros:
  - strong chapter boundaries.
- Cons:
  - poor fit for the spec chain’s sequential state;
  - repeated setup and state transfer become awkward;
  - less convenient to run end-to-end.

### Recommendation

Use Approach A.

It best matches your chosen direction: a course artifact that is independently teachable, spec-faithful, and clearly separated from the package mainline.

## Notebook Architecture

The notebook should be organized into sequential sections that mirror the spec chain:

1. environment/import setup for the notebook
2. fixed-window ETF data retrieval
3. simple DCA backtest
4. benchmark comparison
5. moving-average visualization
6. MA timing strategy
7. parameter scan
8. train/test overfitting check

Each section should:

- consume artifacts created by earlier sections;
- expose named variables exactly where later specs expect them (`df`, `result_dca`, `backtest_dca`, `backtest_dca_with_ma`, scan results, etc.);
- be runnable in top-down order without hidden state outside prior notebook cells.

## Data And Reproducibility Rules

To keep the notebook aligned with the tightened course specs:

- use the fixed data window from the spec chain rather than “latest available” data;
- keep the notebook implementation self-contained;
- make validation cells explicit where the revised specs now require them;
- preserve the teaching sequence around parameter scanning and overfitting instead of “optimizing it away”.

## File Responsibilities

### `docs/superpowers/specs/course/q1-how-to-profit/notebooks/q1-strategy.ipynb`

- the main course artifact;
- contains all chapter code, charts, validations, and narrative flow;
- follows the spec order exactly.

### `docs/superpowers/specs/course/q1-how-to-profit/README.md`

- states what the notebook is;
- explains how to open/run it locally;
- documents that it is a course artifact separate from the package mainline;
- keeps setup notes local to the course workspace instead of polluting top-level docs.

## Validation Strategy

Success for this deliverable is not “library-grade abstraction”; it is:

- the notebook exists at the chosen path;
- the notebook structure mirrors the spec sequence;
- later cells can rely on earlier named variables/functions as specified;
- the chapter can be run from top to bottom without requiring package-level integration changes;
- the final sections demonstrate the intended teaching arc, especially the scan → overfitting reveal.

## Risks And Mitigations

### Risk 1: accidental coupling to `ai_xquanty`

Mitigation:

- keep notebook logic self-contained;
- do not import package backtest helpers unless a spec explicitly calls for it.

### Risk 2: notebook state drift across sections

Mitigation:

- preserve exact variable/function names expected by downstream sections;
- add small validation cells after key sections.

### Risk 3: overengineering the course artifact

Mitigation:

- prioritize readability and spec fidelity over reuse;
- do not introduce a helper module unless the notebook becomes materially harder to follow without it.

## Execution Plan Shape

The implementation plan should treat this as one subproject with a sequential notebook build:

1. scaffold the `docs/superpowers/specs/course/q1-how-to-profit/` workspace;
2. create notebook structure and chapter sections;
3. implement the spec chain in order;
4. add local readme and final validation pass.

## Approval Check

This design assumes:

- one notebook for the whole Q1 chapter;
- the runnable notebook living directly inside the Q1 course spec directory;
- no forced reuse of `ai_xquanty` package internals;
- notebook-first delivery over framework-first delivery.

If those assumptions still look right, the next step is to write the detailed implementation plan for the notebook build.
