# Security Checklist — Every App

Run through this before pushing to GitHub.

## Before git push
- [ ] `.env.local` is listed in `.gitignore`
- [ ] No API keys in any `.ts` / `.tsx` / `.js` file
- [ ] Webhook URL is server-side only (in `app/api/` route, not `app/page.tsx`)
- [ ] No `NEXT_PUBLIC_` prefix on anything sensitive

## API route (`app/api/submit/route.ts`)
- [ ] Input type-checked (`typeof message !== 'string'`)
- [ ] Empty/null checked (`!message.trim()`)
- [ ] Webhook URL not exposed in response or error messages

## Frontend
- [ ] `react-markdown` used for any AI-generated content (safe by default, no HTML rendering)
- [ ] No `dangerouslySetInnerHTML` on untrusted content

## n8n
- [ ] AI API keys stored in n8n credential store — never in app code
- [ ] Webhook path is clean and not guessable (e.g. `/fitness-coach` not `/webhook`)

## Notes
- Session IDs: use `crypto.randomUUID()` — never `Math.random()`
- localStorage is client-writable — fine for XP/prefs, not for anything security-sensitive
