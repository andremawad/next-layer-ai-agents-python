# Episode 9: Give Your AI Agent a Voice (Speech to Text + Text to Speech)

One voice turn in plain Python: speech to text, the agent, text to speech, each stage timed
against a 3-second budget. Small interfaces (`STT`, `TTS`) make every stage swappable and testable.

Video: coming soon

Part of the course [AI Engineering: Build Real AI Agents in Python](../README.md) on [Next Layer](https://www.youtube.com/@NextLayerEng).

```bash
# one-time setup from the repo root: uv sync   (see ../README.md)
export OPENAI_API_KEY=...        # Windows PowerShell: $env:OPENAI_API_KEY="..."
uv run python voice_agent.py question.wav reply.mp3
```

Example output (timings depend on your network, region and models):

```text
heard: Are you open on Sunday?
said:  No, we're closed on Sundays. We're open Saturday from ten to four.
audio: reply.mp3
stt 0.58s  llm 1.21s  tts 0.66s | total 2.45s (budget 3.0s)
```

## The audio file

`question.wav` is a short sample ("Are you open on Sunday?", generated with a free text-to-speech
voice), so you can run the demo right away. To ask your own question, record a few seconds of
speech and save it as a WAV (or MP3/M4A) file:

- **Windows:** the Sound Recorder app, then pass the saved file (it saves `.m4a`, which works too).
- **macOS:** QuickTime Player > File > New Audio Recording, export, then pass the file.
- **Linux:** `arecord -d 4 -f cd my-question.wav`
- **Any OS:** [Audacity](https://www.audacityteam.org/) > record > File > Export > WAV.

```bash
uv run python voice_agent.py my-question.wav reply.mp3
```

Keep recordings short (one question), and don't commit your own voice: `.gitignore` skips
audio files except this sample.

Model names are environment variables (`STT_MODEL`, `TTS_MODEL`, `TTS_VOICE`, `MODEL`) because audio
models change often. **Check the current OpenAI audio docs before relying on the defaults**: the
endpoint names used here (`audio.transcriptions.create`, `audio.speech.create`) were not re-verified
for this release. To use another provider, write one adapter function with the same shape.

## Tests (no microphone, no key)

```bash
uv run pytest -q                 # pip: pytest -q (with the venv active)
```

Exercises and quiz: [exercises.md](exercises.md), [quiz.md](quiz.md). Next: multi-agent systems.
