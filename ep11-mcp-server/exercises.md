# Ep11 exercises: MCP server and host

Work in this folder. `pytest -q` runs the server in-process, so there's no subprocess, no network and no key.
Solutions were run against `mcp` 2.3.

## Exercise 1 (in the video): a tool the host must approve

Add a read-only `find_free_slots(day)` tool to the server that returns `[]` on closed days and
`["10:30", "13:00", "15:30"]` otherwise. Run `python mcp_agent.py "Any free slots on Monday?"` first
**without** changing the host: it asks you before using the new tool. That's the default deny working.
Then read the tool, decide it's safe, and allowlist it. Add these tests to `test_mcp_agent.py`:

```python
@pytest.mark.anyio
async def test_free_slots_runs_without_asking():
    llm = FakeLLM(reply(calls=[("find_free_slots", {"day": "monday"})]), reply("10:30 is free."))
    async with Client(make_server()) as mcp:
        agent = McpAgent(mcp, client=llm, log=lambda _: None)
        await agent.ask("free on monday?")
    assert agent.pending is None
    assert tool_results(llm) == [{"ok": True, "result": ["10:30", "13:00", "15:30"]}]


@pytest.mark.anyio
async def test_no_slots_when_closed():
    async with Client(make_server()) as mcp:
        r = await mcp.call_tool("find_free_slots", {"day": "Sunday"})
    assert r.structured_content == {"result": []}
```

<details><summary>Solution</summary>

In `make_server`, next to the other tools:

```python
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def find_free_slots(day: str) -> list[str]:
        """Free appointment times on one weekday, for example 'monday'."""
        if HOURS.get(day.strip().lower()) == "closed":
            return []
        return ["10:30", "13:00", "15:30"]
```

In `mcp_agent.py`:

```python
AUTO_RUN = {"get_opening_hours", "list_bookings", "find_free_slots"}
```

`test_server_tools_become_openai_tools` now fails because it lists exactly three tools. Add
`"find_free_slots"` to its expected set. A test that notices a new tool is a good thing: it's the
test-suite version of the host's allowlist.
</details>

## Exercise 2: put the policy resource in the prompt

Resources are data the host can load into context. Make `McpAgent.ask` read `clinic://policy` and
append it to the system prompt, so "Is there a fee if I cancel today?" can be answered without a tool call.

<details><summary>Solution</summary>

```python
    async def ask(self, text: str) -> str:
        if not self.tools:
            await self.load_tools()
        policy = (await self.mcp.read_resource("clinic://policy")).contents[0].text
        llm = self.client or make_client()
        messages: list = [
            {"role": "system", "content": "You help a patient with clinic bookings. Use the tools.\n"
                                          f"Clinic policy: {policy}"},
            {"role": "user", "content": text}]
        ...
```

Test idea: with a `FakeLLM` that replies straight away, assert that `"$50"` appears in
`llm.requests[0]["messages"][0]["content"]`. In a real host, cache the resource instead of
reading it on every question.
</details>

## Exercise 3: audit a server before you trust it

Write `audit.py` that connects to a server (ours, or any local MCP server you have), and prints every
tool's name, description and annotations. Then write down which tools you'd put in `AUTO_RUN` and why.

<details><summary>Solution</summary>

```python
import asyncio
from mcp import Client
from mcp_agent import server_params


async def main():
    async with Client(server_params()) as mcp:
        for t in (await mcp.list_tools()).tools:
            a = t.annotations
            print(f"{t.name}: read_only={a.read_only_hint if a else None} "
                  f"destructive={a.destructive_hint if a else None}\n    {t.description}")

asyncio.run(main())
```

For our server: `get_opening_hours` and `list_bookings` are reads of the current patient's own data,
so they're safe to auto-run. `cancel_booking` changes data, so it needs a yes. Also read each
description for instructions aimed at the model ("always call this first", "ignore previous rules").
That's tool poisoning, a form of prompt injection, and a reason not to connect that server at all.
</details>
