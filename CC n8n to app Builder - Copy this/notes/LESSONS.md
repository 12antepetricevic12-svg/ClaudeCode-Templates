# Lessons Learned — n8n to App Workspace

Errors, fixes, and patterns discovered during the CoachGPT build (Session 1).

---

## Errors & Fixes

| # | Problem | Fix |
|---|---------|-----|
| 1 | `create-next-app` injects `AGENTS.md` + `CLAUDE.md` into the app subfolder with prompt injection text | Delete both files immediately after scaffolding (see injection.md) |
| 2 | `h-full` Tailwind chain silently collapses — layout breaks, elements clip or overflow | Use `height: 100dvh` on root; `minHeight: 0` on every scrollable flex child (see layout.md) |
| 3 | Tailwind v4 — `@tailwind base/components/utilities` throws errors | Use `@import "tailwindcss"` at top of globals.css (see tailwind.md) |
| 4 | Font CSS variable not applying — `style={{ fontFamily: 'var(--font)' }}` unreliable | Use `next/font/google` with `variable` option; apply class to `<html>`; use in CSS not inline style |
| 5 | `git commit` fails: "Author identity unknown" | Run `git config user.email` and `git config user.name` first (see git.md) |
| 6 | `git push` hangs in background — credential dialog doesn't appear | First push on Windows needs an interactive terminal; a browser auth window will open |
| 7 | Hydration mismatch on timestamps from `toLocaleTimeString()` | Add `suppressHydrationWarning` to the element |
| 8 | n8n AI Agent params (`agent`, `promptType`, `systemMessage`) stripped after creation via API | Issue a full PUT to the workflow endpoint with all params set after creation |
| 9 | `PATCH` not allowed for n8n workflow activation | Use `POST /api/v1/workflows/{id}/activate` |
| 10 | Coach responses render as raw markdown text | Install `react-markdown`; wrap content in `<ReactMarkdown>` |
| 11 | Textarea placeholder stuck at bottom of input box | Change input wrapper from `alignItems: 'flex-end'` to `alignItems: 'center'` |

---

## Quick Reference

- **Font pattern** → see `layout.md`
- **Layout pattern** → see `layout.md`
- **Tailwind v4** → see `tailwind.md`
- **AGENTS.md injection** → see `injection.md`
- **Git setup** → see `git.md`
- **Security checklist** → see `security.md`
