"""Shared period/bank filters: presets, persistence, reset and independent scopes."""
from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from royale import config, io
from royale.filters import matching_preset, preset_range

JAN1, JUN30 = date(2025, 1, 1), date(2025, 6, 30)


def open_home():
    at = AppTest.from_file(str(config.REPO_ROOT / "app.py"), default_timeout=60).run()
    clean(at)
    return at


def clean(at):
    assert not list(at.exception), [e.value for e in at.exception]
    assert not list(at.error), [e.value for e in at.error]


def widget(at, kind, label):
    return next(w for w in getattr(at, kind) if w.label == label)


def metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def captions(at):
    return "\n".join(c.value for c in at.caption)


def test_presets_use_2025_case_dates_and_clip_to_page_bounds():
    assert preset_range("Full period", JAN1, JUN30) == (JAN1, JUN30)
    assert preset_range("Q1", JAN1, JUN30) == (JAN1, date(2025, 3, 31))
    assert preset_range("Q2", JAN1, JUN30) == (date(2025, 4, 1), JUN30)
    # A May-June page has no Q1 rows: no silent clamp of January into May.
    assert preset_range("Q1", date(2025, 5, 1), JUN30) is None
    assert preset_range("Custom", JAN1, JUN30) is None
    assert matching_preset((JAN1, date(2025, 3, 31)), JAN1, JUN30) == "Q1"
    assert matching_preset((JAN1, date(2025, 3, 30)), JAN1, JUN30) == "Custom"


def test_preset_drives_slider_and_custom_range_updates_preset():
    at = open_home()
    preset = widget(at, "radio", "Period preset")
    assert preset.value == "Full period"
    assert preset.options == ["Full period", "Q1", "Q2", "Custom"]
    preset.set_value("Q2").run()
    clean(at)
    assert widget(at, "slider", "Analysis period").value == (date(2025, 4, 1), JUN30)
    widget(at, "slider", "Analysis period").set_value((date(2025, 2, 3), date(2025, 2, 9))).run()
    clean(at)
    assert widget(at, "radio", "Period preset").value == "Custom"


def test_period_and_bank_survive_home_to_machines_and_reset_restores_default():
    at = open_home()
    widget(at, "radio", "Period preset").set_value("Q1").run()
    widget(at, "selectbox", "Bank drill").select("B-01").run()
    clean(at)
    at.switch_page("pages/1_machines.py").run()
    clean(at)
    assert widget(at, "slider", "Analysis period").value == (JAN1, date(2025, 3, 31))
    assert widget(at, "radio", "Period preset").value == "Q1"
    assert widget(at, "selectbox", "Bank drill").value == "B-01"
    assert "B-01, Jan 01, 2025–Mar 31, 2025" in captions(at)
    # The daily period also reaches compatible daily pages; the zone drill stays local.
    at.switch_page("pages/3_downtime.py").run()
    clean(at)
    assert widget(at, "slider", "Analysis period").value == (JAN1, date(2025, 3, 31))
    assert widget(at, "selectbox", "Zone drill").value == "All zones"
    # Back on Machines, reset restores the documented default.
    at.switch_page("pages/1_machines.py").run()
    widget(at, "button", "Reset filters").click().run()
    clean(at)
    assert widget(at, "slider", "Analysis period").value == (JAN1, JUN30)
    assert widget(at, "radio", "Period preset").value == "Full period"
    assert widget(at, "selectbox", "Bank drill").value == "All banks"
    at.switch_page("app.py").run()
    assert widget(at, "selectbox", "Bank drill").value == "All banks"


def test_monthly_guest_and_holdout_scopes_stay_independent():
    at = open_home()
    widget(at, "slider", "Analysis period").set_value((date(2025, 1, 10), date(2025, 1, 20))).run()
    for page, label, expected, scope in [
        ("pages/4_players.py", "Analysis period (gaming months)", ("2025-01", "2025-06"), "Monthly guest scope"),
        ("pages/5_comps.py", "Period (whole months)", ("2025-01", "2025-06"), "Monthly guest scope"),
        ("pages/7_model.py", "Evaluation period", (date(2025, 5, 1), JUN30), "May–June evaluation scope"),
    ]:
        at.switch_page(page).run()
        clean(at)
        control = next(w for w in list(at.slider) + list(at.select_slider) if w.label == label)
        # Not rounded to January, and not clamped into May.
        assert tuple(control.value) == expected, page
        text = captions(at)
        assert scope in text and "not applied here" in text and "Jan 10, 2025–Jan 20, 2025" in text


def test_historical_filters_never_change_fixed_july_plan_or_evidence():
    at = open_home()
    fixed = [metric(at, label) for label in ("Inspection budget", "Budget retained", "Configuration inspection")]
    assert fixed == ["$1,200", "$98,800", "One"]
    plan_text = at.info[0].value
    evidence = [m.value for m in at.markdown if m.value.startswith("**") and "Recommended" not in m.value]
    widget(at, "radio", "Period preset").set_value("Q2").run()
    widget(at, "selectbox", "Bank drill").select("B-02").run()
    clean(at)
    assert [metric(at, label) for label in ("Inspection budget", "Budget retained", "Configuration inspection")] == fixed
    assert at.info[0].value == plan_text
    assert [m.value for m in at.markdown if m.value.startswith("**") and "Recommended" not in m.value] == evidence
    widget(at, "button", "Reset filters").click().run()
    assert [metric(at, label) for label in ("Inspection budget", "Budget retained", "Configuration inspection")] == fixed
    # Actions keeps the same plan whatever the evidence period.
    at.switch_page("pages/6_actions.py").run()
    clean(at)
    assert metric(at, "Plan cost") == "$1,200"
    assert any(s.value == "Within budget and catalogue limits." for s in at.success)
    # Implementation names stay in Source diagnostics, not in the headline status.
    assert not any("validate_plan" in e.value for e in list(at.success) + list(at.error))
    widget(at, "slider", "Evidence period").set_value((date(2025, 6, 1), date(2025, 6, 7))).run()
    clean(at)
    assert metric(at, "Plan cost") == "$1,200"
    assert "Historical evidence scope" in captions(at) and "July plan fixed" in captions(at)


def test_bank_with_no_rows_in_period_shows_empty_state(monkeypatch):
    original = io.mart

    def no_june_b01(name):
        data = original(name)
        if name == "q1_machines":
            dates = data.gaming_date.astype(str)
            data = data.loc[~((data.bank_id == "B-01") & (dates >= "2025-06-01"))]
        return data

    monkeypatch.setattr(io, "mart", no_june_b01)
    at = open_home()
    widget(at, "slider", "Analysis period").set_value((date(2025, 6, 1), JUN30)).run()
    widget(at, "selectbox", "Bank drill").select("B-01").run()
    clean(at)
    assert any("No on-floor machine-days" in i.value for i in at.info)
    assert "Historical scope: B-01, Jun 01, 2025–Jun 30, 2025" in captions(at)
    assert metric(at, "Inspection budget") == "$1,200"


@pytest.mark.parametrize("page", ["pages/1_machines.py", "pages/2_demand.py", "pages/3_downtime.py",
                                  "pages/4_players.py", "pages/5_comps.py", "pages/6_actions.py", "pages/7_model.py"])
def test_every_page_states_its_scope(page):
    at = open_home()
    at.switch_page(page).run()
    clean(at)
    assert "scope" in captions(at).lower(), page


def test_navigation_is_grouped_without_changing_routes():
    from royale.theme import NAV_GROUPS, ROUTES
    assert [group for group, _ in NAV_GROUPS] == ["OVERVIEW", "INVESTIGATE", "GUESTS & LOYALTY", "DECIDE & VALIDATE"]
    expected = ["app.py"] + [f"pages/{p.name}" for p in sorted((config.REPO_ROOT / "pages").glob("*.py"))]
    assert [route for route, _ in ROUTES] == expected
