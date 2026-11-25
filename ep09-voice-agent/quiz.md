# Ep09 quiz: Give your agent a voice

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. What are the three calls in a voice turn?
2. Why is the system prompt written "for the ear"?
3. What does `for_speech` do, and why?
4. Why stop the turn when the transcript is empty?
5. Why track p95 and time to first sound, not only the average?
6. When would you move from this pipeline to a real-time speech API?

## Spaced review

7. (Ep08) Why keep the agent out of the web layer?
8. (Ep04) Why does RAG skip the model when nothing matches?

---

<details><summary>Answers</summary>

1. Speech to text, the agent (LLM), text to speech.
2. Everything is read aloud: lists, markdown and emojis sound broken.
3. Strips markdown symbols and caps the length at a sentence end, so the voice doesn't read symbols or ramble.
4. It was silence or noise: skipping saves two paid calls and avoids answering nothing.
5. Users remember the slowest turns, and the first sound is what makes it feel responsive.
6. When measurements show the pipeline is the bottleneck and you need lower latency or interruptions.
7. To test and reuse it without the framework.
8. With no sources the model can only guess, and the call costs money.
</details>
