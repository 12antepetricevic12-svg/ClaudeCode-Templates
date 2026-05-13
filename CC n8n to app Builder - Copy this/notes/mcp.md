# n8n MCP Connection — Troubleshooting

If `n8n_health_check`, `search_nodes`, or any `mcp__n8n-mcp__*` tool returns "tool not found" (or simply doesn't appear in Claude's tool list), the MCP bridge isn't connected to this session. Follow the fix below.

---

## How to detect it's broken

Any one of these is a signal:

1. In Claude Code, run `/mcp`. If `n8n-mcp` is **not listed**, or is listed as failed/disconnected, the bridge isn't running.
2. Ask Claude to call `n8n_health_check` — if Claude reports "tool not available" or similar, the MCP is disconnected.
3. The server is configured in `~/.claude/settings.json` but that doesn't matter — see root cause below.

---

## Root cause (from the first incident)

The Claude Code **VS Code extension** reads MCP configuration from `~/.claude.json`, NOT from `~/.claude/settings.json`. The `settings.json` file is used by the CLI version of Claude Code, but the VS Code extension ignores its `mcpServers` block.

In `~/.claude.json`, each project gets its own `"mcpServers": {}` object. Out of the box these are empty. The fix is to place a workspace-level `.mcp.json` at the project root — Claude Code's extension auto-discovers that file (after a window reload and trust approval).

---

## Fix — 3 steps

### 1. Verify `.mcp.json` exists at the workspace root

Path: `c:\Users\12ant\Desktop\CC n8n to app Jelsa Nautica\.mcp.json`

Confirm with `ls`. If it's present, go to step 2. If it's missing, recreate it using the template below. **You'll need the n8n API key** — copy it from `~/.claude/settings.json` under `mcpServers.n8n-mcp.env.N8N_API_KEY`.

Template (replace the placeholder before saving):

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": [
        "C:\\Users\\12ant\\AppData\\Roaming\\npm\\node_modules\\n8n-mcp\\dist\\mcp\\index.js"
      ],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "https://faroscar.app.n8n.cloud",
        "N8N_API_KEY": "<paste from ~/.claude/settings.json>"
      }
    }
  }
}
```

**Security reminder:** `.mcp.json` contains the n8n API key. It is already listed in this workspace's `.gitignore`. Do not remove that line.

### 2. Reload the VS Code window

`Ctrl+Shift+P` → type "Developer: Reload Window" → Enter.

This is required for Claude Code to re-scan MCP configuration. A plain "new chat" is not enough.

### 3. Approve the MCP trust prompt

On reload, Claude Code usually displays a one-time **trust prompt** for the MCP server defined in `.mcp.json`. Click **Approve**. Without this, the server is loaded but blocked — `/mcp` may list it but no tools will work.

If no prompt appears, check `/mcp` directly to see the server's status and any error message.

---

## Verify it worked

Open a new Claude Code chat in this workspace and send:

> run n8n_health_check

Expected:

```json
{
  "status": "ok",
  "apiUrl": "https://faroscar.app.n8n.cloud",
  "mcpVersion": "2.35.5",
  ...
}
```

If that works, the bridge is live and every `mcp__n8n-mcp__*` tool is callable.

---

## Common failure modes

| Symptom | Likely cause |
|---|---|
| `/mcp` shows `n8n-mcp` as failed/disconnected | Node path in `.mcp.json` is wrong — verify `C:\Program Files\nodejs\node.exe` exists |
| `/mcp` doesn't list `n8n-mcp` at all | `.mcp.json` missing, malformed JSON, or window wasn't reloaded |
| Tools exist but `n8n_health_check` returns auth error | `N8N_API_KEY` in `.mcp.json` is expired or wrong — regenerate via n8n cloud → Settings → API |
| Package not found at startup | Run `npm install -g n8n-mcp` (global package at `%AppData%\npm\node_modules\n8n-mcp`) |

---

## When to run the preflight

Per this workspace's `CLAUDE.md` → Step 1 of the pipeline includes: **before starting a workflow audit**, call `n8n_health_check` once. That's the only time it needs to run proactively. If it works, continue. If it fails, follow this file.

No need to verify MCP status on ordinary prompts — only when you're about to use n8n tools for real work.
