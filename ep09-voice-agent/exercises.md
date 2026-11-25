# Ep09 exercises: Give your agent a voice

Work in this folder. `pytest -q` fakes every stage: no microphone, no speakers, no key.

## Exercise 1 (in the video): enforce the latency budget

Add `over_budget` and `slowest` to `Turn`, and log a warning from `VoiceAgent.turn` when a turn is
over `BUDGET_S`.

```python
from voice_agent import Turn

def test_over_budget_and_slowest():
    t = Turn("a", "b", None, {"stt": 0.5, "llm": 2.8, "tts": 0.4})
    assert t.over_budget and t.slowest == "llm"
    assert not Turn("a", "b", None, {"stt": 0.5}).over_budget


def test_slow_turn_logs_a_warning(tmp_path, caplog):
    slow = iter([0.0, 0.1, 0.1, 3.5, 3.5, 3.6])           # stt 0.1 s, llm 3.4 s, tts 0.1 s
    agent = VoiceAgent(stt=lambda p: "hi", llm=lambda m: "hello", tts=fake_tts,
                       clock=lambda: next(slow))
    agent.turn(tmp_path / "in.wav", tmp_path / "out.mp3")
    assert "over budget" in caplog.text and "llm" in caplog.text
```

<details><summary>Solution</summary>

```python
import logging

# in Turn:
    @property
    def over_budget(self) -> bool:
        return self.total > BUDGET_S

    @property
    def slowest(self) -> str | None:
        return max(self.timings, key=self.timings.get) if self.timings else None

# at the end of VoiceAgent.turn():
        result = Turn(heard, said, out, timings)
        if result.over_budget:
            logging.warning("voice turn over budget: %.2fs > %.1fs (slowest: %s)",
                            result.total, BUDGET_S, result.slowest)
        return result
```
</details>

## Exercise 2: speak times the way people do

Write `speak_time("16:30") -> "half past four"` for times on the hour and half hour
("09:00" -> "nine o'clock"), and use it in `for_speech` for `HH:MM` patterns.

<details><summary>Solution</summary>

```python
import re
WORDS = "twelve one two three four five six seven eight nine ten eleven".split()

def speak_time(hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    word = WORDS[h % 12]
    return {0: f"{word} o'clock", 30: f"half past {word}"}.get(m, hhmm)

# in for_speech, before the length check:
    clean = re.sub(r"\b\d{1,2}:\d{2}\b", lambda m: speak_time(m.group()), clean)
```

```python
def test_speak_time():
    assert speak_time("16:30") == "half past four" and speak_time("09:00") == "nine o'clock"
    assert speak_time("10:15") == "10:15"         # leave other times to the voice
```
</details>

## Exercise 3: stream the first sentence

Change the flow so the first complete sentence of the reply is sent to TTS before the rest is
written. Measure time to first sound before and after (needs a key and the streaming chat API from Ep08).

<details><summary>Solution (sketch)</summary>

Stream the chat completion, append tokens to a buffer, and as soon as the buffer contains `. `, `? `
or `! `, send that sentence to `tts` and keep going. Time to first sound drops to roughly
STT + time-to-first-sentence + TTS of one sentence. Real-time speech APIs do this, and more, for you.
</details>
