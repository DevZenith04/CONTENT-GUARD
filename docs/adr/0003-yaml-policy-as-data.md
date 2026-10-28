# ADR 0003: YAML Policy Specification as Configuration

## Context
Policy updates and rule tuning frequently need to be executed by Trust & Safety operators and policy managers who may not be Python engineers. Hardcoding rules inside application logic prevents rapid adjustments during emerging safety incidents.

## Decision
All moderation rules, category definitions, regular expressions, severity thresholds, and policy versions are isolated in `backend/config/rules.yaml`. The rule engine parses this configuration dynamically on startup.

## Alternatives Considered
- **Database-Stored Rules**: Dynamic without restarts, but lacks version control, git auditability, and peer review via pull requests.
- **Hardcoded Python Regex**: Inflexible and risks introducing regression bugs when non-engineers edit code.

## Consequences
- **Positive**: Auditable via Git, easily reviewed in PRs, versioned by `policy_version`, tunable without code changes.
- **Negative**: Requires application reload to pick up configuration changes (handled cleanly in dev with `--reload`).
