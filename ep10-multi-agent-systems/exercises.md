# Ep10 exercises: Multi-agent systems

Work in this folder. `pytest -q` uses a scripted fake LLM; no key needed. Exercise 1's comparison needs a key.

## Exercise 1 (in the video): evaluate the baseline vs the router

Count model calls and passes for `single_agent` and `routed` on 5 requests. Start with a wrapper
that counts calls, tested offline:

```python
def test_counting_llm_counts_calls():
    llm = CountingLLM(ScriptedLLM('{"specialist": "faq"}', "We're closed on Sundays."))
    assert ma.routed(llm, "open sunday?") == ("faq", "We're closed on Sundays.")
    assert llm.calls == 2
```

<details><summary>Solution</summary>

```python
class CountingLLM:
    def __init__(self, llm):
        self.llm, self.calls = llm, 0

    def __call__(self, messages):
        self.calls += 1
        return self.llm(messages)


CASES = [("Are you open on Sunday?", ["closed"]),
         ("How much is a late cancellation?", ["50"]),
         ("Move my visit to Saturday", ["saturday"]),
         ("Is cosmetic work covered by insurance?", ["covered"]),
         ("Move my visit to Saturday and tell me the fee", ["saturday", "fee"])]   # all must appear


def compare(real_llm):
    for name, run in (("single", lambda llm, q: ma.single_agent(llm, q)),
                      ("routed", lambda llm, q: ma.routed(llm, q)[1])):
        passes = calls = 0
        for q, keywords in CASES:
            llm = CountingLLM(real_llm)
            answer = run(llm, q).lower()
            passes += all(k in answer for k in keywords)
            calls += llm.calls
        print(f"{name}: {passes}/{len(CASES)} passed, {calls} model calls")

compare(ma.make_llm())
```

A typical result: both pass the one-area questions, the router uses twice the calls, and the
two-area question is where routing fails and the orchestrator (or the single agent) wins. Run it
several times (Ep07: pass@k vs pass^k) before you decide.
</details>

## Exercise 2: parallel workers

Run the orchestrator's workers at the same time with `ThreadPoolExecutor` (from Ep02), keeping the
results in plan order.

```python
def test_parallel_orchestrate_keeps_order():
    llm = ScriptedLLM('[{"specialist": "bookings", "task": "a"}, {"specialist": "billing", "task": "b"}]',
                      "A", "B", "merged")
    assert ma.orchestrate(llm, "x", log=lambda _: None) == "merged"
```

<details><summary>Solution</summary>

```python
from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor() as pool:
        outs = list(pool.map(lambda s: SPECIALISTS[s["specialist"]].run(llm, s["task"]), steps))
    results = [f"{s['specialist']}: {o}" for s, o in zip(steps, outs)]
```

`pool.map` keeps the order of `steps`. Note the scripted fake hands out replies in call order, so
with real threads the "A"/"B" replies may swap between workers: a reminder that fakes for parallel
code should key replies by input, not by order.
</details>

## Exercise 3: tools per specialist

Give the bookings specialist the safe cancel flow from Ep03, and make sure the billing specialist
can't see that tool. Write a test that the billing specialist's request has no `tools` with
`cancel_booking`.

<details><summary>Solution (sketch)</summary>

Add `tools: tuple = ()` to `Specialist`, pass `tools=list(self.tools)` only when it's non-empty, and
run the Ep03 loop for specialists that have tools. Permissions per agent are one of the few
strong reasons to split into several agents.
</details>
