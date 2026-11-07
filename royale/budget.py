"""Price actions from action_catalog against the $100,000 / 30-day budget.

GUIDE.md formula for one action line:
    quantity * (unit_cost_cents + recurring_cost_cents_per_day * max(0, 30 - lead_days)) / 100
Rules: at most 3 action types (A-HOLD does not use a slot), quantity <= quantity_limit,
no two actions in the same incompatibility_group on the same target, purchases count in full.

Issue #2 implements these and tests them in tests/test_budget.py. Until then they raise.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from royale import config

_TODO = "Implemented by issue #2 (action pricing helper)."


@dataclass
class ActionLine:
    action_type_id: str
    quantity: int
    targets: list[str] = field(default_factory=list)  # machine, bank, zone or manufacturer ids


def line_cost_usd(catalog: pd.DataFrame, line: ActionLine, horizon_days: int = config.HORIZON_DAYS) -> float:
    """Cost of one action line in dollars, per the GUIDE.md formula."""
    raise NotImplementedError(_TODO)


def plan_cost_usd(catalog: pd.DataFrame, lines: list[ActionLine]) -> float:
    """Total cost of a plan in dollars."""
    raise NotImplementedError(_TODO)


def validate_plan(catalog: pd.DataFrame, lines: list[ActionLine],
                  budget_usd: float = config.BUDGET_USD) -> list[str]:
    """Return a list of violations (empty = valid): over budget, >3 types, over limit, conflicts."""
    raise NotImplementedError(_TODO)


def effective_days(catalog: pd.DataFrame, action_type_id: str, horizon_days: int = config.HORIZON_DAYS) -> int:
    """Days an action is in effect inside the horizon: max(0, horizon - lead_days)."""
    raise NotImplementedError(_TODO)
