# InCharge Accounting Tools

Claude Code skills, agents, and shared knowledge specific to InCharge's
**accounting/finance domain** — its systems (Business Central, Salesforce,
Ramp, PayFabric, bank feeds), its processes (O2C, P2P, R2R), and its
vocabulary (RSS, EPC, LOB, etc.).

This is the sibling to
[`productivity-tools`](../productivity-tools), which holds
general-purpose tools any department could use (process mapping, and
whatever else follows). The test for which repo something belongs in: would
this be just as useful to Product, HR, or Service as it is to Accounting? If
yes, it belongs in the productivity repo instead. If it only makes sense
with Accounting's own data, systems, or vocabulary baked in, it belongs here.

## Layout

```
CLAUDE.md               Instructions for Claude Code sessions in this repo
.claude-plugin/
  marketplace.json      Plugin manifest
skills/
  <skill-name>/
    SKILL.md             The recipe Claude follows. Required.
    references/          Knowledge only THIS skill needs.
agents/
  <agent-name>.md         Subagent definitions
```

The org glossary and systems landscape live in the productivity repo
(`productivity-tools/shared-knowledge/`, `$TOOLS_PRODCTVTY`), since several
skills across departments use them. Skills here can read them from there.
Put Accounting-only reference material in a `references/` folder inside the
skill that needs it.

## Source material

The fuller current-state narrative (systems, people, process detail, open
questions) lives in the Accounting team's working notebook:
`Accounting-MyNotes/Current-State Accounting Processes Report.md`. That
folder stays a personal/team working notebook in OneDrive, not synced here —
pull a curated summary into a skill's `references/` only when a skill needs to
load it automatically.

## Status

- [x] Repo scaffolded; glossary and landscape moved to the productivity repo
      (2026-10-01)
- [x] Pushed to GitHub (`origin/main`, 2026-10-01)
- [x] `CLAUDE.md` added (2026-10-05): repo purpose, which-repo rule, git and approval rules
- [ ] First accounting-specific skill (candidates from the current-state
      report: bank-transaction/remittance matching, AP invoice-exception
      triage, PO-receipt reconciliation)
- [ ] `productivity-tools/shared-knowledge/org-glossary.md` reviewed by Delphine
