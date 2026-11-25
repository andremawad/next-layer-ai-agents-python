"""Episode 7: Test your AI agent like real software (evals in Python).

    pip install openai tzdata
    set OPENAI_API_KEY, then:  python evals.py --k 3          (exit code 1 on a regression)

Frontend mental model: this is Jest + CI for something non-deterministic. You can't snapshot
the exact words, so each case asserts properties (mentions 14:32, called get_time, no made-up
city), runs k times, and the suite fails the build if the pass rate drops below the baseline,
the way a Lighthouse CI budget fails on a slower page.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

HERE = Path(__file__).parent
MODEL = os.environ.get("MODEL", "gpt-4o-mini")


def make_client():
    from openai import OpenAI
    return OpenAI()


# ---------------------------------------------------------------- the agent under test (Ep01's)
@dataclass
class Result:
    answer: str
    tools: list[str] = field(default_factory=list)


ZONES = {"london": "Europe/London", "tokyo": "Asia/Tokyo", "new york": "America/New_York"}
TOOLS = [{"type": "function", "function": {
    "name": "get_time", "description": "Current local time in a city",
    "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}]


def get_time(city: str) -> str:
    zone = ZONES.get(str(city).lower())
    return datetime.now(ZoneInfo(zone)).strftime("%H:%M") if zone else f"Unknown city: {city}"


def time_agent(question: str, client=None, model: str = MODEL) -> Result:
    client = client or make_client()
    messages: list = [{"role": "user", "content": question}]
    used: list[str] = []
    for _ in range(5):
        msg = client.chat.completions.create(model=model, messages=messages,
                                             tools=TOOLS).choices[0].message
        if not msg.tool_calls:
            return Result(msg.content or "", used)
        messages.append(msg)
        for call in msg.tool_calls:
            used.append(call.function.name)
            city = json.loads(call.function.arguments).get("city", "")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": get_time(city)})
    return Result("Stopped after 5 tool rounds.", used)


# ---------------------------------------------------------------- cases and graders
@dataclass(frozen=True)
class Case:
    id: str
    question: str
    must_call: str | None = None          # a tool that must be used
    must_not_call: bool = False           # answer from knowledge, no tool
    contains_any: tuple[str, ...] = ()    # at least one of these strings (case-insensitive)
    not_contains: tuple[str, ...] = ()    # none of these


def load_cases(path: Path = HERE / "cases.jsonl") -> list[Case]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            d["contains_any"] = tuple(d.get("contains_any", ()))
            d["not_contains"] = tuple(d.get("not_contains", ()))
            out.append(Case(**d))
    return out


def grade(case: Case, r: Result) -> list[str]:
    """Code-based graders. Returns the list of failed checks (empty = pass)."""
    fails, text = [], r.answer.lower()
    if case.must_call and case.must_call not in r.tools:
        fails.append(f"did not call {case.must_call}")
    if case.must_not_call and r.tools:
        fails.append(f"called {r.tools} but should answer directly")
    if case.contains_any and not any(s.lower() in text for s in case.contains_any):
        fails.append(f"answer has none of {list(case.contains_any)}")
    for s in case.not_contains:
        if s.lower() in text:
            fails.append(f"answer contains forbidden {s!r}")
    return fails


@dataclass
class Report:
    rows: list[dict]

    @property
    def pass_rate(self) -> float:
        runs = [ok for row in self.rows for ok in row["runs"]]
        return sum(runs) / len(runs) if runs else 0.0

    def pass_at_k(self) -> float:                 # at least one success per case
        return sum(any(r["runs"]) for r in self.rows) / len(self.rows)

    def pass_hat_k(self) -> float:                # every run succeeded (reliability)
        return sum(all(r["runs"]) for r in self.rows) / len(self.rows)


def run_suite(agent: Callable[[str], Result], cases: list[Case], k: int = 1) -> Report:
    rows = []
    for case in cases:
        runs, notes = [], []
        for _ in range(k):
            try:
                fails = grade(case, agent(case.question))
            except Exception as e:                # a crash is a failed run, not a crashed suite
                fails = [f"crashed: {e}"]
            runs.append(not fails)
            notes += fails
        rows.append({"id": case.id, "runs": runs, "fails": sorted(set(notes))})
    return Report(rows)


def gate(report: Report, baseline: float, allowed_drop: float = 0.05) -> bool:
    """True when the pass rate didn't regress more than allowed_drop below the baseline."""
    return report.pass_rate >= baseline - allowed_drop


def main(argv: list[str] | None = None, agent: Callable[[str], Result] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=1)
    ap.add_argument("--baseline", default=str(HERE / "baseline.json"))
    ap.add_argument("--update-baseline", action="store_true")
    a = ap.parse_args(argv)
    report = run_suite(agent or time_agent, load_cases(), a.k)
    for row in report.rows:
        mark = "PASS" if all(row["runs"]) else "FAIL"
        print(f"  {mark}  {row['id']:<22} {sum(row['runs'])}/{len(row['runs'])}  {'; '.join(row['fails'])}")
    base_f = Path(a.baseline)
    baseline = json.loads(base_f.read_text())["pass_rate"] if base_f.exists() else 0.0
    print(f"pass rate {report.pass_rate:.0%} (baseline {baseline:.0%})  "
          f"pass@{a.k} {report.pass_at_k():.0%}  pass^{a.k} {report.pass_hat_k():.0%}")
    if a.update_baseline:
        base_f.write_text(json.dumps({"pass_rate": round(report.pass_rate, 3)}) + "\n")
        return 0
    if not gate(report, baseline):
        print("REGRESSION: pass rate dropped below the baseline")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
