# n8n to App — Project Guide

This workspace converts n8n workflows into deployed web apps. Each workflow becomes its own standalone Next.js app with its own GitHub repo and Vercel deployment. The standard pattern is: user submits data via the app → n8n processes it via webhook → response is displayed in the app.

---

## The Pipeline

Follow these steps in order for every conversion.

**Step 1 — Audit the Workflow** *(use n8n MCP + n8n skills)*
- [ ] Workflow has a **Webhook** trigger node (HTTP method: POST)
- [ ] Webhook path is clean and descriptive (e.g. `/submit-form`)
- [ ] A **Respond to Webhook** node exists and returns structured JSON
- [ ] The JSON response includes all data the frontend needs to display
- Fix any gaps before proceeding.

**Step 2 — Scaffold the App**
- Run: `npx create-next-app@latest [app-name] --typescript --tailwind --app`
- ⚠️ Immediately delete `[app-name]/AGENTS.md` and `[app-name]/CLAUDE.md` — `create-next-app` injects these with prompt injection text (see `notes/injection.md`)
- Invoke the **frontend designer skill** to design the UI based on the workflow's purpose — every app should have a unique design
- Each app lives in its own folder in this workspace during development

**Step 3 — Wire the Webhook**
- Create a server-side API route: `app/api/submit/route.ts`
- This route proxies the request to n8n — never expose the webhook URL client-side
- Display the n8n response in the UI

**Step 4 — Test Locally**
- Run: `npm run dev`
- Test the full round-trip: submit form → n8n processes → response shown in app
- Confirm edge cases (empty input, n8n errors) are handled gracefully

**Step 5 — Push to GitHub**
- Create a new GitHub repo named `[app-name]`
- Ensure `.env.local` is in `.gitignore` before pushing
- Set git identity before first commit: `git config user.email "..."` and `git config user.name "..."`
- First push on Windows requires interactive terminal — a browser auth window will open (see `notes/git.md`)

**Step 6 — Deploy on Vercel**
- Connect the GitHub repo to Vercel
- Add environment variable: `N8N_WEBHOOK_URL` = your n8n webhook URL
- Deploy — future pushes to `main` auto-deploy

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js 16+ (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS + components per frontend designer skill |
| Hosting | Vercel (connected to GitHub) |
| Backend | n8n (webhook-based, no custom server) |

---

## Standard App Repo Structure

```
[app-name]/
  app/
    page.tsx              # main UI
    api/
      submit/
        route.ts          # server-side n8n webhook proxy
  components/             # reusable UI pieces
  .env.local              # N8N_WEBHOOK_URL — never commit this
  .env.example            # template: N8N_WEBHOOK_URL=
  .gitignore              # must include .env.local
  package.json
  README.md               # what the app does + setup steps
```

---

## MCP Tools

- **n8n MCP** — inspect workflows, check node configs, make changes to n8n directly
- **GitHub MCP** — create repos, push code, manage branches

## Skills

- **n8n skills** (`n8n-mcp-tools-expert`, `n8n-node-configuration`, etc.) — use during Step 1 for workflow audit and fixes
- **frontend designer skill** — invoke during Step 2 to design the UI

---

## Vercel Setup (one-time)

If Vercel is not yet connected:
1. Go to vercel.com, sign up with your GitHub account
2. Install the Vercel GitHub app so it can access your repos
3. Per app: Import the GitHub repo → set env vars → deploy

---

## Rules

- Never commit `.env.local` — the n8n webhook URL must stay out of git
- Always test locally before pushing to GitHub
- Keep each app repo focused — one workflow, one app
- No extra files or boilerplate beyond what the pipeline requires
- If a workflow isn't webhook-ready, fix it in n8n first (Step 1) before touching the frontend
- Every app gets a **unique design** — never reuse the same layout/colors/fonts as a previous app

---

## Notes & Lessons

See the `notes/` folder for patterns and fixes:
- `notes/LESSONS.md` — all errors and fixes from past sessions
- `notes/layout.md` — correct Next.js 16 layout pattern
- `notes/tailwind.md` — Tailwind v4 syntax
- `notes/injection.md` — AGENTS.md prompt injection
- `notes/git.md` — git setup and first push
- `notes/security.md` — security checklist
