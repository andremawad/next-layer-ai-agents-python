"""Tests for Episode 7: testing the eval harness itself, with fake agents.  Run:  pytest -q"""
import json
from types import SimpleNamespace

import evals
from evals import Case, Result, gate, grade, load_cases, run_suite


def test_cases_file_loads():
    cases = load_cases()
    assert len(cases) == 5 and all(isinstance(c.contains_any, tuple) for c in cases)


def test_grader_checks_tools_and_text():
    case = Case("t", "q", must_call="get_time", contains_any=("14:32",), not_contains=("guess",))
    assert grade(case, Result("It's 14:32.", ["get_time"])) == []
    fails = grade(case, Result("I guess noon", []))
    assert len(fails) == 3


def test_must_not_call():
    case = Case("t", "q", must_not_call=True)
    assert grade(case, Result("60", ["get_time"])) != []


def test_flaky_agent_shows_in_pass_at_k_vs_pass_hat_k():
    answers = iter(["14:32", "no idea", "14:32"])
    agent = lambda q: Result(next(answers), ["get_time"])
    report = run_suite(agent, [Case("t", "q", must_call="get_time", contains_any=("14:32",))], k=3)
    assert report.pass_rate == 2 / 3
    assert report.pass_at_k() == 1.0 and report.pass_hat_k() == 0.0


def test_crash_counts_as_failure_not_suite_crash():
    def boom(q):
        raise RuntimeError("tool exploded")
    report = run_suite(boom, [Case("t", "q")], k=2)
    assert report.pass_rate == 0 and "crashed" in report.rows[0]["fails"][0]


def test_gate_blocks_regressions():
    good = run_suite(lambda q: Result("ok"), [Case("a", "q")])
    bad = run_suite(lambda q: Result("ok", ["x"]), [Case("a", "q", must_not_call=True)])
    assert gate(good, baseline=0.8) and not gate(bad, baseline=0.8)


def test_main_exit_code_is_the_ci_signal(tmp_path, capsys):
    base = tmp_path / "baseline.json"
    base.write_text(json.dumps({"pass_rate": 1.0}))
    always_wrong = lambda q: Result("banana")
    assert evals.main(["--baseline", str(base)], agent=always_wrong) == 1
    assert "REGRESSION" in capsys.readouterr().out


def test_time_agent_reports_tools_used():
    msgs = iter([
        SimpleNamespace(content=None, tool_calls=[SimpleNamespace(
            id="c1", function=SimpleNamespace(name="get_time", arguments='{"city": "Atlantis"}'))]),
        SimpleNamespace(content="I don't know Atlantis.", tool_calls=None)])
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=next(msgs))]))))
    r = evals.time_agent("time in Atlantis?", client=fake)
    assert r.tools == ["get_time"] and "Atlantis" in r.answer
