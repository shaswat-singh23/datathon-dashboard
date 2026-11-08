"""Checker regressions and a real CLI run; nested pytest cannot launch itself."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rubric", ROOT / "tools/rubric.py")
rubric = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rubric)


def test_weighted_score_excludes_manual_and_has_no_fake_full_score():
    rows = [rubric.row("R1", "pass", "ok"), rubric.row("R7", "fail", "bad"),
            rubric.row("R8", "manual", "review")]
    assert rubric.score(rows) == {"earned": 3, "possible": 7, "percent": 42.86}
    assert rubric.score([rows[2]]) == {"earned": 0, "possible": 0, "percent": None}
    with pytest.raises(ValueError):
        rubric.row("R1", "skipped", "")


def test_period_control_echo_does_not_count_as_changed_result():
    def view(caption, amount):
        return SimpleNamespace(metric=[SimpleNamespace(value=amount)],
                               dataframe=[SimpleNamespace(value=pd.DataFrame({"amount": [amount]}))],
                               caption=[SimpleNamespace(value=caption)])
    before = view("January–June", 100)
    assert rubric.numeric_output(before) == rubric.numeric_output(view("January", 100))
    assert rubric.numeric_output(before) != rubric.numeric_output(view("January", 30))
    before.dataframe[0].value["period"] = ["January"]
    after = view("February", 100)
    after.dataframe[0].value["period"] = ["February"]
    assert rubric.numeric_output(before) == rubric.numeric_output(after)


def test_page_failure_is_a_failure_not_an_omitted_check():
    rows = [{"page": "app.py", "seconds": 6}, {"page": "pages/broken.py", "error": "raw data read"}]
    result = rubric.page_row("R1", rows, lambda p: ("pass" if p["seconds"] < 5 else "fail", p["seconds"]))
    assert result["status"] == "fail"
    assert len(result["details"]) == 2
    assert result["details"][1]["details"] == "raw data read"


def test_worker_crash_is_reported(monkeypatch, tmp_path):
    (tmp_path / "pages").mkdir()
    def crash(*args, **kwargs):
        return SimpleNamespace(returncode=1, stderr="worker crash", stdout="")
    monkeypatch.setattr(rubric.subprocess, "run", crash)
    assert rubric.page_checks(tmp_path) == [{"page": "app.py", "error": "worker crash"}]


def test_source_requires_all_three_references():
    assert rubric.source_status({"sources": ["marts/q1_machines.parquet findings/22-machines.md"]})[0] == "fail"
    assert rubric.source_status({"sources": ["marts/q1_machines.parquet query royale/marts/q1_machines.py findings/22-machines.md"]})[0] == "pass"


def test_appendix_requires_evidence_columns_not_just_filename(tmp_path):
    (tmp_path / "findings").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "findings/1-result.md").write_text("# Claim")
    path = tmp_path / "docs/claims_evidence.md"
    header = "| # | Claim | Table/query | Result | Alternative | Limitation | Finding | Checked by |\n"
    path.write_text(header + "Mentioned here: 1-result.md")
    assert rubric.appendix_check(tmp_path)["status"] == "fail"
    path.write_text(header + "| 1 | claim | query | 10 | placebo | observational | 1-result.md | reviewer |")
    assert rubric.appendix_check(tmp_path)["status"] == "pass"
    path.write_text(header + "| 1 | claim | query | 10 | | observational | 1-result.md | reviewer |")
    assert rubric.appendix_check(tmp_path)["status"] == "fail"


def test_deliverable_word_limit_and_missing_disclosure(tmp_path):
    (tmp_path / "docs").mkdir()
    writeup = tmp_path / "docs/writeup.md"
    writeup.write_text("word " * 400)
    assert rubric.deliverables_check(tmp_path)["status"] == "fail"
    (tmp_path / "docs/ai_disclosure.md").write_text("# AI use\nReviewed by humans")
    assert rubric.deliverables_check(tmp_path)["status"] == "pass"
    writeup.write_text("word " * 401)
    assert rubric.deliverables_check(tmp_path)["status"] == "fail"


def test_mart_size_and_skipped_pytest_cannot_pass(monkeypatch, tmp_path):
    path = tmp_path / "sample.parquet"
    path.write_bytes(b"small")
    monkeypatch.setattr(rubric, "committed_marts", lambda root: [path])
    assert rubric.mart_and_tests_check(tmp_path, False)["status"] == "manual"
    with path.open("wb") as handle:
        handle.truncate(5 * 1024 * 1024)
    assert rubric.mart_and_tests_check(tmp_path, False)["status"] == "fail"
    path.unlink()
    assert rubric.mart_and_tests_check(tmp_path, False)["status"] == "fail"


def test_pytest_failure_and_recursion_guard(monkeypatch, tmp_path):
    path = tmp_path / "sample.parquet"
    path.write_bytes(b"small")
    monkeypatch.setattr(rubric, "committed_marts", lambda root: [path])
    def failed(command, **kwargs):
        assert command == [sys.executable, "-m", "pytest", "-q"]
        assert kwargs["env"][rubric.NESTED] == "1"
        return SimpleNamespace(returncode=1, stdout="1 failed", stderr="")
    monkeypatch.setattr(rubric.subprocess, "run", failed)
    assert rubric.mart_and_tests_check(tmp_path, True)["status"] == "fail"


def test_deployment_shell_does_not_prove_home_loaded(monkeypatch, tmp_path):
    (tmp_path / "README.md").write_text("Pending deployment")
    assert rubric.deployment_check(tmp_path)["status"] == "fail"
    class Shell:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self, limit):
            return b"<html>Streamlit</html>"
    monkeypatch.setattr(rubric, "urlopen", lambda *args, **kwargs: Shell())
    assert rubric.deployment_check(tmp_path, "https://example.com")["status"] == "manual"


def test_chart_missing_axes_and_title_is_a_failure():
    chart = SimpleNamespace(proto=SimpleNamespace(spec=json.dumps({"data": [{"type": "scatter"}], "layout": {}})))
    at = SimpleNamespace(get=lambda name: [chart] if name == "plotly_chart" else [])
    assert len(rubric.chart_problems(at)["problems"]) == 3


def test_model_check_rejects_wrong_mae_and_missing_actual_trace():
    from royale import io
    from royale.model import KINDS, LABELS, score_forecasts
    expected = score_forecasts(io.mart("q7_forecast"))
    table = pd.DataFrame({"Model": [LABELS[k] for k in KINDS],
                          "Full holdout MAE (USD/day)": expected.to_numpy()})
    spec = {"data": [{"name": name} for name in ["Actual coin-in"] + list(LABELS.values())]}
    chart = SimpleNamespace(proto=SimpleNamespace(spec=json.dumps(spec)))
    at = SimpleNamespace(dataframe=[SimpleNamespace(value=table)], get=lambda name: [chart])
    assert all(rubric.model_evidence(at).values())
    table.loc[0, "Full holdout MAE (USD/day)"] += 500
    assert not rubric.model_evidence(at)["displayed_maes_reconcile"]
    spec["data"] = spec["data"][1:]
    chart.proto.spec = json.dumps(spec)
    assert not rubric.model_evidence(at)["actual_constant_and_fitted_traces"]


@pytest.mark.skipif(os.environ.get(rubric.NESTED) == "1", reason="Checker's child pytest must not recursively run the CLI")
def test_checker_cli_writes_complete_report_without_raw_data(tmp_path):
    report = tmp_path / "rubric.json"
    env = dict(os.environ, DATA_DIR=str(tmp_path / "missing-raw"), PYTHON_DOTENV_DISABLED="1")
    result = subprocess.run([sys.executable, str(ROOT / "tools/rubric.py"), "--skip-pytest", "--output", str(report)],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr[-3000:]
    rows = json.loads(report.read_text())
    assert [r["id"] for r in rows] == list(rubric.WEIGHTS)
    assert [r["weight"] for r in rows] == list(rubric.WEIGHTS.values())
    assert all(set(r) == {"id", "weight", "status", "details"} for r in rows)
    assert all(r["status"] in {"pass", "fail", "manual"} for r in rows)
    assert "manual checks excluded" in result.stdout
    assert rows[14]["status"] == "manual"
    # This is a measurement harness: genuine dashboard failures remain report rows.
    # Every route must have actually been attempted, even if its app crashed.
    assert len(rows[0]["details"]) == 1 + len(list((ROOT / "pages").glob("*.py")))
    assert not any(p["details"] == "" for p in rows[0]["details"])


def test_deployment_check_diagnoses_auth_redirect(tmp_path, monkeypatch):
    def loop(*args, **kwargs):
        raise OSError("redirect loop")
    monkeypatch.setattr(rubric, "urlopen", loop)
    monkeypatch.setattr(rubric, "_first_redirect",
                        lambda url: "https://share.streamlit.io/-/auth/app?redirect_uri=x")
    result = rubric.deployment_check(tmp_path, "https://x.streamlit.app/")
    assert result["status"] == "fail"
    assert "not public" in result["details"]["diagnosis"]


def test_finding_template_flags_missing_and_empty_fields():
    good = ("# T\n- Issue: #1 | Author: a | Time: 10:00\n- Claim: c\n- Evidence: e\n"
            "- So what: s\n- Checked by: unchecked\n")
    assert rubric.finding_problems(good) == []
    assert rubric.finding_problems(good.replace("- So what: s\n", "- So what:\n")) == ["So what"]
    assert rubric.finding_problems(good.replace("# T\n", "")) == ["title"]
    assert rubric.finding_problems(good.replace("- Evidence: e\n", "- Evidence:\n  - e\n")) == []
