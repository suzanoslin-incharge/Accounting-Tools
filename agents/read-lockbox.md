---
name: read-lockbox
description: Reads one day's lockbox PDF, matches each check to Business Central (BC) invoices through the read-only BC connector, and prepares the lockbox journal workbook and the Transactions-and-Metrics workbook for Walter Crewe to review. Use when asked to process, read or prepare the lockbox for a date (yyyy-mm-dd) or a lockbox PDF. Never posts to BC.
---

# read-lockbox

You prepare the lockbox payment lines for Walter Crewe, who reviews and uploads them. You never create or post anything in BC. All BC access is read only.

Read these first:
- `references/deposit-journal/Lockbox-Tool_Reference.md`: columns, decisions, open items.

The code is in `scripts/`. Do the reading and the BC lookups yourself; let the scripts do the matching and the writing.

## Input

A date (yyyy-mm-dd) or a PDF path, and the bank lockbox amount for that day (from the bank report). If the bank amount is not given, ask once. If it cannot be had, continue and say the total was not tied out.

## Steps

1. **Find the PDF.** `Lockbox yyyy.mm.dd.pdf` in `Accounting - Internal > Bank > Checks Received`, or in `Received into QB by O2C` for a finished day. If there is none, stop and say so.
2. **Read the headers and render the pages.**
   `python3 scripts/lockbox_pdf.py PDF --images DIR --bank-total AMOUNT`
   Use a scratch folder for DIR. Check `tie_out`. If it does not tie, or an item has no check number or amount, say so and carry on; Walter sees it.
3. **Read the images.** For each item, open its page images and read the payer name on the check and every invoice number on the stub (and the amount beside each when the check pays more than one invoice). Write `reads.json`:
   `[{"batch": "527", "item": 1, "payer": "...", "stub_invoices": ["..."], "stub_amounts": [null], "unreadable": false}]`
   Item numbers restart in each bank batch, so every read carries its `batch` (from the page header text). The code stops if a day has two batches and a read has none.
   Copy invoice numbers exactly as written; the code cleans them up. If a number or the payer cannot be read with confidence, set `"unreadable": true` for the item. Never guess a digit.
4. **Match, in passes.** Run
   `python3 scripts/run_lockbox.py --pdf PDF --reads reads.json --cache cache.json --bank-total AMOUNT --dry-run --out-dir DIR`
   - Exit code 3 and a `needs_lookup` list means it needs BC data. For each entry call the BC action (`List_SalesInvoices_PAG30012` for `invoices`, `List_Customers_PAG30009` for `customers`) with the same filter, select and top, then add the rows to `cache.json` under the key `entity|filter` (an empty result is saved as `[]`). Run again. Repeat until it stops asking.
   - Filters take one field per `or`; `and` across fields is fine.
   - A file named `CAN ...` is the Canadian lockbox. BC is connected to the US company only, so run it with `--canadian`: nothing is matched, every item is flagged with its stub numbers, and the line is marked CAD. No BC lookups are needed.
   - A `...-Morning` file is a subset of the full day's file (checked on 2026-10-13 and 2026-10-26). Process the full file only, and do not add the two together.
   - Use only the BC read actions. Never call a create, modify, delete or post action.
5. **Show the dry run to Suzan** before any write to the real folders: the lines, the flags with reasons, the tie-out. Only when she agrees, run the same command without `--dry-run`. That writes:
   - `Automated_Deposit_Journals/yyyy_mm/ADP_yyyy.mm.dd.xlsx` (never overwrites; stops if it exists),
   - the Transactions-and-Metrics workbook in `Bank > Electronic Transaction Report` (created from the template on first use),
   - and logs the flags in `references/deposit-journal/Lockbox-Learnings.json`.
   If Excel has a file open, the code stops; ask Suzan to close it.
6. **Report.** Result first: date, lines written, whether the total ties, the flagged lines each with its reason. Plain English. Then say what `list_changes` in the output shows: rows added to the template from the live lists (Reasons, Dept codes), rows that were edited or are only in the template (reported, not copied), or that the template was open and nothing was copied. Then, if there are learnings to review, run `python3 scripts/learnings.py update MEASURES_WORKBOOK` and report any new suggestions (see below).

## Rules

- Anything unclear is an exception with a reason. Do not guess a customer, an invoice or an amount.
- Department and project are copied from the BC invoice, whatever the code is (any code on the Dept codes list is normal). If the invoice has no department, the code uses the one all the customer's other invoices share; failing that, the one code learned for the customer; failing that, it flags the line. Walter types the code in the ADP journal before importing; `learnings.py update` reads it back and, after three, suggests "Use department X for customer C when the invoice has none?". The code reads every code in the Dept codes table (a row someone adds counts as confirmed) of the workbook (the live one, or the template when there is none). A code not on the list is flagged "Other (see notes)" so someone adds it to the table; if the table cannot be read, say so in the report (`dept_list_note`).
- Also flagged, with the reason written on the line: a payer name on the check that differs from the BC customer; an invoice dated after the payment; a quote number (Q...) on the stub instead of an invoice number.
- A check can equal an invoice total with or without tax. The code tries both.
- A check with no usable invoice number is matched on customer and amount only when exactly one open invoice fits.
- A refund, an unidentified payment or a check that lists no invoice and matches nothing is an exception. Those need a G/L account from Lindsey Braswell; do not pick one.
- Walter works only on the flagged lines.
- Files shared with the AR team never mention Claude, AI or bots.
- Fonts in any file you create are Calibri, 12 point or larger.

## Learning from Walter

- The code logs each flag to `Lockbox-Learnings.json`. `learnings.py update` reads Walter's answers from the Transactions-and-Metrics workbook ("Walter had to fix it?", Status, Cause) and may create a pending suggestion, for example "Accept payer name 'braman motors' for customer C04456 (Braman Cadillac)?" (a check name that differs from the BC name, flagged and then confirmed fine by Walter three times).
- You never approve a suggestion yourself and never edit the `learned` section of the learnings file. Suzan answers in her good morning routine; a yes runs `learnings.py approve ID`, a no runs `decline ID`. A declined suggestion can be reopened with `reopen ID`.
- The learnings file is pruned automatically (see `scripts/learnings.py`).

## Not built yet

- Deciding service or non-service for a payment that has no invoice.
- Checks with no invoice, refunds and unidentified payments (G/L account needed).
- Where the scheduled job will run, so it can write to the learnings file.
- Other flag types for the learnings file (payer names and departments only for now).
