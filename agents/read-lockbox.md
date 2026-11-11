---
name: read-lockbox
description: Reads one day's lockbox PDF, matches each check to Business Central (BC) invoices through the read-only BC connector, and prepares the lockbox journal workbook and the measures workbook for Walter Crewe to review. Use when asked to process, read or prepare the lockbox for a date (yyyy-mm-dd) or a lockbox PDF. Never posts to BC.
---

# read-lockbox

You prepare the lockbox payment lines for Walter Crewe, who reviews and uploads them. You never create or post anything in BC. All BC access is read only.

Read these first:
- `references/deposit-journal/Lockbox-Tool_Reference.md`: columns, decisions, open items.
- `references/deposit-journal/Lockbox-Rules.json`: rules the tool has been told are normal (read by the code; do not edit it).

The code is in `scripts/`. Do the reading and the BC lookups yourself; let the scripts do the matching and the writing.

## Input

A date (yyyy-mm-dd) or a PDF path, and the bank lockbox amount for that day (from the bank report). If the bank amount is not given, ask once. If it cannot be had, continue and say the total was not tied out.

## Steps

1. **Find the PDF.** `Lockbox yyyy.mm.dd.pdf` in `Accounting - Internal > Bank > Checks Received`, or in `Received into QB by O2C` for a finished day. If there is none, stop and say so.
2. **Read the headers and render the pages.**
   `python3 scripts/lockbox_pdf.py PDF --images DIR --bank-total AMOUNT`
   Use a scratch folder for DIR. Check `tie_out`. If it does not tie, or an item has no check number or amount, say so and carry on; Walter sees it.
3. **Read the images.** For each item, open its page images and read the payer name on the check and every invoice number on the stub (and the amount beside each when the check pays more than one invoice). Write `reads.json`:
   `[{"item": 1, "payer": "...", "stub_invoices": ["..."], "stub_amounts": [null], "unreadable": false}]`
   Copy invoice numbers exactly as written; the code cleans them up. If a number or the payer cannot be read with confidence, set `"unreadable": true` for the item. Never guess a digit.
4. **Match, in passes.** Run
   `python3 scripts/run_lockbox.py --pdf PDF --reads reads.json --cache cache.json --bank-total AMOUNT --dry-run --out-dir DIR`
   - Exit code 3 and a `needs_lookup` list means it needs BC data. For each entry call the BC action (`List_SalesInvoices_PAG30012` for `invoices`, `List_Customers_PAG30009` for `customers`) with the same filter, select and top, then add the rows to `cache.json` under the key `entity|filter` (an empty result is saved as `[]`). Run again. Repeat until it stops asking.
   - Filters take one field per `or`; `and` across fields is fine.
   - Use only the BC read actions. Never call a create, modify, delete or post action.
5. **Show the dry run to Suzan** before any write to the real folders: the lines, the flags with reasons, the tie-out. Only when she agrees, run the same command without `--dry-run`. That writes:
   - `Automated_Deposit_Journals/yyyy_mm/ADP_yyyy.mm.dd.xlsx` (never overwrites; stops if it exists),
   - the measures workbook in `Bank > Electronic Transaction Report` (created from the template on first use),
   - and logs the flags in `references/deposit-journal/Lockbox-Learnings.json`.
   If Excel has a file open, the code stops; ask Suzan to close it.
6. **Report.** Result first: date, lines written, whether the total ties, the flagged lines each with its reason. Plain English. Then, if there are learnings to review, run `python3 scripts/learnings.py update MEASURES_WORKBOOK` and report any new suggestions (see below).

## Rules

- Anything unclear is an exception with a reason. Do not guess a customer, an invoice or an amount.
- Department and project are copied from the BC invoice; the code flags a department that is not accepted for that customer.
- A check can equal an invoice total with or without tax. The code tries both.
- A check with no usable invoice number is matched on customer and amount only when exactly one open invoice fits.
- A refund, an unidentified payment or a check that lists no invoice and matches nothing is an exception. Those need a G/L account from Lindsey Braswell; do not pick one.
- Walter works only on the flagged lines.
- Files shared with the AR team never mention Claude, AI or bots.
- Fonts in any file you create are Calibri, 12 point or larger.

## Learning from Walter

- The code logs each flag to `Lockbox-Learnings.json`. `learnings.py update` reads Walter's answers from the measures workbook ("Walter had to fix it?", Status, Cause) and may create a pending suggestion, for example "Accept department 4160 for customer C01871?".
- You never approve a suggestion yourself and never edit the rules file. Suzan answers in her good morning routine; a yes runs `learnings.py approve ID`, a no runs `decline ID`. A declined suggestion can be reopened with `reopen ID`.
- The learnings file is pruned automatically (see `scripts/learnings.py`).

## Not built yet

- Deciding service or non-service for a payment that has no invoice.
- Checks with no invoice, refunds and unidentified payments (G/L account needed).
- Where the scheduled job will run, so it can write to the learnings file.
- Other flag types for the learnings file (department only for now).
