# ADR 0004: Routing Self-Harm Content to Review Instead of Auto-Block

## Context
Self-harm and suicidal ideation are critical public health concerns. When users post messages expressing distress or suicidal intent, automated blocking actions can silence individuals in acute crisis, disconnect them from support communities, or exacerbate distress.

## Decision
ContentGuard **never automatically blocks (`BLOCK`) self-harm content**. Instead:
1. Self-harm signals are immediately escalated to prioritized human review (`REVIEW`).
2. Crisis intervention support resources (e.g. 988 Suicide & Crisis Lifeline) are surfaced in API responses and interface headers for immediate help.

## Alternatives Considered
- **Auto-Block on Keyword Match**: Dangerous to vulnerable users; treats cries for help as punitive platform violations.
- **Ignore / Allow**: Unacceptable risk; leaves critical user distress undetected.

## Consequences
- **Positive**: Empathetic, safety-first intervention that preserves outreach channels and surfaces emergency help.
- **Negative**: Increases human reviewer queue volume for self-harm events, requiring dedicated protocol handling.
