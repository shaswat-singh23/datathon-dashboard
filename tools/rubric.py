"""Run the judging rubric: ``uv run python tools/rubric.py``.

The score covers automated checks only, not predicted judging points. ``manual``
means the full criterion still needs review; details include any measured subset.
Exit 0 means the report was written (dashboard failures are report rows). Exit 2
means the runner itself failed. ``--skip-pytest`` avoids recursion in its pytest.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = dict(zip((f"R{i}" for i in range(1, 18)),
                   (3, 3, 2, 2, 3, 3, 4, 3, 2, 2, 2, 3, 2, 2, 1, 2, 1)))
NESTED = "ROYALE_RUBRIC_NESTED"


def row(check, status, details):
    if check not in WEIGHTS or status not in {"pass", "fail", "manual"}:
        raise ValueError((check, status))
    return {"id": check, "weight": WEIGHTS[check], "status": status, "details": details}


def score(rows):
    eligible = [r for r in rows if r["status"] != "manual"]
    possible = sum(r["weight"] for r in eligible)
    earned = sum(r["weight"] for r in eligible if r["status"] == "pass")
    return {"earned": earned, "possible": possible,
            "percent": round(100 * earned / possible, 2) if possible else None}


def committed_marts(root):
    result = subprocess.run(["git", "ls-files", "--", "marts/*.parquet"], cwd=root,
                            capture_output=True, text=True, check=True)
    return [root / name for name in result.stdout.splitlines()]


def clean(at):
    problems = [str(e.value) for e in list(at.exception) + list(at.error)]
    if problems:
        raise RuntimeError("; ".join(problems))


def numeric_output(at):
    """Exclude widget labels, captions and dates: a changed control alone is no evidence."""
    return ([str(m.value) for m in at.metric],
            [frame.value.select_dtypes(include="number").reset_index(drop=True).to_json(double_precision=12)
             for frame in at.dataframe if not frame.value.select_dtypes(include="number").empty])


def shown_output(at):
    charts = [str(e.proto) for kind in ("plotly_chart", "arrow_vega_lite_chart") for e in at.get(kind)]
    tables = [frame.value.to_json(date_format="iso", double_precision=12) for frame in at.dataframe]
    return numeric_output(at), tables, charts


def rendered_text(at):
    return "\n".join(str(e.value) for kind in ("markdown", "caption", "text", "info", "warning", "success")
                     for e in at.get(kind))


def change_period(at):
    widgets = [w for w in list(at.slider) + list(at.select_slider) + list(at.date_input)
               if re.search(r"period|date", w.label, re.I)]
    if not widgets:
        raise RuntimeError("No labeled period/date control")
    widget = widgets[0]
    value = widget.value
    if not isinstance(value, (tuple, list)) or len(value) != 2 or value[0] == value[1]:
        raise RuntimeError("Period control does not expose a changeable range")
    widget.set_value((value[0], value[0])).run()
    clean(at)


def change_drill(at):
    widgets = [w for w in list(at.selectbox) + list(at.multiselect) + list(at.radio)
               if re.search(r"bank|zone|machine|region|tier|age band|group|action drill|error breakdown", w.label, re.I)]
    if not widgets:
        raise RuntimeError("No bank, zone, machine, guest-group or page-specific drill")
    for widget in widgets:
        if len(widget.options) < 2:
            continue
        if widget.type == "multiselect":
            widget.set_value([widget.options[0]] if not widget.value else [])
        elif widget.type == "radio":
            widget.set_value(widget.options[1 if widget.index != 1 else 0])
        else:
            widget.select_index(1 if widget.index != 1 else 0)
        at.run()
        clean(at)
        return
    raise RuntimeError("Drill controls have no alternative selection")


def chart_problems(at):
    """Only explicit defects are automated; color independence still needs review."""
    problems = []
    count = 0
    for element in at.get("plotly_chart"):
        count += 1
        spec = json.loads(element.proto.spec)
        layout = spec.get("layout", {})
        def title(value):
            return value.get("text", "") if isinstance(value, dict) else value
        if not title(layout.get("title")):
            problems.append(f"Plotly chart {count}: missing title")
        # These pages use Cartesian charts. Other coordinate systems need manual review.
        if any(trace.get("type", "scatter") in {"scatter", "bar", "heatmap", "box", "histogram"}
               for trace in spec.get("data", [])):
            for axis in ("xaxis", "yaxis"):
                if not title(layout.get(axis, {}).get("title")):
                    problems.append(f"Plotly chart {count}: missing {axis} label")
    return {"count": count, "problems": problems,
            "manual": "Review native charts, all interactive states, and non-color encodings."}


def model_evidence(at):
    """Reconcile displayed MAEs and require actual/model traces on one chart."""
    import numpy as np
    import pandas as pd
    from royale import io
    from royale.model import FITTED_KIND, KINDS, LABELS, score_forecasts
    data = io.mart("q7_forecast")
    dates = pd.to_datetime(data.gaming_date)
    holdout = (len(data) == 61 and dates.nunique() == 61
               and str(dates.min().date()) == "2025-05-01"
               and str(dates.max().date()) == "2025-06-30")
    expected = score_forecasts(data)
    matched = False
    for frame in at.dataframe:
        table = frame.value
        if {"Model", "Full holdout MAE (USD/day)"} <= set(table.columns):
            displayed = table.set_index("Model")["Full holdout MAE (USD/day)"]
            matched = all(LABELS[k] in displayed.index and
                          np.isclose(displayed[LABELS[k]], expected[k], rtol=1e-8) for k in KINDS)
    chart = False
    for element in at.get("plotly_chart"):
        names = {trace.get("name", "") for trace in json.loads(element.proto.spec).get("data", [])}
        chart |= {"Actual coin-in", LABELS["constant"], LABELS[FITTED_KIND]} <= names
    return {"61_unique_holdout_days": holdout, "displayed_maes_reconcile": bool(matched),
            "actual_constant_and_fitted_traces": bool(chart)}


def inspect_page(page):
    # This worker is a fresh process; dotenv cannot restore the local raw-data path.
    sys.path.insert(0, str(ROOT))
    from streamlit.testing.v1 import AppTest
    import pandas as pd
    from royale import config, io
    allowed = {path.resolve() for path in committed_marts(ROOT)}
    original = pd.read_parquet
    def parquet(path, *args, **kwargs):
        if not isinstance(path, (str, Path)) or Path(path).resolve() not in allowed:
            raise RuntimeError("Rubric forbids parquet outside committed marts")
        return original(path, *args, **kwargs)
    def forbidden(*args, **kwargs):
        raise RuntimeError("Rubric forbids raw-data access")
    result = {"page": page}
    with tempfile.TemporaryDirectory(prefix="rubric-raw-") as empty, ExitStack() as stack:
        config.DATA_DIR = Path(empty)
        for name in ("connect", "sql", "table"):
            stack.enter_context(patch.object(io, name, forbidden))
        stack.enter_context(patch.object(pd, "read_parquet", parquet))
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
        if page != "app.py":
            at.run()
            clean(at)
            at.switch_page(page)
        started = time.perf_counter()
        at.run()
        elapsed = time.perf_counter() - started
        clean(at)
        # st.stop with an error/empty shell must not count as successful rendering.
        if not at.title or not (at.metric or at.dataframe):
            raise RuntimeError("Page stopped before rendering any metrics or tables")
        result.update(seconds=round(elapsed, 3), text=rendered_text(at), charts=chart_problems(at))
        sources = [e for e in at.expander if e.label.lower().startswith("source")]
        result["sources"] = [rendered_text(e) + "\n" + "\n".join(str(c.value) for c in e.get("code"))
                             + "\n" + "\n".join(str(option) for w in e.get("selectbox") for option in w.options)
                             for e in sources]
        result["traces"] = [{"label": e.label, "pages": len(e.get("page_link")), "text": rendered_text(e)}
                            for e in at.expander if e.label.startswith("Trace:")]
        result["chart_count"] = len(at.get("plotly_chart")) + len(at.get("arrow_vega_lite_chart"))
        if page == "pages/7_model.py":
            result["model"] = model_evidence(at)
        for check, change, snapshot in (("R2", change_period, numeric_output), ("R3", change_drill, shown_output)):
            try:
                # Restore default state: period and drill are independent experiments.
                fresh = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
                if page != "app.py":
                    fresh.switch_page(page).run()
                clean(fresh)
                before = snapshot(fresh)
                change(fresh)
                result[check] = {"status": "pass" if snapshot(fresh) != before else "fail",
                                 "details": "Displayed results changed" if snapshot(fresh) != before
                                 else "Control changed, but no measured output changed"}
            except Exception as exc:
                result[check] = {"status": "fail", "details": str(exc)}
    return result


def page_checks(root):
    pages = ["app.py"] + [str(p.relative_to(root)) for p in sorted((root / "pages").glob("*.py"))]
    results = []
    for page in pages:
        env = dict(os.environ, PYTHON_DOTENV_DISABLED="1")
        env.pop("DATA_DIR", None)
        try:
            worker = subprocess.run([sys.executable, str(root / "tools/rubric.py"), "--page-worker", page],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=150)
            if worker.returncode:
                raise RuntimeError(worker.stderr[-1800:] or worker.stdout[-1800:])
            results.append(json.loads(worker.stdout))
        except Exception as exc:
            results.append({"page": page, "error": str(exc)})
    return results


def page_row(check, pages, predicate):
    details = []
    for page in pages:
        if "error" in page:
            details.append({"page": page["page"], "status": "fail", "details": page["error"]})
        else:
            status, detail = predicate(page)
            details.append({"page": page["page"], "status": status, "details": detail})
    return row(check, "pass" if details and all(d["status"] == "pass" for d in details) else "fail", details)


def source_status(page):
    for source in page["sources"]:
        if (re.search(r"(?:marts/\S+\.parquet|\bq\d_\w+|property_day)", source)
                and re.search(r"query|SELECT|royale[/.]marts|build\b", source, re.I)
                and re.search(r"findings/[^\s`\])]+\.md", source)):
            return "pass", "Source names mart, query/builder reference and finding; query correctness needs review"
    return "fail", "Source must name its mart, query/builder and findings file"


UNCERTAINTY = r"confidence interval|\bCI\b|\binterval|luck band|\bband\b|\bp-value|credible|bootstrap|\u00b1|\+/-|standard error|\bz-score|uncertaint"


def uncertainty_status(page):
    found = sorted({m.group(0).lower() for m in re.finditer(UNCERTAINTY, page["text"], re.I)})
    if found:
        return "pass", {"terms": found, "limitation": "Term presence only; review that each comparison shows it."}
    return "fail", "No interval, luck band or other uncertainty language rendered on this page"


def appendix_check(root):
    appendix = root / "docs/claims_evidence.md"
    text = appendix.read_text() if appendix.exists() else ""
    # Only a table row with nonempty evidence columns counts; a filename elsewhere does not.
    lines = [line for line in text.splitlines() if line.startswith("|")]
    missing = []
    for finding in sorted((root / "findings").glob("*.md")):
        if finding.name == "README.md":
            continue
        matches = [line for line in lines if finding.name in line]
        if not any(len(cells := line.strip("|").split("|")) >= 8
                   and all(cells[i].strip() not in {"", "—", "-"} for i in (2, 3, 4, 5)) for line in matches):
            missing.append(finding.name)
    headings = all(re.search(term, text, re.I) for term in ("table.*query", "result", "alternative", "limitation"))
    return row("R8", "pass" if headings and not missing else "fail",
               {"missing_or_incomplete_rows": missing, "required_columns_present": headings,
                "limitation": "Checks coverage and nonempty fields, not scientific validity."})


def deliverables_check(root):
    writeup, disclosure = root / "docs/writeup.md", root / "docs/ai_disclosure.md"
    words = len(writeup.read_text().split()) if writeup.exists() else None
    disclosed = disclosure.is_file() and bool(disclosure.read_text().strip())
    return row("R13", "pass" if words is not None and 0 < words <= 400 and disclosed else "fail",
               {"writeup_words": words, "ai_disclosure_nonempty": disclosed,
                "word_rule": "Whitespace-separated tokens, including headings and links (conservative)."})


def deployment_check(root, url=None):
    if not url:
        readme = root / "README.md"
        candidates = re.findall(r"https://[a-zA-Z0-9.-]+\.streamlit\.app/?", readme.read_text() if readme.exists() else "")
        url = candidates[0] if candidates else None
    if not url:
        return row("R14", "fail", "No deployed Streamlit URL in README; pass --url to check another host")
    if not url.startswith("https://"):
        return row("R14", "fail", "Deployment URL must use HTTPS")
    try:
        with urlopen(url, timeout=15) as response:
            code = response.status
            body = response.read(1_000_000).decode("utf-8", errors="replace")
        if code != 200 or "streamlit" not in body.lower():
            return row("R14", "fail", {"url": url, "http_status": code, "streamlit_shell": False})
        return row("R14", "manual", {"url": url, "http_status": code,
                   "details": "Streamlit HTML shell responds; browser review must confirm the dashboard home loads (not a login/error page)."})
    except (OSError, URLError, ValueError) as exc:
        return row("R14", "fail", {"url": url, "error": str(exc)})


def mart_and_tests_check(root, run_tests):
    marts = committed_marts(root)
    invalid = [str(p.relative_to(root)) for p in marts if not p.is_file() or p.stat().st_size >= 5 * 1024 * 1024]
    details = {"committed_marts": len(marts), "missing_or_oversize": invalid}
    if not marts or invalid:
        return row("R15", "fail", details)
    if not run_tests:
        return row("R15", "manual", {**details, "pytest": "Not run (--skip-pytest); size subset passes"})
    try:
        env = dict(os.environ, **{NESTED: "1"})
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root,
                                env=env, capture_output=True, text=True, timeout=600)
        details.update(pytest_exit_code=result.returncode, pytest_output=result.stdout[-3000:] + result.stderr[-1000:])
        return row("R15", "pass" if result.returncode == 0 else "fail", details)
    except subprocess.TimeoutExpired:
        return row("R15", "fail", {**details, "pytest": "Timed out after 600 seconds"})


def budget_check(root):
    sys.path.insert(0, str(root))
    from royale import budget
    from royale.marts.q6_actions import proposed_plan
    import pandas as pd
    try:
        path = root / "marts/q6_actions.parquet"
        if path not in committed_marts(root):
            raise ValueError("Action mart is not committed")
        data = pd.read_parquet(path)
        catalog = data.loc[data.record_type == "catalog"]
        plan = proposed_plan(data)
        violations = budget.validate_plan(catalog, plan)
        details = {"violations": violations, "cost_usd": budget.plan_cost_usd(catalog, plan),
                   "details": "Runtime plan validation measured. Review each action's expected effect, uncertainty and measurement plan manually."}
        return row("R12", "fail" if violations else "manual", details)
    except Exception as exc:
        return row("R12", "fail", str(exc))


def originality_check(root):
    findings = [p for p in (root / "findings").glob("*.md") if p.name != "README.md"]
    candidates = [p.name for p in findings if re.search(r"\bunexpected\b", p.read_text(), re.I)
                  and re.search(r"^##? .*reproduc", p.read_text(), re.I | re.M)]
    return row("R17", "manual" if candidates else "fail",
               {"candidates": candidates, "details": "Review whether the result is unexpected; marker plus reproduction heading alone is insufficient."})


def run_checks(root=ROOT, *, run_tests=True, url=None):
    pages = page_checks(root)
    rows = [page_row("R1", pages, lambda p: ("pass" if p["seconds"] < 5 else "fail",
                                           {"seconds": p["seconds"], "limit_seconds": 5})),
            *[page_row(check, pages, lambda p, c=check: (p[c]["status"], p[c]["details"])) for check in ("R2", "R3")],
            page_row("R4", pages, source_status)]
    model = next((p for p in pages if p["page"] == "pages/7_model.py"), {})
    text = model.get("text", "")
    model_ok = (not model.get("error") and all(re.search(pattern, text, re.I | re.S) for pattern in
                (r"January.*April", r"May.*June", r"MAE", r"constant.*mean|mean.*training"))
                and bool(model.get("model")) and all(model["model"].values()))
    rows.append(row("R5", "pass" if model_ok else "fail",
                    {"model_evidence": model.get("model", {}),
                     "holdout_baseline_text": bool(re.search(r"January.*April.*May.*June", text, re.I | re.S)),
                     "limitation": "Checks the displayed evaluation against the committed mart; feature provenance is R11's manual audit."}))
    actions = next((p for p in pages if p["page"] == "pages/6_actions.py"), {})
    traces = actions.get("traces", [])
    trace_ok = (traces and not actions.get("error") and
                all(t["pages"] and re.search(r"findings/[^\s)]+\.md", t["text"]) for t in traces))
    rows.append(row("R6", "manual" if trace_ok else "fail",
                    {"traces": traces, "details": "Trace expanders checked for page and finding links; review coverage of every recommendation and alternative drill."}))
    rows.extend([
        row("R7", "manual", "Requires claim-by-claim numeric reconciliation with independently checked findings; digit or filename matching cannot prove this."),
        appendix_check(root),
        page_row("R9", pages, uncertainty_status),
        row("R10", "manual", "Audit money helpers, ratios of sums, dated placement joins and off-floor exclusions in every query; source mentions alone are insufficient."),
        row("R11", "manual", "Trace forecast feature provenance and availability dates, including indirect imports; banning words in model code would flag explanatory comments and miss leakage."),
        budget_check(root), deliverables_check(root), deployment_check(root, url),
        mart_and_tests_check(root, run_tests),
    ])
    chart_details = [{"page": p["page"], **p.get("charts", {"problems": [p.get("error", "No chart inspection")]})} for p in pages]
    rows.append(row("R16", "fail" if any(p["problems"] for p in chart_details) else "manual", chart_details))
    rows.append(originality_check(root))
    return sorted(rows, key=lambda r: int(r["id"][1:]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/rubric.json")
    parser.add_argument("--skip-pytest", action="store_true", help="R15 stays manual unless a size defect is found")
    parser.add_argument("--url", help="Deployed HTTPS URL; defaults to Streamlit URL in README")
    parser.add_argument("--page-worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.page_worker:
        print(json.dumps(inspect_page(args.page_worker)))
        return
    rows = run_checks(run_tests=not args.skip_pytest, url=args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement: downstream loops never read a partially written report.
    with tempfile.NamedTemporaryFile(mode="w", dir=args.output.parent, suffix=".tmp", delete=False) as handle:
        json.dump(rows, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(args.output)
    total = score(rows)
    percent = f"{total['percent']:.2f}%" if total["percent"] is not None else "N/A"
    print(f"Rubric: {total['earned']}/{total['possible']} automated weight ({percent}); "
          f"{sum(r['status'] == 'manual' for r in rows)} manual checks excluded; report: {args.output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Rubric runner failed: {exc}", file=sys.stderr)
        sys.exit(2)
