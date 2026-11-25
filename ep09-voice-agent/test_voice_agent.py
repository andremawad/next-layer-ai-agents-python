"""Tests for Episode 9. No API key, no audio hardware: every stage is a fake.  Run:  pytest -q"""
from pathlib import Path
from types import SimpleNamespace

from voice_agent import SYSTEM, VoiceAgent, for_speech, openai_stt, openai_tts


def fake_tts(text, out_path):
    Path(out_path).write_bytes(b"ID3fake")
    return Path(out_path)


def ticking_clock():
    t = [0.0]

    def now():
        t[0] += 0.5
        return t[0]
    return now


def test_one_turn_end_to_end(tmp_path):
    seen = []
    agent = VoiceAgent(stt=lambda p: " Are you open Sunday? ",
                       llm=lambda msgs: seen.append(list(msgs)) or "**No**, we're closed on Sundays.",
                       tts=fake_tts, clock=ticking_clock())
    turn = agent.turn(tmp_path / "in.wav", tmp_path / "out.mp3")
    assert turn.heard == "Are you open Sunday?"
    assert turn.said == "No, we're closed on Sundays."          # markdown stripped for speech
    assert turn.audio.read_bytes() == b"ID3fake"
    assert set(turn.timings) == {"stt", "llm", "tts"} and turn.total == 1.5
    assert seen[0][0]["content"] == SYSTEM


def test_silence_skips_llm_and_tts(tmp_path):
    called = []
    agent = VoiceAgent(stt=lambda p: "   ", llm=lambda m: called.append("llm") or "x",
                       tts=lambda t, o: called.append("tts"))
    turn = agent.turn(tmp_path / "in.wav", tmp_path / "out.mp3")
    assert turn.audio is None and called == []


def test_history_grows_across_turns(tmp_path):
    agent = VoiceAgent(stt=lambda p: "hi", llm=lambda m: "hello", tts=fake_tts)
    agent.turn(tmp_path / "a.wav", tmp_path / "a.mp3")
    agent.turn(tmp_path / "b.wav", tmp_path / "b.mp3")
    assert [m["role"] for m in agent.history] == ["system", "user", "assistant", "user", "assistant"]


def test_for_speech_caps_at_sentence_end():
    long = "One. " * 200
    out = for_speech(long, max_chars=50)
    assert len(out) <= 50 and out.endswith(".")


def test_openai_adapters_call_the_right_endpoints(tmp_path):
    audio_in = tmp_path / "q.wav"
    audio_in.write_bytes(b"RIFF")
    fake = SimpleNamespace(audio=SimpleNamespace(
        transcriptions=SimpleNamespace(create=lambda model, file: SimpleNamespace(text="hello")),
        speech=SimpleNamespace(create=lambda model, voice, input: SimpleNamespace(content=b"mp3"))))
    assert openai_stt(fake)(audio_in) == "hello"
    assert openai_tts(fake)("hi", tmp_path / "r.mp3").read_bytes() == b"mp3"
