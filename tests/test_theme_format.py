"""Shortened dollar display stays faithful to the exact value it abbreviates."""
import re

import pytest

from royale.theme import exact_usd, short_usd

SCALE = {"": 1, "k": 1e3, "M": 1e6, "B": 1e9}


def parse_short(text):
    match = re.fullmatch(r"(−?)\$([\d,]+(?:\.\d+)?)([kMB]?)", text)
    assert match, text
    sign, number, suffix = match.groups()
    return (-1 if sign else 1) * float(number.replace(",", "")) * SCALE[suffix]


def parse_exact(text):
    match = re.fullmatch(r"Exact: (−?)\$([\d,]+(?:\.\d+)?)", text)
    assert match, text
    sign, number = match.groups()
    return (-1 if sign else 1) * float(number.replace(",", ""))


@pytest.mark.parametrize("value, shown", [
    (248_912_345, "$248.9M"), (41_300, "$41.3k"), (-5_300, "−$5.3k"), (189, "$189"),
    (218_340, "$218.3k"), (1_805_103, "$1.8M"), (2.4e9, "$2.4B"), (0, "$0"),
])
def test_short_usd_examples(value, shown):
    assert short_usd(value) == shown


@pytest.mark.parametrize("value", [0, 189, 999, 1_000, 41_349, 913_383, 1_805_103,
                                   248_912_345, 3.21e9, -5_300, -1_234_567])
def test_short_usd_round_trips_within_display_precision(value):
    back = parse_short(short_usd(value))
    # One decimal of the chosen unit: within half a step of that unit, sign preserved.
    unit = next((s for s in (1e9, 1e6, 1e3) if abs(value) >= s), 1)
    tolerance = 0.5 if unit == 1 else 0.05 * unit
    assert abs(back - value) <= tolerance + 1e-9
    assert (back < 0) == (value < 0)


@pytest.mark.parametrize("value", [0, 189, 913_383, 248_912_345, -1_234_567])
def test_exact_usd_round_trips_to_the_dollar(value):
    assert parse_exact(exact_usd(value)) == value
    assert exact_usd(1234.5, cents=True) == "Exact: $1,234.50"
