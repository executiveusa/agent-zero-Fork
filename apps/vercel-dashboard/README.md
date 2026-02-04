# Vercel Dashboard - Agent Zero

Mobile-first Next.js dashboard for Agent Zero with BFF (Backend for Frontend) architecture.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Architecture

- **Frontend**: Next.js 14 + React 18 + TypeScript + Tailwind CSS
- **BFF**: Server-side proxy routes at `/api/az/*`
- **State**: Real-time polling (750ms) from Agent Zero backend
- **Auth**: NextAuth.js (ready to configure)

## Environment Variables

Copy `.env.example` to `.env.local`:

```
AZ_BASE_URL=http://localhost:50001
AZ_API_KEY=your-api-key
NEXTAUTH_SECRET=your-secret
```

## Features

✅ Mobile-first responsive design
✅ Real-time polling integration
✅ BFF proxy for backend communication
✅ Operational state indicators (7 states)
✅ Mission Control landing page
✅ Navigation to Chats, Tasks, Settings

## Build

```bash
npm run build
npm start
```

## Deployment

```bash
vercel deploy
```
