# Ep11 quiz: MCP

Answer from memory, then check. Try again in 3 days without rewatching.

## This episode

1. What do `list_tools` and `call_tool` do?
2. What's the difference between a host, a client and a server in MCP?
3. Why doesn't our host trust `readOnlyHint`?
4. Why must a stdio server never print to stdout?
5. Why does the server read the patient from its environment instead of a tool argument?
6. When should a tool raise `ToolError` instead of any other exception?
7. When are plain functions better than an MCP server?

## Spaced review

8. (Ep03) Why is there no confirm tool in the model's tool list?
9. (Ep02) What does the `{ok, error, hint}` envelope let the model do?
10. (Ep07) How would you check that moving tools into MCP didn't make the agent worse?

---

<details><summary>Answers</summary>

1. `list_tools` returns the server's tools with names, descriptions and JSON schemas; `call_tool` runs one with arguments.
2. The host is the app that runs the model (our `mcp_agent.py`); it uses a client to talk to a server, which owns the tools and data.
3. It's a label from code we may not control. Our own allowlist decides what runs without a human yes.
4. stdout carries the protocol messages; stray text corrupts them. Log to stderr.
5. The model controls tool arguments, so it could ask for anyone's data. Identity must come from the connection.
6. For failures you expect (not found, not allowed): its message reaches the model. Other exceptions count as crashes and only a generic error goes back.
7. One app with a few tools you wrote yourself: an extra process and protocol add nothing.
8. If the model could call confirm, it could approve its own request.
9. Recover: read the error and hint, fix the call, or explain to the user.
10. Run the Ep07 eval suite before and after, and compare pass rates against the baseline.
</details>
