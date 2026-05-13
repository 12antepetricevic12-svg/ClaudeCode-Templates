# Tailwind v4 — Syntax Change

`create-next-app` in this workspace scaffolds **Tailwind v4**, which has a breaking change.

## Wrong (v3 syntax — will throw errors)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Correct (v4 syntax)
```css
@import "tailwindcss";
```

Put this as the **first line** of `globals.css`. Everything else (CSS vars, keyframes, custom classes) goes below it.

## postcss.config.mjs
Tailwind v4 uses `@tailwindcss/postcss` — no `tailwind.config.js` needed by default.
