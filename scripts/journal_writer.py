"""Build the Lockbox sheet of the daily deposit journal workbook.

Fills the 11 columns defined in references/deposit-journal/Lockbox-Tool_Reference.md
(section 4) from the lockbox items and the BC match results. One line per
invoice. Walter checks the workbook and uploads it; the tool never posts to BC.

The workbook is made by copying the template. An existing output file is never
overwritten, and a file that is open in Excel is never written.
"""
import datetime as dt
import shutil
import subprocess
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

import openpyxl
from openpyxl.styles import Alignment, Font

from bc_match import MatchResult
from rules import department_ok, load_rules

DESCRIPTION = "ELECTRNIC LOCKBOX CR"   # spelled the way the bank spells it
COLUMNS = ["Transaction Date", "Account Name", "Credit Amount", "Account Type", "Account No.",
           "Description", "Department", "Project Code", "Document Type", "Document No.",
           "External Document No."]
FONT = "Calibri"
SIZE = 12


@dataclass
class JournalLine:
    transaction_date: dt.date
    account_name: str
    credit_amount: Decimal
    account_type: str
    account_no: str
    department: str
    project_code: str
    external_document_no: str
    reason: str = ""          # detail; not written to the journal, goes to the measures workbook
    reason_code: str = ""     # a Reason from the measures workbook list
    note: str = ""
    payer: str = ""           # payer name as read from the check
    check_no: str = ""
    flag_type: str = ""       # for the learnings file, for example "department"
    flag_customer: str = ""
    flag_code: str = ""


def lines_for_check(value_date: str, check_amount: Decimal, payer: str,
                    stub_numbers: List[str], matches: List[MatchResult],
                    stub_amounts: Optional[List[Decimal]] = None, check_no: str = "",
                    rules: Optional[dict] = None) -> List[JournalLine]:
    """One JournalLine per match result. The lines must add up to the check amount.

    With one invoice, the line is the check amount. With several, the caller must
    pass the amount written on the stub for each invoice, or the lines are flagged.
    """
    date = dt.date.fromisoformat(value_date)
    rules = rules or load_rules("")      # no file: defaults only
    out = []
    for i, m in enumerate(matches):
        if len(matches) == 1:
            amt = check_amount
        elif stub_amounts and stub_amounts[i] is not None:
            amt = Decimal(stub_amounts[i])
        else:
            amt = Decimal("0")
            m.status, m.reason = "flagged", (m.reason + "; " if m.reason else "") + \
                "check pays several invoices and the stub amount for this one was not read"
            m.code = m.code or "Remittance wrong or unclear"
        inv = m.invoice or {}
        dept = inv.get("shortcutDimension1Code", "")
        cust = inv.get("customerNumber", "")
        if dept and not department_ok(rules, cust, dept):    # copied as is, but Walter should look
            m.reason = (m.reason + "; " if m.reason else "") + \
                f"department {dept} on the invoice (customer {cust}) is not 1000 or 2000 (copied from the invoice; please confirm)"
            m.status, m.code = "flagged", m.code or "Other (see notes)"
            flag = ("department", cust, dept)
        else:
            flag = ("", "", "")
        known = m.status == "matched" or bool(inv)
        out.append(JournalLine(
            date, inv.get("customerName", "") if known else payer, amt,
            "Customer" if inv else "", inv.get("customerNumber", ""),
            inv.get("shortcutDimension1Code", ""), inv.get("shortcutDimension2Code", ""),
            inv.get("number", ""), m.reason if m.status == "flagged" else "", 
            m.code if m.status == "flagged" else "", m.note, payer, check_no, *flag))
    if sum((l.credit_amount for l in out), Decimal("0")) != check_amount:
        for l in out:
            l.reason = (l.reason + "; " if l.reason else "") + "lines do not add up to the check amount"
            l.reason_code = l.reason_code or "Amounts do not add up"
    return out


def _is_open(path: Path) -> bool:
    if (path.parent / f"~${path.name}").exists():
        return True
    r = subprocess.run(["lsof", str(path)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def write_journal(template: str, output: str, lines: List[JournalLine]) -> Path:
    tpl, out = Path(template), Path(output)
    if out.exists():
        raise FileExistsError(f"{out} already exists; not overwritten.")
    if _is_open(tpl):
        raise RuntimeError(f"{tpl.name} is open. Close it first.")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tpl, out)
    wb = openpyxl.load_workbook(out)
    ws = wb["Lockbox"]
    if [c.value for c in ws[1]][:11] != COLUMNS:
        raise ValueError("Template headers are not the 11 expected columns.")
    base = Font(name=FONT, size=SIZE)
    for c in ws[1]:
        c.font = Font(name=FONT, size=SIZE, bold=True)
    for r, l in enumerate(lines, start=2):
        vals = [l.transaction_date, l.account_name, float(l.credit_amount), l.account_type,
                l.account_no, DESCRIPTION, l.department, l.project_code, "Payment", None,
                l.external_document_no]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = base
            cell.alignment = Alignment(vertical="top")
        ws.cell(row=r, column=1).number_format = "yyyy-mm-dd"
        ws.cell(row=r, column=3).number_format = "#,##0.00"
    ws.column_dimensions.clear()   # the template groups columns E and F; set each one alone
    for i, w in enumerate([19, 40, 16, 15, 14, 27, 14, 19, 17, 16, 26], start=1):
        cd = ws.column_dimensions[openpyxl.utils.get_column_letter(i)]
        cd.min = cd.max = i
        cd.width = w
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.freeze_panes = "A2"
    wb.properties.creator = "Suzan Oslin"
    wb.save(out)
    return out
