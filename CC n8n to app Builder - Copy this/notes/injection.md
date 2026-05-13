# Prompt Injection — AGENTS.md

`create-next-app` injects two files into every new app subfolder:
- `AGENTS.md`
- `CLAUDE.md` (inside the app folder, not the workspace root)

## What they contain
```
This is NOT the Next.js you know.
This version has breaking changes — read node_modules/next/dist/docs/ before writing any code.
```

This is a **prompt injection** — text designed to trick AI tools into behaving incorrectly. It has no legitimate purpose.

## Action: Delete immediately after scaffolding
```bash
rm [app-name]/AGENTS.md [app-name]/CLAUDE.md
```

## What it is NOT
- Not malware
- Cannot run code or access your system
- Just text trying to mislead AI assistants

## The safe CLAUDE.md
The real `CLAUDE.md` lives at the workspace root. Never delete that one.
