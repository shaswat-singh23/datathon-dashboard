"""Judge interactions, source accessibility and exposure math with no raw data."""
from datetime import date
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from royale import config, io
from royale.evidence import documents, local_references_as_text, read_document
from royale.overview import period_totals, rank_stability, select_machine_days, weekday_profile


@pytest.fixture
def no_raw_data(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail("Dashboard tried to read raw data")

    for name in ("connect", "sql", "table"):
        monkeypatch.setattr(io, name, forbidden)


def open_page(page=None):
    at = AppTest.from_file(str(config.REPO_ROOT / "app.py"), default_timeout=60).run()
    if page:
        at.switch_page(f"pages/{page}").run()
    assert_clean(at)
    return at


def assert_clean(at):
    assert not list(at.exception), [e.value for e in at.exception]
    assert not list(at.error), [e.value for e in at.error]


def metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def selectbox(at, label):
    return next(s for s in at.selectbox if s.label == label)


@pytest.mark.parametrize("page", [None] + [p.name for p in sorted((config.REPO_ROOT / "pages").glob("*.py"))])
def test_judge_period_drill_and_evidence_on_every_route(page, no_raw_data):
    at = open_page(page)
    assert any(e.label.startswith("Source") for e in at.expander)
    period = (list(at.slider) + list(at.select_slider))[0]
    if page in {"4_players.py", "5_comps.py"}:
        month = period.options[2]
        period.set_value((month, month))
    elif page == "7_model.py":
        period.set_value((date(2025, 5, 1), date(2025, 5, 1)))
    else:
        period.set_value((date(2025, 3, 8), date(2025, 3, 8)))
    at.run()
    assert_clean(at)
    drills = [s for s in at.selectbox if s.label != "Evidence document"] + list(at.multiselect)
    assert drills, f"{page or 'Home'} has no drill"
    drill = drills[0]
    if drill.type == "multiselect":
        drill.set_value([drill.value[0] if drill.value else drill.options[0]])
    else:
        drill.select_index(min(1, len(drill.options) - 1))
    at.run()
    assert_clean(at)
    # A judge can read both required submission documents without an external URL.
    for name, heading in [("docs/claims_evidence.md", "# Claims & Evidence appendix"),
                          ("docs/ai_disclosure.md", "# AI-use disclosure")]:
        selectbox(at, "Evidence document").select(name).run()
        assert_clean(at)
        assert any(heading in m.value for m in at.markdown)
        assert at.get("download_button")


def test_home_changes_dollars_and_rank_scope_with_bank_and_period(no_raw_data):
    at = open_page()
    assert metric(at, "Manager picks surviving adjustment") == "8 / 10"
    assert "M-1158" in at.info[0].value and "$1,200" in at.info[0].value and "$98,800" in at.info[0].value
    fixed_plan = at.info[0].value
    # Registered direct links take judges to the three key investigations.
    assert len(at.get("page_link")) >= 3
    at.slider[0].set_value((date(2025, 6, 1), date(2025, 6, 30))).run()
    selectbox(at, "Bank drill").select("B-01").run()
    assert_clean(at)
    source = io.mart("q1_machines")
    dates = pd.to_datetime(source.gaming_date)
    expected = source.loc[(source.bank_id == "B-01") & (dates.dt.month == 6)]
    assert metric(at, "Coin-in") == f"${expected.coin_in_cents.sum() / 100:,.0f}"
    displayed = at.dataframe[0].value
    assert set(displayed.index) <= set(expected.machine_id)
    assert displayed.active_days.max() <= 30
    assert at.info[0].value == fixed_plan


def test_dst_day_uses_23_hours_and_reconciles_property_totals(no_raw_data):
    day = date(2025, 3, 8)
    selected = select_machine_days(io.mart("q1_machines"), day, day)
    assert set(selected.scheduled_seconds) == {23 * 3600}
    totals = period_totals(selected)
    assert totals["scheduled_hours"] == 23 * selected.machine_id.nunique()
    floor = io.mart("property_day")
    expected = floor.loc[pd.to_datetime(floor.gaming_date).dt.date == day].iloc[0]
    assert totals["coin_in"] == pytest.approx(expected.coin_in_usd)
    assert totals["available_hours"] == pytest.approx(expected.available_machine_hours)
    assert totals["availability"] == pytest.approx(expected.availability_ratio)
    at = open_page()
    at.slider[0].set_value((day, day)).run()
    assert_clean(at)
    assert metric(at, "Coin-in") == f"${expected.coin_in_usd:,.0f}"


def test_home_zero_exposure_does_not_invent_adjusted_ranks(no_raw_data, monkeypatch):
    original = io.mart

    def zero(name):
        data = original(name)
        if name == "q1_machines":
            data[["available_seconds", "coin_in_cents", "house_win_cents", "theo_cents"]] = 0
        return data

    monkeypatch.setattr(io, "mart", zero)
    at = open_page()
    assert metric(at, "Observed hold") == "Undefined"
    assert metric(at, "Availability") == "0.00%"
    assert metric(at, "Manager picks surviving adjustment") == "Undefined"


@pytest.mark.parametrize("path", [".env", "README.md", "../.env", "/etc/passwd", "findings/../.env", "docs/../../.env"])
def test_evidence_rejects_unpublished_paths(path):
    with pytest.raises(ValueError):
        read_document(path)


def test_evidence_rejects_symlinks_outside_published_directories(tmp_path, monkeypatch):
    (tmp_path / "findings").mkdir()
    (tmp_path / ".env").write_text("not public")
    (tmp_path / "findings/1-symlink.md").symlink_to(tmp_path / ".env")
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    with pytest.raises(ValueError):
        read_document("findings/1-symlink.md")


def test_all_evidence_is_readable_and_relative_urls_are_not_broken_routes():
    for name in documents():
        assert read_document(name).startswith("# ")
    rendered = local_references_as_text("[Claim](../findings/22-machines.md) · [NOAA](https://noaa.gov)")
    assert "(../findings/" not in rendered
    assert "22-machines.md" in rendered and "[NOAA](https://noaa.gov)" in rendered


def test_weekday_profile_matches_training_mart_and_ignores_holdout_outcomes():
    forecasts = io.mart("q7_forecast")
    profile = weekday_profile(forecasts)
    floor = io.mart("property_day")
    train = floor.loc[pd.to_datetime(floor.gaming_date) <= "2025-04-30"].copy()
    train["weekday"] = pd.to_datetime(train.gaming_date).dt.day_name()
    expected = train.groupby("weekday").coin_in_usd.mean()
    for day, row in profile.iterrows():
        assert row.weekday_prediction_usd == pytest.approx(expected[day])
        assert row.constant_prediction_usd == pytest.approx(train.coin_in_usd.mean())
    forecasts["coin_in_usd"] = -1e20
    pd.testing.assert_frame_equal(profile, weekday_profile(forecasts))


def test_month_removal_sensitivity_detects_unstable_rank_and_handles_zero_exposure():
    # Three full calendar blocks: one machine is weak in two and strong in one.
    dates = pd.date_range("2025-01-01", "2025-03-31")
    rows = []
    for machine in ("A", "B", "C"):
        for day in dates:
            rate = (0 if day.month < 3 else 30) if machine == "A" else {"B": 8, "C": 12}[machine]
            rows.append(dict(machine_id=machine, gaming_date=day, theo_cents=100 * rate,
                             supplied_cost_usd=0, available_seconds=3600))
    data = pd.DataFrame(rows)
    sensitivity = rank_stability(data, ["A", "B", "C"])
    assert sensitivity.loc["A", "full_adjusted_rank"] == 2
    assert sensitivity.loc["A", "lowest_rank"] == 1
    assert sensitivity.loc["A", "highest_rank"] == 3
    assert (sensitivity.testable_runs == 3).all()
    # If C has exposure only in March, deleting March makes its rank undefined.
    data.loc[(data.machine_id == "C") & (data.gaming_date.dt.month < 3), "available_seconds"] = 0
    sensitivity = rank_stability(data, ["C"])
    assert sensitivity.loc["C", "testable_runs"] == 2
    assert sensitivity.loc["C", "complete_months"] == 3
    assert rank_stability(data[data.gaming_date.dt.month < 3], ["A"]).empty


def test_committed_month_removal_ranks_match_independent_aggregation():
    data = io.mart("q1_machines")
    manager = (data.groupby("machine_id").house_win_cents.sum().sort_index()
               .sort_values(kind="stable").head(10).index)
    sensitivity = rank_stability(data, manager)
    assert (sensitivity.complete_months == 6).all()
    independent = []
    for month in range(1, 7):
        remaining = data.loc[pd.to_datetime(data.gaming_date).dt.month != month]
        totals = remaining.groupby("machine_id")[["theo_cents", "supplied_cost_usd", "available_seconds"]].sum()
        totals["rate"] = (totals.theo_cents / 100 - totals.supplied_cost_usd) / (totals.available_seconds / 3600)
        order = totals.loc[totals.available_seconds > 0].sort_index().sort_values("rate", kind="stable")
        independent.append(pd.Series(range(1, len(order) + 1), index=order.index).reindex(manager))
    expected = pd.concat(independent, axis=1)
    assert sensitivity.lowest_rank.tolist() == expected.min(axis=1).tolist()
    assert sensitivity.highest_rank.tolist() == expected.max(axis=1).tolist()
    assert sensitivity.bottom_ten_runs.tolist() == (expected <= 10).sum(axis=1).tolist()
