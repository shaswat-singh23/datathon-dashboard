---
name: baseline
description: Build an honest baseline model with proper cross-validation. Use when the user wants a first model, a benchmark, or to check whether a prediction task is feasible.
argument-hint: "[target-column] [table-name-or-path]"
---

Target: $0. Data: $1. If either is missing, infer from EDA.md or ask.

1. State the task type (regression, binary, multiclass, forecasting) and the metric that matches the challenge.
2. Choose the split and justify it in one line: time-based if there is a time column, GroupKFold if rows share an entity, otherwise (stratified) KFold.
3. Naive baseline: mean or median, majority class, or last-value / seasonal-naive for time series.
4. Model: sklearn Pipeline with all preprocessing inside CV, then HistGradientBoosting. Try lightgbm only if it adds something.
5. Report for baseline and model: metric mean and std across folds, train vs validation gap, and top 10 features by permutation importance on validation folds.
6. Leakage check: if the model beats the baseline by an implausible margin or one feature dominates, investigate before reporting. Say what you checked.
7. Save code to `src/models/baseline_<target>.py`, runnable with `uv run python -m src.models.baseline_<target>`. Append results to FINDINGS.md using the entry format in AGENTS.md.

No hyperparameter tuning yet.
