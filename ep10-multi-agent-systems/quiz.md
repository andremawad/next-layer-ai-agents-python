# Ep10 quiz: Multi-agent systems

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. When does routing beat orchestrator-workers?
2. Why validate the planner's JSON?
3. Why cap the number of subtasks?
4. Why do errors compound across agents? Give the rough math for three hops at 90%.
5. Name three good reasons to split into several agents.
6. Why always keep a single-agent baseline?

## Spaced review (the whole series)

7. (Ep01) The four steps of the agent loop?
8. (Ep07) pass@k or pass^k: which means reliable?
9. (Ep09) The three calls in a voice turn?

---

<details><summary>Answers</summary>

1. When each request belongs to exactly one area: cheaper and simpler.
2. It's model output: it can name specialists that don't exist or be malformed.
3. A confused planner could fan out into many paid calls.
4. Each hop can misread text; 0.9 x 0.9 x 0.9 is about 0.73.
5. One prompt doing too many jobs; tools that need different permissions; parts that can run in parallel (and only when evals improve).
6. Without it you can't tell if the extra agents are worth their cost and latency.
7. Ask, decide, run, return.
8. pass^k.
9. Speech to text, the agent, text to speech.
</details>
