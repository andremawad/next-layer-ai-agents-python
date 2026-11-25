# Ep08 exercises: Deploy with FastAPI and Docker

Work in this folder. `pytest -q` needs no key. The HTTP tests need `pip install -r requirements.txt pytest httpx`
(they're skipped otherwise).

## Exercise 1 (in the video): a rate limit per session

Allow 5 `/chat` requests per session per minute; the 6th gets HTTP 429. Put the logic in
`agent_core.py` (no FastAPI there), with an injectable clock.

```python
def test_rate_limiter_allows_five_per_minute():
    now = [0.0]
    rl = agent_core.RateLimiter(limit=5, window=60, clock=lambda: now[0])
    assert all(rl.allow("s") for _ in range(5))
    assert not rl.allow("s")
    assert rl.allow("other")              # limits are per session
    now[0] += 61
    assert rl.allow("s")                  # the window moved on


def test_chat_returns_429(client):
    for _ in range(5):
        client.post("/chat", json={"message": "hi", "session_id": "busy"})
    assert client.post("/chat", json={"message": "hi", "session_id": "busy"}).status_code == 429
```

(For the second test, give the fake LLM at least 5 replies.)

<details><summary>Solution</summary>

In `agent_core.py`:

```python
import time
from collections import defaultdict, deque


class RateLimiter:
    """At most `limit` calls per `window` seconds per key (a sliding window)."""

    def __init__(self, limit: int = 5, window: float = 60.0, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now, q = self.clock(), self.hits[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
```

In `app.py`:

```python
from fastapi import HTTPException
limiter = agent_core.RateLimiter()

# first line of chat():
    if not limiter.allow(body.session_id):
        raise HTTPException(status_code=429, detail="Too many requests, try again in a minute")
```

In the `client` fixture, reset it: `app_module.limiter.hits.clear()`. In production, key the limit
by the authenticated user, not a session id the client chooses.
</details>

## Exercise 2: a timeout on the model call

Make the OpenAI client time out after 20 seconds and turn a timeout into HTTP 504 with a short message.

<details><summary>Solution</summary>

```python
def make_client():
    from openai import OpenAI
    return OpenAI(timeout=20.0)
```

```python
@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn, llm=Depends(get_llm)) -> ChatOut:
    ...
    try:
        text = agent_core.answer(sessions.history(body.session_id), llm)
    except Exception as e:                       # e.g. openai.APITimeoutError
        if "timeout" in type(e).__name__.lower():
            raise HTTPException(504, "The model took too long. Please try again.")
        raise HTTPException(502, "The model service failed. Please try again.")
```

Test it with a fake LLM whose `create` raises `TimeoutError`.
</details>

## Exercise 3: call it from a page

Serve a one-file HTML page that uses `stream_client.js` to show tokens as they arrive. You'll need
CORS if the page is on another origin.

<details><summary>Solution</summary>

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["POST"], allow_headers=["content-type"])
```

```html
<script type="module">
  import { streamChat } from "./stream_client.js";
  const out = document.querySelector("#out");
  streamChat("What time is it in Tokyo?", (t) => (out.textContent += t));
</script>
<pre id="out"></pre>
```

Allow only your own origins; never `allow_origins=["*"]` on an endpoint that spends money.
</details>
