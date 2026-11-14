# accounting-tools

Suzan Oslin's repo for Claude skills, agents and reference material that only make sense with InCharge's accounting and finance domain baked in: its systems (Business Central, Salesforce, Ramp, PayFabric, bank feeds), its processes (order-to-cash, procure-to-pay, record-to-report) and its vocabulary. Personal preferences (fonts, writing style, approvals) are in `~/.claude/CLAUDE.md`. The same rules apply here.

## Which repo does a tool belong in?

- Would it be just as useful to Product, HR or Service? Put it in `productivity-tools`.
- Does it only work with accounting data, systems or vocabulary? Put it here.
- The department directory and systems landscape live in `productivity-tools/shared-knowledge/` (`$TOOLS_PRODCTVTY`). Read them from there. Do not copy them into this repo.
- Reference material that only one skill needs goes in that skill's `references/` folder.

## Layout

- `.claude-plugin/marketplace.json`: plugin manifest.
- `skills/<skill-name>/SKILL.md` (required) and optional `references/`.
- `agents/<agent-name>.md`: subagent definitions.

The repo is a scaffold so far: `skills/` and `agents/` are empty. The first skills are not built yet. Candidates from the current-state report are bank-transaction and remittance matching, AP invoice-exception triage, and PO-receipt reconciliation. Build one only when Suzan asks.

## The knowledge base is not in this repo

The knowledge base and trackers live in OneDrive: `$KB_ROOT` (the `_KB` folder) and `$ACCT_MYNOTES` (Accounting-MyNotes). Never copy knowledge base content here. Pull a short, curated summary into a skill's `references/` only when that skill must load it automatically. See `$ACCT_MYNOTES/CLAUDE.md` for the knowledge base rules.

## Git

- Commit and push straight to `main` when Suzan asks. Do not create a branch unless she asks. If a change looks risky, say so and let her decide.
- Commit only when asked, with a short message that says what changed and why. Standing exception (2026-11-13): the good night routine commits and pushes this repo whenever there are changes from the day's work, without asking.

## Rules for anything you create

- Never use any font smaller than 12 point in files you generate.
- A skill never writes to the knowledge base or trackers until Suzan approves the proposal.
- Names and roles come from the department directory; keep first names as written until Suzan confirms the full name.
- Error handling (2026-11-11): when Suzan defines a tool, PRD section or flow and does not say what happens when something fails (a missing file, a locked workbook, a job that never runs, bad data), make the suggestion yourself. Keep it big picture: one or two likely failures, who is told, how it is recovered. Do not list every edge case. Prefer a signal that works even if the tool itself is dead (for example the flow checks that a run happened, rather than the tool reporting that it failed). Alerts go through Teams. Show the suggestion as part of the proposal with a default she can accept with "yes".
