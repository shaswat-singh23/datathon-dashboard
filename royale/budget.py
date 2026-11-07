"""Catalogue pricing and validation for the July 1–30, $100,000 plan.

Targets in a ``same_machine`` group must be machine IDs, including all machines
in a bank move. Callers expand banks before validation; this module does not read
raw placement data. Comp-policy actions conflict across the whole property.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from numbers import Integral

import pandas as pd

from royale import config


@dataclass
class ActionLine:
    action_type_id: str
    quantity: int
    targets: list[str] = field(default_factory=list)


def _action(catalog: pd.DataFrame, action_type_id: str) -> pd.Series:
    rows = catalog.loc[catalog["action_type_id"] == action_type_id]
    if len(rows) != 1:
        raise ValueError(f"Expected one catalog row for {action_type_id}; found {len(rows)}")
    return rows.iloc[0]


def _quantity(quantity: int) -> None:
    if isinstance(quantity, bool) or not isinstance(quantity, Integral) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")


def effective_days(catalog: pd.DataFrame, action_type_id: str,
                   horizon_days: int = config.HORIZON_DAYS) -> int:
    """Operating days after lead time, floored at zero within the horizon."""
    if isinstance(horizon_days, bool) or not isinstance(horizon_days, Integral) or horizon_days < 0:
        raise ValueError("horizon_days must be a nonnegative integer")
    return max(0, horizon_days - int(_action(catalog, action_type_id)["lead_days"]))


def _line_cost_cents(catalog: pd.DataFrame, line: ActionLine, horizon_days: int) -> int:
    _quantity(line.quantity)
    row = _action(catalog, line.action_type_id)
    days = effective_days(catalog, line.action_type_id, horizon_days)
    return line.quantity * (int(row["unit_cost_cents"]) +
                            int(row["recurring_cost_cents_per_day"]) * days)


def line_cost_usd(catalog: pd.DataFrame, line: ActionLine,
                  horizon_days: int = config.HORIZON_DAYS) -> float:
    """Quantity × (fixed cents + recurring cents × effective days) / 100.

    Fixed packages and purchases count in full, even beyond the horizon.
    Unknown action IDs and invalid quantities raise ValueError.
    """
    return _line_cost_cents(catalog, line, horizon_days) / 100


def plan_cost_usd(catalog: pd.DataFrame, lines: list[ActionLine]) -> float:
    """Sum in integer cents before converting to dollars."""
    return sum(_line_cost_cents(catalog, line, config.HORIZON_DAYS) for line in lines) / 100


def validate_plan(catalog: pd.DataFrame, lines: list[ActionLine],
                  budget_usd: float = config.BUDGET_USD) -> list[str]:
    """Return budget, type, quantity and target-conflict violations.

    Quantity limits apply across all lines of a type. A-HOLD uses no slot.
    Missing targets for target-specific incompatibilities are violations, since
    their compatibility cannot be checked. Empty plans preserve the budget.
    """
    violations = []
    types = {line.action_type_id for line in lines} - {"A-HOLD"}
    if len(types) > 3:
        violations.append("Plan exceeds 3 action types")
    quantities: dict[str, int] = {}
    occupied: dict[tuple[str, str], str] = {}
    total_cents = 0
    for line in lines:
        try:
            row = _action(catalog, line.action_type_id)
            total_cents += _line_cost_cents(catalog, line, config.HORIZON_DAYS)
        except ValueError as exc:
            violations.append(f"{line.action_type_id}: {exc}")
            continue
        quantities[line.action_type_id] = quantities.get(line.action_type_id, 0) + line.quantity
        group = row["incompatibility_group"]
        if pd.isna(group) or not group:
            continue
        if group == "comp_policy":
            targets = ["property"]
        else:
            targets = line.targets
            if not targets:
                violations.append(f"{line.action_type_id}: targets required for {group}")
        for target in set(targets):
            key = (str(group), target)
            if key in occupied:
                violations.append(f"Conflict in {group} on {target}: {occupied[key]} and {line.action_type_id}")
            occupied[key] = line.action_type_id
    for action_type, quantity in quantities.items():
        limit = int(_action(catalog, action_type)["quantity_limit"])
        if quantity > limit:
            violations.append(f"{action_type}: quantity {quantity} exceeds quantity_limit {limit}")
    if total_cents > budget_usd * 100:
        violations.append(f"Plan cost ${total_cents / 100:,.2f} exceeds budget ${budget_usd:,.2f}")
    return violations
