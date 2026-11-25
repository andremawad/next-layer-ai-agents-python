"""Episode 8: Deploy a Python AI agent as an API (FastAPI + Docker).

    pip install -r requirements.txt
    set OPENAI_API_KEY, then:  fastapi dev app.py        (or: docker build -t agent-api . )

Endpoints:  GET /health   POST /chat   POST /chat/stream (Server-Sent Events)
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import agent_core

app = FastAPI(title="AI agent API")
sessions = agent_core.Sessions()


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=64)


class ChatOut(BaseModel):
    answer: str
    session_id: str


@lru_cache
def get_llm():
    """One client per process. Tests swap it with app.dependency_overrides."""
    return agent_core.make_client()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn, llm=Depends(get_llm)) -> ChatOut:
    sessions.add(body.session_id, "user", body.message)
    text = agent_core.answer(sessions.history(body.session_id), llm)
    sessions.add(body.session_id, "assistant", text)
    return ChatOut(answer=text, session_id=body.session_id)


@app.post("/chat/stream")
def chat_stream(body: ChatIn, llm=Depends(get_llm)) -> StreamingResponse:
    history = sessions.history(body.session_id) + [{"role": "user", "content": body.message}]
    return StreamingResponse(agent_core.stream_sse(history, llm), media_type="text/event-stream")
