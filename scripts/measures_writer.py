"""Add lockbox lines to the measures workbook (Lines sheet).

The measures workbook lives in Accounting - Internal > Bank > Electronic
Transaction Report. It is made once from the KPI tracker template (example rows
removed) and then each day's lines are added to the first blank rows.

The tool fills only the dark blue columns (payment date, source, payer, check no.,
amount, invoice) plus Reason, Cause, Status and Notes for a flagged line. Walter
fills the teal columns. The purple columns are formulas and are left alone.
A line already in the workbook (same date, check no. and invoice) is not added twice.
A file that is open in Excel is never written.
"""
import datetime as dt
import shutil
import subprocess
from pathlib import Path
from typing import List

import openpyxl

from journal_writer import JournalLine

LINES_SHEET = "X-action Lines"
DAILY_SHEET = "Daily Metrics"
FIRST_ROW, LAST_ROW = 5, 504
# Columns on the Lines sheet
A_DATE, B_SOURCE, C_PAYER, D_CHECK, E_AMOUNT, F_INVOICE, G_REASON = 1, 2, 3, 4, 5, 6, 7
J_CAUSE, N_STATUS, P_NOTES = 10, 14, 16
FILL_COLS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16]   # not the formula columns H, I, Q to T


def _is_open(path: Path) -> bool:
    if (path.parent / f"~${path.name}").exists():
        return True
    return bool(subprocess.run(["lsof", str(path)], capture_output=True, text=True).stdout.strip())


def create_from_template(template: str, output: str) -> Path:
    """Copy the template and remove the example rows. Never overwrites a file."""
    tpl, out = Path(template), Path(output)
    if out.exists():
        raise FileExistsError(f"{out} already exists; not overwritten.")
    if _is_open(tpl):
        raise RuntimeError(f"{tpl.name} is open. Close it first.")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tpl, out)
    wb = openpyxl.load_workbook(out)
    ws = wb[LINES_SHEET]
    for r in range(FIRST_ROW, LAST_ROW + 1):
        if str(ws.cell(r, P_NOTES).value or "").startswith("EXAMPLE"):
            for c in FILL_COLS:
                ws.cell(r, c).value = None
    daily = wb[DAILY_SHEET]
    for r in (6, 7):                                   # the two example days
        daily.cell(r, 1).value = None
        daily.cell(r, 6).value = None
    wb.properties.creator = "Suzan Oslin"
    wb.save(out)
    return out


def append_lines(workbook: str, lines: List[JournalLine], source: str = "Lockbox") -> int:
    """Add lines to the first blank rows. Returns how many were added."""
    path = Path(workbook)
    if _is_open(path):
        raise RuntimeError(f"{path.name} is open. Close it first.")
    wb = openpyxl.load_workbook(path)
    ws = wb[LINES_SHEET]
    seen, free = set(), []
    for r in range(FIRST_ROW, LAST_ROW + 1):
        if ws.cell(r, A_DATE).value is None:
            free.append(r)
        else:
            d = ws.cell(r, A_DATE).value
            d = d.date() if isinstance(d, dt.datetime) else d
            seen.add((d, str(ws.cell(r, D_CHECK).value), str(ws.cell(r, F_INVOICE).value)))
    added = 0
    for l in lines:
        key = (l.transaction_date, str(l.check_no), l.external_document_no)
        if key in seen:
            continue
        if not free:
            raise RuntimeError("The Lines sheet is full (row 504). Extend the sheet first.")
        r = free.pop(0)
        ws.cell(r, A_DATE).value = l.transaction_date
        ws.cell(r, B_SOURCE).value = source
        ws.cell(r, C_PAYER).value = l.payer or l.account_name
        ws.cell(r, D_CHECK).value = l.check_no
        ws.cell(r, E_AMOUNT).value = float(l.credit_amount)
        ws.cell(r, F_INVOICE).value = l.external_document_no or None
        if l.reason_code:                               # flagged line
            ws.cell(r, G_REASON).value = l.reason_code
            ws.cell(r, J_CAUSE).value = "Payment problem"
            ws.cell(r, N_STATUS).value = "Open"
        notes = "; ".join(x for x in (l.reason, l.note) if x)
        ws.cell(r, P_NOTES).value = notes or None
        ws.row_dimensions[r].height = max(20, 16 * -(-len(notes) // 40))   # room for wrapped notes
        seen.add(key)
        added += 1
    wb.save(path)
    return added
