# Working conventions

## Commits

Format: `type(ref): description`

- `ref` is a spec ID (`FR-04`, `NFR-02`), a prompt round (`round-3`),
  or a report section (`report-s5`)
- types: feat, fix, test, docs, spec, vibe, chore

Examples:
- `vibe(round-3): add login endpoint`
- `feat(FR-04): reject overlapping bookings`
- `test(FR-04): overlap edge cases`
- `docs(report-s2): non-functional requirements`

## Workflow

- Every change goes through a pull request; no direct pushes to main
- Every PR links an issue (`Closes #12`)
- Commit from your own GitHub account
- Never edit `vibe/` after it is marked frozen
