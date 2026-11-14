# Lockbox tool: reference

Prepared by Suzan Oslin. Last updated 2026-11-10. Status: nothing is built yet. This is one living file for the whole project: edit it as decisions change. Working notes for a single day or test go in their own temporary file, not here. Decisions below can change; each one says so where it is a "for now" choice.

## 1. What this is

An accounts receivable (AR) tool to help Walter Crewe post customer payments in Business Central (BC). It is built in three tools, one job each:

1. **Lockbox tool.** Reads the daily lockbox PDF and prepares the lockbox payment lines. This is the first one.
2. **Deposit tool.** Prepares the deposit. It relies on the remittance tool.
3. **Remittance tool.** Finds the remittance (what each payment covers) for each payment.

Suggested build order, because the deposit tool needs the remittance tool: 1, then 3, then 2. Not decided.

The tool never creates or posts a deposit in BC. Walter checks the workbook and uploads it.

## 2. Files and folders

All are in the Accounting - Internal site, under Bank > Checks Received.

| What | Where and name |
| --- | --- |
| Daily lockbox file (input) | `Checks Received`, named `Lockbox yyyy.mm.dd` (PDF). Example: `Lockbox 2026.10.01.pdf` |
| Lockbox file after Walter is done | Moved to `Received into QB by O2C`, same name |
| Template | `references/deposit-journal/Template_Automated_Deposit_Journal.xlsx` in this repo (kept out of SharePoint). One sheet, named `Lockbox` |
| Daily workbook (output) | `Automated_Deposit_Journals/yyyy_mm/ADP_yyyy.mm.dd.xlsx`. Example: `2026_10/ADP_2026.10.01.xlsx` |

- **Testing for now:** read the lockbox files already in `Received into QB by O2C`. Start with the first business day of October 2026, which is 2026-10-01.
- **Code:** the tool's code lives in the accounting-tools repo (`/Users/suzanoslin/accounting-tools`). Layout: this reference file is in `references/deposit-journal/` (shared by the three tools). The agent will be `agents/read-lockbox.md` and its code will go in `scripts/` when they are built.
- A second copy of the template, named `...-Suzan Oslin's Macbook Pro.xlsx`, sits beside it. It looks like a sync duplicate and is not used.

## 3. What the lockbox PDF contains

Checked on `Lockbox 2026.10.01.pdf` (13 pages, 6 checks, batch 512).

- **One check is one item.** Its first page is the image of the check. The next page or pages are the payer's remittance stub (for a lockbox, the check and stub image is the remittance), which lists what the check pays (for example an invoice number). One item can have more than one stub page.
- **A text line at the top of every page** gives: value date, program, batch number, item number, and on the check page the payment serial number (the check number) and the amount. This text can be read directly. It needs no image reading.
- **The payer name and invoice numbers** are only in the images (the check and the stub).
- **Invoice numbers are written in different ways** on the stubs: with or without the hyphen, with or without the "S-INV" start (for example `S-INV012858`, `SINV012544`, `INV#13008`). Some come from another system and are not BC numbers. The tool must clean the number up and then confirm it in BC.
- **Typed marks** such as "payment applied" (and one with a customer number) were added to finished files. They are not part of the payment.
- **Tie-out:** the six amounts on 2026-10-01 add to 16,362.68, which equals the lockbox credit on the bank report for that day.

## 4. The 11 columns of the Lockbox sheet

Columns A to I follow the order of the bank deposit lines in BC (screenshot of deposit BD04340, 2026-11-13), using only the line columns the tool fills or Walter needs. BC also shows Bank Payment Type, Source No., Currency Factor, Source Currency Code, Source Currency Amount and Currency Code. The sheet leaves them out. Columns J and K are for review and are not BC line columns.

| Column | What goes in it | Status |
| --- | --- | --- |
| Account Type | `Customer`, or `G/L Account` for a line with no customer. BC also offers Vendor, Bank Account, Fixed Asset, IC Partner, Employee and Allocation Account | Decided |
| Account No. | The customer number in BC (for a G/L line, the G/L number) | Decided. Needs the BC lookup |
| Description | Left blank. BC fills it in from the customer number (for example "Shopify customer" for SC001) | Corrected 2026-11-13. Earlier decision was the fixed text `ELECTRNIC LOCKBOX CR` |
| Project Code | The project number from the invoice in BC. When there is a work order, add it after a slash: `Project# / WO#` | Decided for now (2026-11-10). The knowledge base had the work order in External Document No. instead |
| Document Date | The date the transaction hit the bank. For a lockbox, the value date in the page header. On the BC line this column is called Document Date (it showed 11/3/2026, the deposit's posting date) | Decided. Was named Transaction Date |
| Document Type | `Payment` | Decided |
| Document No. | The bank deposit number. Left blank for Walter to fill in | Decided |
| External Document No. | The invoice number | Decided |
| Credit Amount | The amount applied to that invoice. The check amount is split across its invoices, and the lines add up to the check amount | Decided for now (option A, 2026-11-10) |
| Account Name | The customer name as it appears in BC. It often differs from the name on the check. For review only: BC has no such line column | Decided. Needs the BC customer lookup |
| Department | Generally 1000 for non-service payments and 2000 for service payments. Shree sets the codes. Exception: Stripe is 5100. For review: in BC, Dept Code is on the deposit header (the example shows 1000) | Decided 2026-11-13: copy the department from the BC invoice whatever the code is (4160, 5100, 2400 and others are normal). If the invoice has none, use the one all the customer's other invoices share, and flag the line when they disagree. The "not 1000 or 2000" flag is off |

One line per invoice. A check that pays three invoices becomes three lines.

## 5. Rules carried over from the project requirements

- The tool looks each invoice up in BC through the read-only connector.
- If the stub lists invoice numbers, it looks up each one. If it lists none, it may search the customer's open invoices for a set that adds up to the payment. Only one clear match counts as matched.
- More than one possible match, a partial payment, or no match is flagged with the reason. The tool never guesses.
- The lockbox total must equal the bank amount.
- For lockbox, the check and stub image is the remittance (2026-11-13). The tool never looks for a separate remittance, and does not use the reasons "No remittance found" or "Remittance wrong or unclear" for a lockbox line. An item the tool cannot read is flagged "Other (see notes)", and a check that pays several invoices with a stub amount that was not read is flagged "Amounts do not add up". The two remittance reasons stay on the list for bank report items. The Remittance Link column stays blank for lockbox lines.
- Payer names are learned (2026-11-13): a payer-name flag goes in `Lockbox-Learnings.json`. After Walter closes the line three times with "fixed: No" and no tool problem, a suggestion appears for Suzan ("Accept payer name ... for customer ...?"). A yes adds the name to the `learned` section of `Lockbox-Learnings.json`, and the tool stops flagging that pair. There is no separate rules file (2026-11-13): standard rules (Reasons, Dept codes) are lists in the workbook; what the tool learns per customer (department codes, payer names) is in the learnings file. The workbook lists do not hold customer pairs or payer names.
- Department codes (2026-11-13): the tool reads every code in the Dept codes table in the workbook (a row someone adds counts as confirmed; the team is told). A department on the invoice that is not on the list is flagged (Other (see notes)); the department is still copied. Add the new code to the table to stop the flag. A blank invoice department is different: use the code all the customer's other invoices share, else the one learned code for the customer, else flag it. Walter types the code in the ADP journal; `learnings.py update` reads it back, and after three confirmations Suzan is asked once. A customer with several learned codes keeps being flagged.
- Rule (2026-11-13): Walter fixes any issue in the ADP journal file before he imports it into Business Central. An edit made after import is not seen by the tool, and that is accepted; the tool cannot be flawless.
- Open for user acceptance testing (UAT), 2026-11-13: can invoice lines predict a blank department? Tested on 107 October invoices coded 1000 or 2000: a field-service line (SL-*, TRAVEL, SVS-LABOR) meant 2000 every time (77 of 77), but 16 of 93 coded-2000 invoices have none, and the invoice prefix (S, PS) does not predict the code. Not built. Dig deeper with the team during UAT.
- Flagged with the reason written on the line (2026-11-13): the payer on the check differs from the BC customer; the invoice is dated after the payment; the stub shows a quote number (Q...) and not an invoice number; the invoice has no department the tool can work out. A bare stub number such as 13078 is tried as S-INV013078, and a prefixed one such as PS-INV000783 is looked up as written.
- A `CAN` lockbox file is not matched yet, because BC is connected to the US company only. Every item is flagged with its stub numbers and marked CAD (the `--canadian` option) until Canada company access is set up.
- Item numbers restart in each bank batch, so every read in `reads.json` carries its `batch`.
- Walter reviews the sheet and works only on the flagged lines.

## 6. Test plan (first test)

1. Read the header text of every page of `Lockbox 2026.10.01.pdf` and list the six items with check number and amount.
2. Add the amounts and compare with the bank amount (16,362.68).
3. Read the stubs and list the invoice numbers for each check.
4. Compare the result with what Walter posted for that day.

Each step is agreed with Suzan before it is built.

## 7. BC access the tools need

The tools read BC through the MCP server configuration "MCP BC" (Model Context Protocol). The tools can only use APIs listed in that configuration, so each environment needs them added, Allow Read only. The tools never write to BC.

| Tool | APIs (minimum) |
| --- | --- |
| Lockbox | Customers, Sales Invoices, Sales Invoice Lines, Sales Orders, Aged Accounts Receivable, Projects |
| Remittance | Same as lockbox, plus Contacts, Customer Contacts, Sales Credit Memos, Sales Invoice attachments |
| Deposit | Bank Accounts, Accounts (G/L chart), Journals, Journal Lines, Customer Payment Journals, Customer Payments, General Ledger Entries |
| All three | Dimensions, Dimension Set Lines, Default Dimensions, Company Information |

- Customer Ledger Entries and Bank Account Ledger Entries are not standard APIs. Posted payments show in General Ledger Entries; unposted journal lines show in Customer Payments. Customer ledger entries would need a custom API page built by a developer.
- The configuration name in the connector settings must match the name in BC exactly. Both environments use "MCP BC".

## 8. Open items

- How the tool decides service (2000) or non-service (1000) for each line.
- How the tool finds the BC customer, invoice and project for each line.
- What to do with a check that lists no invoice, a refund, or an unidentified payment (these need a G/L account from Lindsey Braswell, per the cash application article).
- Posting Date, Document Date and Dept Code are on the BC deposit header, not the lines. The template has no columns for the header. Whether the line Department should still be shown (and how it reaches the header when one deposit mixes 1000 and 2000) is open.

## 9. Earlier work that may be reused

In `~/Documents/Accounting/Order-to-Cash/`:

- `lockbox_to_excel.py` reads the page header text and groups the pages of one item, then reads payer and invoice numbers with text recognition (OCR). The header reading is a good starting point.
- `clean_transactions.py` builds the daily sheet from the bank report. It belongs to the bank report piece.

## 10. Sources

- PRD: Bank Deposits Automation (2026-11-05), the lockbox and remittance sections.
- Knowledge base: Business Central Cash Application and Bank Deposit Process.
- Suzan Oslin, 2026-11-10: the folders, the column definitions and the decisions above.
