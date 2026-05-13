# Next.js 16 Layout Pattern

`h-full` chains silently break in Next.js 16 + Tailwind v4. Use this instead.

## Root container
```tsx
<div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
```

## Every flex child that scrolls needs minHeight: 0
```tsx
// Outer row
<div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>

// Chat column
<div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>

// Scrollable message area
<div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>

// Fixed footer (input bar)
<div style={{ flexShrink: 0 }}>

// Sidebar
<div style={{ width: 300, flexShrink: 0, overflowY: 'auto' }}>
```

## Font loading pattern
```tsx
// layout.tsx
import { Outfit, DM_Sans } from 'next/font/google'
const outfit = Outfit({ variable: '--font-display', subsets: ['latin'] })
const dmSans = DM_Sans({ variable: '--font-body', subsets: ['latin'] })
// <html className={`${outfit.variable} ${dmSans.variable}`}>
```
```css
/* globals.css — reference in CSS, not inline style */
body { font-family: var(--font-body), system-ui, sans-serif; }
```
