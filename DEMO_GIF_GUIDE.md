# Demo GIF Guide

> Create professional demo GIFs for OpenPaper AI.

## Tools

### Recommended: ScreenToGif (Windows)
Free, open-source screen recorder with built-in GIF editor and optimization.

**Download:** [ScreenToGif](https://www.screentogif.com/)

### Alternative: KeyCastr + GIPHY Capture (macOS)
- [KeyCastr](https://github.com/keycastr/keycastr) — Keystroke visualizer
- [GIPHY Capture](https://giphy.com/apps/giphycapture) — Lightweight GIF recorder

### Alternative: peek (Linux)
```bash
sudo apt install peek
```

## Setup

1. Start the platform:

```bash
docker compose up -d
```

2. Open `http://localhost:3000` in a clean browser window (1920×1080 recommended)
3. Log in with demo credentials
4. Close all other tabs and applications

## Recording Specifications

| Setting | Value |
|---|---|
| Resolution | 1920×1080 (scaled to 960×540 for GIF) |
| Frame rate | 15 FPS |
| Color depth | 256 colors (optimized) |
| Duration | 8–15 seconds per clip |
| File size | < 5 MB per GIF |

## Demo Scenarios

### 1. Workflow Builder (15s)
1. Navigate to Workflows → Create new
2. Drag trigger node → add agent node → connect
3. Click Save → Execute
4. Show run result in Runs panel

**Key actions:** Drag, connect, click, execute

### 2. Agent Chat with Streaming (10s)
1. Navigate to Chat
2. Select an existing chat or create new
3. Type a prompt and press Enter
4. Show SSE streaming token-by-token output

**Key actions:** Type, submit, watch streaming

### 3. Marketplace Install (10s)
1. Navigate to Marketplace → Agents
2. Search for "export"
3. Click Install on Export Agent
4. Show success status and installed badge

**Key actions:** Search, click install, status change

### 4. CLI Doctor (8s)
```bash
openpaper doctor --verbose
```
Terminal recording with dark theme, 120×40 character window.

**Key actions:** Type command, show diagnostic output

### 5. Analytics Dashboard (12s)
1. Navigate to Analytics
2. Show 15s auto-refresh cycle
3. Hover over charts and KPIs

**Key actions:** Navigation, hover interactions

## Optimization Tips

1. **Crop tightly** — Remove browser chrome, address bar, and excess whitespace
2. **Reduce colors** — Use 256-color palette for smaller file size
3. **Remove idle frames** — Cut out waiting/loading pauses
4. **Add cursor highlights** — Use ScreenToGif's cursor effects or a separate tool
5. **Loop once** — Configure GIF to play once or loop 2-3 times (not infinite)

## Publishing

1. Place optimized GIFs in the `screenshots/` directory
2. Naming convention: `demo-{scenario}.gif` (e.g., `demo-workflow-builder.gif`)
3. Reference in README.md using:

```markdown
![Workflow Builder Demo](screenshots/demo-workflow-builder.gif)
```

## Example: README Badge

Add a "Watch Demo" badge linking to a specific GIF:

```markdown
[![Watch Demo](https://img.shields.io/badge/-Watch%20Demo-6366f1?style=flat)](#demo)
```
