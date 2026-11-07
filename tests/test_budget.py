"""Budget rules checked against guide examples and the optional real catalog."""
import os

import pandas as pd
import pytest

from royale import config
from royale.budget import ActionLine, effective_days, line_cost_usd, plan_cost_usd, validate_plan


@pytest.fixture
def catalog():
    # Independent guide prices, limits and groups; monetary values are cents.
    rows = [
        ("A-REPLACE-LEASE", 250000, 5500, 14, 20, "same_machine"),
        ("A-REPLACE-BUY", 2200000, 0, 21, 10, "same_machine"),
        ("A-MOVE-MACHINE", 180000, 0, 2, 24, "same_machine"),
        ("A-MOVE-BANK", 950000, 0, 5, 3, "same_machine"),
        ("A-TECH-SHIFT", 1152000, 0, 7, 3, None),
        ("A-COMP-PILOT", 400000, 0, 5, 1, "comp_policy"),
        ("A-COMP-CHANGE", 150000, 0, 3, 1, "comp_policy"),
        ("A-HOLD", 0, 0, 0, 1, ""),
    ]
    return pd.DataFrame(rows, columns=["action_type_id", "unit_cost_cents",
        "recurring_cost_cents_per_day", "lead_days", "quantity_limit", "incompatibility_group"])


def test_guide_lease_example(catalog):
    assert effective_days(catalog, "A-REPLACE-LEASE") == 16
    assert line_cost_usd(catalog, ActionLine("A-REPLACE-LEASE", 1)) == 3380
    assert line_cost_usd(catalog, ActionLine("A-REPLACE-LEASE", 2)) == 6760
    assert effective_days(catalog, "A-REPLACE-LEASE", 10) == 0
    assert line_cost_usd(catalog, ActionLine("A-REPLACE-LEASE", 1), 10) == 2500


def test_fixed_packages_and_full_purchase(catalog):
    assert line_cost_usd(catalog, ActionLine("A-TECH-SHIFT", 1)) == 11520
    assert line_cost_usd(catalog, ActionLine("A-REPLACE-BUY", 1), 10) == 22000
    assert plan_cost_usd(catalog, [ActionLine("A-REPLACE-BUY", 1), ActionLine("A-TECH-SHIFT", 1)]) == 33520


def test_empty_and_valid_plan(catalog):
    assert plan_cost_usd(catalog, []) == 0
    assert validate_plan(catalog, []) == []
    lines = [ActionLine("A-REPLACE-LEASE", 1, ["M1"]),
             ActionLine("A-TECH-SHIFT", 1), ActionLine("A-COMP-PILOT", 1), ActionLine("A-HOLD", 1)]
    assert validate_plan(catalog, lines) == []


def test_comp_conflicts_even_on_different_targets(catalog):
    errors = validate_plan(catalog, [ActionLine("A-COMP-PILOT", 1, ["control"]),
                                    ActionLine("A-COMP-CHANGE", 1, ["floor"])])
    assert any("comp_policy" in error for error in errors)


def test_budget_boundary(catalog):
    lines = [ActionLine("A-REPLACE-BUY", 5, [f"M{i}" for i in range(5)])]
    assert any("exceeds budget" in error for error in validate_plan(catalog, lines))
    assert validate_plan(catalog, lines, budget_usd=110000) == []


def test_four_types(catalog):
    lines = [ActionLine(name, 1, [f"M{i}"]) for i, name in enumerate(
        ["A-REPLACE-LEASE", "A-REPLACE-BUY", "A-MOVE-MACHINE", "A-TECH-SHIFT"])]
    assert any("3 action types" in error for error in validate_plan(catalog, lines))


def test_quantity_limits_across_lines(catalog):
    lines = [ActionLine("A-TECH-SHIFT", 2), ActionLine("A-TECH-SHIFT", 2)]
    assert any("quantity_limit" in error for error in validate_plan(catalog, lines))


def test_machine_conflicts_and_bank_expansion(catalog):
    lines = [ActionLine("A-MOVE-BANK", 1, ["M1", "M2"]),
             ActionLine("A-REPLACE-LEASE", 1, ["M2"])]
    assert any("same_machine on M2" in error for error in validate_plan(catalog, lines))
    lines[1].targets = ["M3"]
    assert validate_plan(catalog, lines) == []
    assert any("targets required" in error for error in validate_plan(catalog, [ActionLine("A-MOVE-BANK", 1)]))


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
def test_invalid_quantity(catalog, quantity):
    line = ActionLine("A-TECH-SHIFT", quantity)
    with pytest.raises(ValueError, match="positive integer"):
        line_cost_usd(catalog, line)
    assert validate_plan(catalog, [line])


def test_unknown_and_duplicate_catalog_ids(catalog):
    with pytest.raises(ValueError, match="Expected one catalog row"):
        effective_days(catalog, "missing")
    assert validate_plan(catalog, [ActionLine("missing", 1)])
    with pytest.raises(ValueError, match="found 2"):
        line_cost_usd(pd.concat([catalog, catalog]), ActionLine("A-HOLD", 1))


@pytest.mark.parametrize("days", [-1, 1.5, True])
def test_invalid_horizon(catalog, days):
    with pytest.raises(ValueError, match="nonnegative integer"):
        effective_days(catalog, "A-HOLD", days)


def test_real_catalog():
    if not os.environ.get("DATA_DIR") or not config.table_path("action_catalog").is_file():
        pytest.skip("Set DATA_DIR to a dataset containing action_catalog to run this check")
    real = pd.read_parquet(config.table_path("action_catalog"))
    for row in real.itertuples(index=False):
        expected = (row.unit_cost_cents + row.recurring_cost_cents_per_day * max(0, 30 - row.lead_days)) / 100
        assert line_cost_usd(real, ActionLine(row.action_type_id, 1)) == expected
    assert line_cost_usd(real, ActionLine("A-REPLACE-LEASE", 1)) == 3380
