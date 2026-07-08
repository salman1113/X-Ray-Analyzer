# AI X-Ray Analyzer — Frontend

React SPA for the AI X-Ray Analyzer platform.

## Stack

- React 19 + Vite 8
- Tailwind CSS 4
- React Router DOM 7
- Framer Motion
- Lucide React (icons)
- @simplewebauthn/browser (passkey auth)

## Setup

```bash
npm install
npm run dev
```

Runs at `http://localhost:5173`

## Build

```bash
npm run build
```

Output in `dist/` — deploy to any static host (Vercel, Netlify, S3).

## Design System

Pinterest-inspired warm cream palette:

- **Primary (red):** `#e60023` — CTAs only
- **Surface:** `#fbfbf9` (bg), `#f6f6f3` (cards), `#ffffff` (nav/modals)
- **Text:** `#000000` (ink), `#62625b` (mute), `#91918c` (ash)
- **Radii:** 16px (cards/buttons), 32px (modals), pill (chips/search)
- **Font:** Inter (400/500/600/700)
- **No shadows on cards** — flat with hairline borders

## Responsive

- **Mobile (< 768px):** bottom tab bar + hamburger drawer
- **Desktop (≥ 768px):** fixed sidebar + spacious content

## Environment

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```
