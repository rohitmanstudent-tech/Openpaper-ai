---
name: Bug report
about: Create a report to help us improve OpenPaper AI
title: "[Bug] "
labels: bug, triage
assignees: ""
---

## Bug Description

A clear and concise description of what the bug is.

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened, including error messages, stack traces, or unexpected behavior.

## Screenshots / Logs

If applicable, add screenshots or log output to help explain your problem.
Include correlation IDs from JSON log entries if available.

## Environment

- **Deployment:** Docker Compose / Development / CLI-only
- **OpenPaper Version:** v1.0.0-rc.1 (check `/api/health` or `openpaper doctor`)
- **OS:** [e.g., Ubuntu 24.04, macOS 15, Windows 11]
- **Browser:** [e.g., Chrome 125, Firefox 130] (if frontend issue)
- **Python Version:** [e.g., 3.12.10] (if backend/CLI issue)
- **Node Version:** [e.g., 20.15] (if frontend dev)

## Configuration

Relevant environment variables or config settings (redact secrets):

```env
DATABASE_URL=postgresql+asyncpg://...
LOG_LEVEL=debug
```

## Additional Context

- Does this happen consistently or intermittently?
- Does it affect a specific agent, workflow, or provider?
- Have you tried any workarounds?

## Correlation ID

If available from JSON logs: `correlation_id: "uuid-here"`
