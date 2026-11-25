# Ep07 quiz: Evals in Python

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. Why don't snapshot tests work for an agent?
2. What's the difference between pass@k and pass^k? Which one means "reliable"?
3. Why does a crash count as a failed run instead of stopping the suite?
4. What does the baseline gate return on a regression, and why that?
5. Why does the gate allow a small drop?
6. When would you add an LLM-as-judge grader?

## Spaced review

7. (Ep06) What do alpha 0 and alpha 1 mean in hybrid search?
8. (Ep03) Why isn't a prompt rule a real guard?

---

<details><summary>Answers</summary>

1. The wording changes every run, so exact matches fail on harmless rewording.
2. pass@k: any of k runs passed (can it do this at all?). pass^k: all k passed (can I rely on it?). pass^k.
3. So one broken case can't hide the results of all the others.
4. Exit code 1, which fails a CI job.
5. Small suites are noisy: one flaky answer moves the rate a lot.
6. For qualities code can't check (tone, faithfulness), after checking the judge against your own labels.
7. 0 is pure keyword, 1 is pure vector.
8. The model can ignore it or be talked out of it.
</details>
