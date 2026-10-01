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
.claude-plugin/
  marketplace.json      Plugin manifest
skills/
  <skill-name>/
    SKILL.md             The recipe Claude follows. Required.
    references/          Knowledge only THIS skill needs.
agents/
  <agent-name>.md         Subagent definitions
shared-knowledge/
  org-glossary.md          InCharge accounting/ops terms, roles, LOB shorthand
  systems-landscape.md     Systems of record and what each owns
```

`shared-knowledge/` here is intentionally Accounting-specific (moved from
the productivity repo once we realized general-purpose skills shouldn't
hard-depend on one department's glossary). A skill in this repo can assume
these files exist; a skill in the productivity repo should not.

## Source material

The fuller current-state narrative (systems, people, process detail, open
questions) lives in the Accounting team's working notebook:
`Accounting-MyNotes/Current-State Accounting Processes Report.md`. That
folder stays a personal/team working notebook in OneDrive, not synced here —
pull a curated summary into `shared-knowledge/` only when a skill needs to
load it automatically.

## Status

- [x] Repo scaffolded, `shared-knowledge/` populated from the productivity
      repo split
- [ ] Pushed to GitHub
- [ ] First accounting-specific skill (candidates from the current-state
      report: bank-transaction/remittance matching, AP invoice-exception
      triage, PO-receipt reconciliation)
- [ ] `shared-knowledge/org-glossary.md` reviewed by Delphine
