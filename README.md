# Demo MCP Server

A minimal Model Context Protocol server in Python that exposes one tool, one resource, and one prompt.

## 1. Install

```powershell
cd C:\ClaudeCode\MCP
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Smoke test (optional)

The official inspector launches a web UI to poke at the server:

```powershell
mcp dev server.py
```

## 3. Register with Claude Code

From any directory, run:

```powershell
claude mcp add demo-server -- C:\ClaudeCode\MCP\.venv\Scripts\python.exe C:\ClaudeCode\MCP\server.py
```

The `--` separates Claude Code flags from the command to launch the server.

## 4. Verify

```powershell
claude mcp list
```

Inside a Claude Code session, type `/mcp` to confirm `demo-server` is connected. You can then ask Claude things like:

- "Use the demo-server add tool to add 17 and 25."
- "Fetch the demo://greeting/Durga resource."
- "Run the summarize prompt for 'quantum computing'."

## 5. Remove (when done)

```powershell
claude mcp remove demo-server
```
