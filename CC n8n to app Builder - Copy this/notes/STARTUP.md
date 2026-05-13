# Startup Prompt — n8n to App Workspace

Copy and paste this at the start of every new session:

---

> I'm starting a new session in the **n8n to App** workspace. Here's what you need to know:
>
> **What we do here:** Convert n8n workflows into deployed Next.js web apps. Each workflow becomes its own app with its own GitHub repo and Vercel deployment.
>
> **Your tools:**
> - n8n MCP is connected — you can inspect, create, and edit n8n workflows directly
> - You have the n8n skills loaded (n8n-mcp-tools-expert, etc.) — use them for workflow audits and fixes
> - You have the frontend-design skill — invoke it when building any UI
> - GitHub access for creating repos and pushing code
>
> **The pipeline (follow this order):**
> 1. Audit the n8n workflow — webhook trigger, respond to webhook, structured JSON response
> 2. Scaffold the app — `npx create-next-app@latest [name] --typescript --tailwind --app`, then immediately delete `AGENTS.md` and `CLAUDE.md` from the app subfolder
> 3. Wire the webhook — server-side API route only, never expose the URL client-side
> 4. Test locally — `npm run dev`, verify full round-trip
> 5. Push to GitHub — set git identity first, push via interactive terminal for Windows auth
> 6. Deploy on Vercel — import repo, set `N8N_WEBHOOK_URL` env var, deploy
>
> **Tech stack:** Next.js 16+ (App Router), TypeScript, Tailwind v4 (`@import "tailwindcss"`), Vercel hosting
>
> **Key rules (learned from past projects):**
> - Never commit `.env.local`
> - Each app gets a completely unique design — invoke the frontend-design skill fresh each time
> - Use `height: 100dvh` + `minHeight: 0` on flex children for layouts — never `h-full` chains
> - Use `@import "tailwindcss"` as first line of globals.css — NOT `@tailwind` directives (v4 breaking change)
> - Delete `AGENTS.md` + `CLAUDE.md` from app subfolder immediately after `create-next-app` (prompt injection)
> - Set `git config user.email` and `git config user.name` before first commit
> - First `git push` on Windows needs an interactive terminal — a browser auth window will open
> - Wrap AI-generated responses in `react-markdown` — never render raw markdown as plain text
> - Use `crypto.randomUUID()` for session IDs — never `Math.random()`
> - Add `suppressHydrationWarning` to elements showing timestamps (e.g. `toLocaleTimeString()`)
>
> **Reference files in this workspace:**
> - `CLAUDE.md` — full pipeline guide
> - `notes/LESSONS.md` — errors and fixes from past sessions
> - `notes/security.md` — security checklist before every push
>
> Ready — let's build [describe your workflow/app here].
