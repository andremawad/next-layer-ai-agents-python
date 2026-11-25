"""Episode 9: Give your AI agent a voice. One voice turn: speech -> text -> agent -> speech.

    pip install openai
    set OPENAI_API_KEY, then:  python voice_agent.py question.wav reply.mp3

Model names are environment variables because audio models change often; check your
provider's current docs (the audio endpoints used here are marked unverified in RESOURCES.md).

Frontend mental model: a voice turn has a latency budget like a page load has Core Web Vitals.
Each stage is timed, the same way you'd read a waterfall in the Network tab.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
STT_MODEL = os.environ.get("STT_MODEL", "whisper-1")
TTS_MODEL = os.environ.get("TTS_MODEL", "tts-1")
TTS_VOICE = os.environ.get("TTS_VOICE", "alloy")
BUDGET_S = 3.0           # target for a whole turn; past this, conversation feels laggy
SYSTEM = ("You are a clinic receptionist on the phone. Answer in one or two short spoken "
          "sentences. No lists, no markdown, no emojis: everything you write is read aloud.")


class STT(Protocol):
    def __call__(self, audio_path: Path) -> str: ...


class TTS(Protocol):
    def __call__(self, text: str, out_path: Path) -> Path: ...


def make_client():
    from openai import OpenAI
    return OpenAI()


# ---------------------------------------------------------------- the three stages
def openai_stt(client=None, model: str = STT_MODEL) -> STT:
    def transcribe(audio_path: Path) -> str:
        c = client or make_client()
        with open(audio_path, "rb") as f:
            return c.audio.transcriptions.create(model=model, file=f).text
    return transcribe


def openai_llm(client=None, model: str = MODEL) -> Callable[[list[dict]], str]:
    def reply(messages: list[dict]) -> str:
        c = client or make_client()
        return c.chat.completions.create(model=model, messages=messages).choices[0].message.content
    return reply


def openai_tts(client=None, model: str = TTS_MODEL, voice: str = TTS_VOICE) -> TTS:
    def speak(text: str, out_path: Path) -> Path:
        c = client or make_client()
        audio = c.audio.speech.create(model=model, voice=voice, input=text)
        Path(out_path).write_bytes(audio.content)
        return Path(out_path)
    return speak


def for_speech(text: str, max_chars: int = 400) -> str:
    """Clean model text for TTS: drop markdown symbols, cap the length at a sentence end."""
    clean = " ".join(text.replace("*", "").replace("#", "").replace("`", "").split())
    if len(clean) <= max_chars:
        return clean
    cut = clean.rfind(".", 0, max_chars)
    return clean[:cut + 1] if cut > 0 else clean[:max_chars]


# ---------------------------------------------------------------- one turn, timed
@dataclass
class Turn:
    heard: str
    said: str
    audio: Path | None
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def total(self) -> float:
        return sum(self.timings.values())


@dataclass
class VoiceAgent:
    stt: STT
    llm: Callable[[list[dict]], str]
    tts: TTS
    history: list[dict] = field(default_factory=lambda: [{"role": "system", "content": SYSTEM}])
    clock: Callable[[], float] = time.perf_counter

    def turn(self, audio_in: Path, audio_out: Path) -> Turn:
        timings: dict[str, float] = {}

        def timed(name, fn, *args):
            t0 = self.clock()
            result = fn(*args)
            timings[name] = self.clock() - t0
            return result

        heard = timed("stt", self.stt, audio_in).strip()
        if not heard:                                  # silence or noise: don't call the LLM
            return Turn("", "", None, timings)
        self.history.append({"role": "user", "content": heard})
        said = for_speech(timed("llm", self.llm, self.history))
        self.history.append({"role": "assistant", "content": said})
        out = timed("tts", self.tts, said, audio_out)
        return Turn(heard, said, out, timings)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python voice_agent.py question.wav reply.mp3")
    client = make_client()
    agent = VoiceAgent(openai_stt(client), openai_llm(client), openai_tts(client))
    t = agent.turn(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"heard: {t.heard}\nsaid:  {t.said}\naudio: {t.audio}")
    print("  ".join(f"{k} {v:.2f}s" for k, v in t.timings.items()),
          f"| total {t.total:.2f}s (budget {BUDGET_S:.1f}s)")
