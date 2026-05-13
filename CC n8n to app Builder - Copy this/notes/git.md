# Git Setup — First-Time Steps

## Before first commit (required once per machine)
```bash
git config user.email "your@email.com"
git config user.name "YourGitHubUsername"
```
Without this, `git commit` fails with "Author identity unknown".

## First push to GitHub (Windows)
Run this in an **interactive terminal** (VS Code terminal or Windows Terminal):
```bash
git push -u origin master
```
A **browser window will open** asking you to sign into GitHub. Sign in once — Windows saves your credentials automatically. All future pushes will work without prompting.

## Does NOT work
- Running `git push` as a background process (no browser window can open)
- Expecting it to work silently on first run

## Full init sequence for a new app
```bash
git init
git remote add origin https://github.com/[username]/[repo].git
git config user.email "your@email.com"
git config user.name "YourGitHubUsername"
git add [files]
git commit -m "Initial commit"
git push -u origin master   # opens browser for auth
```
