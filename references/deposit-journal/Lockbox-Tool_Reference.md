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
| Template | `Automated_Deposit_Journals/Template_Automated_Deposit_Journal.xlsx`. One sheet, named `Lockbox` |
| Daily workbook (output) | `Automated_Deposit_Journals/yyyy_mm/ADP_yyyy.mm.dd.xlsx`. Example: `2026_10/ADP_2026.10.01.xlsx` |

- **Testing for now:** read the lockbox files already in `Received into QB by O2C`. Start with the first business day of October 2026, which is 2026-10-01.
- **Code:** the tool's code lives in the accounting-tools repo (`/Users/suzanoslin/accounting-tools`). Layout: this reference file is in `references/deposit-journal/` (shared by the three tools). The agent will be `agents/read-lockbox.md` and its code will go in `scripts/` when they are built.
- A second copy of the template, named `...-Suzan Oslin's Macbook Pro.xlsx`, sits beside it. It looks like a sync duplicate and is not used.

## 3. What the lockbox PDF contains

Checked on `Lockbox 2026.10.01.pdf` (13 pages, 6 checks, batch 512).

- **One check is one item.** Its first page is the image of the check. The next page or pages are the payer's remittance stub, which lists what the check pays (for example an invoice number). One item can have more than one stub page.
- **A text line at the top of every page** gives: value date, program, batch number, item number, and on the check page the payment serial number (the check number) and the amount. This text can be read directly. It needs no image reading.
- **The payer name and invoice numbers** are only in the images (the check and the stub).
- **Invoice numbers are written in different ways** on the stubs: with or without the hyphen, with or without the "S-INV" start (for example `S-INV012858`, `SINV012544`, `INV#13008`). Some come from another system and are not BC numbers. The tool must clean the number up and then confirm it in BC.
- **Typed marks** such as "payment applied" (and one with a customer number) were added to finished files. They are not part of the payment.
- **Tie-out:** the six amounts on 2026-10-01 add to 16,362.68, which equals the lockbox credit on the bank report for that day.

## 4. The 11 columns of the Lockbox sheet

| Column | What goes in it | Status |
| --- | --- | --- |
| Transaction Date | The date the transaction hit the bank. For a lockbox, the value date in the page header | Decided |
| Account Name | The customer name as it appears in BC. It often differs from the name on the check | Decided. Needs the BC customer lookup |
| Credit Amount | The amount applied to that invoice. The check amount is split across its invoices, and the lines add up to the check amount | Decided for now (option A, 2026-11-10) |
| Account Type | `Customer`, or `G/L Account` for a line with no customer. BC also offers Vendor, Bank Account, Fixed Asset, IC Partner, Employee and Allocation Account | Decided |
| Account No. | The customer number in BC (for a G/L line, the G/L number) | Decided. Needs the BC lookup |
| Description | The fixed text `ELECTRNIC LOCKBOX CR`, spelled the way the bank spells it | Decided for now (2026-11-10). Later we may copy it from the bank report row |
| Department | Generally 1000 for non-service payments and 2000 for service payments. Shree sets the codes. Exception: Stripe is 5100 | Rule known. How the tool tells service from non-service is open |
| Project Code | The project number from the invoice in BC. When there is a work order, add it after a slash: `Project# / WO#` | Decided for now (2026-11-10). The knowledge base had the work order in External Document No. instead |
| Document Type | `Payment` | Decided |
| Document No. | The bank deposit number. Left blank for Walter to fill in | Decided |
| External Document No. | The invoice number | Decided |

One line per invoice. A check that pays three invoices becomes three lines.

## 5. Rules carried over from the project requirements

- The tool looks each invoice up in BC through the read-only connector.
- If the stub lists invoice numbers, it looks up each one. If it lists none, it may search the customer's open invoices for a set that adds up to the payment. Only one clear match counts as matched.
- More than one possible match, a partial payment, or no match is flagged with the reason. The tool never guesses.
- The lockbox total must equal the bank amount.
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
- Whether the Document Date and Posting Date on the BC deposit header need columns in the template.

## 9. Earlier work that may be reused

In `~/Documents/Accounting/Order-to-Cash/`:

- `lockbox_to_excel.py` reads the page header text and groups the pages of one item, then reads payer and invoice numbers with text recognition (OCR). The header reading is a good starting point.
- `clean_transactions.py` builds the daily sheet from the bank report. It belongs to the bank report piece.

## 10. Sources

- PRD: Bank Deposits Automation (2026-11-05), the lockbox and remittance sections.
- Knowledge base: Business Central Cash Application and Bank Deposit Process.
- Suzan Oslin, 2026-11-10: the folders, the column definitions and the decisions above.
