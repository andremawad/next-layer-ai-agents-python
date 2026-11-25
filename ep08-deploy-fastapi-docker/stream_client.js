// Episode 8: read the /chat/stream SSE feed from a browser or Node 18+.
// EventSource only does GET, so for a POST we read the response body as a stream.
export async function streamChat(message, onToken, base = "http://localhost:8000") {
  const res = await fetch(`${base}/chat/stream`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop();                    // keep a half-received event for later
    for (const event of events) {
      const data = event.replace(/^data: /, "");
      if (data === "[DONE]") return;
      onToken(JSON.parse(data).token);
    }
  }
}
