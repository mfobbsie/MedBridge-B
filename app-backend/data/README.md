# caduceus-web

**Caduceus Healthcare Equity Decision Intelligence Platform**  
Next.js 14 · TypeScript · Tailwind CSS · Rhenman & Partners

---

## What this is

The production React frontend for Caduceus. Not a dashboard — an institutional healthcare equity operating system that continuously prioritizes analyst and PM attention.

Architecture: workflow-centric. Every surface is entered through a named workflow (AM_TRIAGE, EARNINGS_PREP, THESIS_CHECK, PM_EXPOSURE). The workflow rail persists across navigation. Decisions are captured in context with breadcrumb, evidence pins, and materiality scores attached automatically.

---

## V1 surfaces (live)

| Surface | Data source | Status |
|---|---|---|
| Attention workbench | catalyst_events, beat/miss, EDGAR signals | ✓ Live |
| Earnings workbench | catalyst_events (200 rows, 8 tickers) | ✓ Live |
| Decision registry | FastAPI Module 5 (mock in V1) | ✓ Live |
| Portfolio workbench | Portfolio weights + P&L | ✓ Live |
| Thesis check sheet | Records to FastAPI | ✓ Live |
| Workflow state machine | WorkflowContext (client state) | ✓ Live |
| Materiality scorer | Deterministic algorithm | ✓ Live |
| CopilotStrip | Silent below m60, dismissable | ✓ Live |

## V2 surfaces (planned)

| Surface | Data source |
|---|---|
| Company workbench | EDGAR financials, CT.gov pipeline, Orange Book LOE |
| Filing delta signals | 10-K text extraction (EDGAR EFTS) |
| Thesis registry | Analyst-populated via UI |
| AI copilot panel | Anthropic API + pgvector RAG |
| Risk workbench | Orange Book patent cliff, IRA exposure |
| Events workbench | FDA calendar, healthcare conferences |

---

## Setup

```bash
npm install
npm run dev
```

Opens at http://localhost:3000

For Vercel deployment:
```bash
npm run build
vercel deploy
```

---

## Design system

- **Canvas:** `#F5F2EC` ivory
- **Rail:** `#1A1D24` charcoal
- **Accent:** `#3E6B89` muted blue
- **Deterioration:** `#9C3A2A` terracotta
- **Escalation:** `#B07A2E` ochre
- **Intact:** `#3F6B4E` forest
- **Fonts:** IBM Plex Serif (headings) · Inter (body) · JetBrains Mono (tabular)

---

## Architecture

```
src/
  app/
    layout.tsx          Root layout — sidebar, topnav, workflow rail
    page.tsx            Redirects to /attention
    attention/          Attention workbench — priority queue + reasoning + evidence
    earnings/           Earnings calendar + beat/miss
    decisions/          Decision registry
    portfolio/          Holdings + P&L
    companies/          Company workbench (V2)
    risks/              Risk workbench (V2)
    events/             Events calendar (V2)
  components/
    app-sidebar.tsx     Navigation rail
    top-nav.tsx         Top header with coverage selector + copilot toggle
    workflow-rail.tsx   Persistent workflow state strip
    workbench-shell.tsx 3-panel layout (280 / flex / 320)
    copilot-strip.tsx   Inline AI — silent below m60
    thesis-check-sheet.tsx  Decision capture bottom sheet
  lib/
    workflow/
      types.ts          Shared workflow types
      workflow-context.tsx  State machine
      materiality.ts    Deterministic scorer
    data/
      mock.ts           V1 mock data + real catalyst_events data
    utils.ts            cn() utility
```
