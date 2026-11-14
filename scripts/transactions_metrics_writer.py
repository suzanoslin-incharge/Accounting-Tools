"""Add lockbox lines to the Transactions-and-Metrics workbook (X-action Lines sheet).

The Transactions-and-Metrics workbook lives in Accounting - Internal > Bank > Electronic
Transaction Report. It is made once from the KPI tracker template (example rows
removed) and then each day's lines are added to the first blank rows.

The tool fills only the dark blue columns (payment date, amount received, payer, check
no., invoice(s), source) plus Reason, Cause, Status and Notes for a flagged line. The
Remittance Link column is left blank for now. Walter fills the teal columns. The purple
columns are formulas and are left alone.
One row per payment (one check or bank transaction), found again on a rerun by payment
date, payer and check or transaction number; a rerun never adds a second row and never
changes the teal columns. A file that is open in Excel is never written (WorkbookOpen).
"""
import datetime as dt
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import List

import openpyxl

from journal_writer import JournalLine

LINES_SHEET = "X-action Lines"
DAILY_SHEET = "Daily Metrics"
FIRST_ROW, LAST_ROW = 4, 503
# Columns on the X-action Lines sheet (layout of the 2026-11-13 template)
A_DATE, B_AMOUNT, C_APPLIED, D_DATE_APPLIED, E_STATUS, F_REMIT_LINK, G_REASON = 1, 2, 3, 4, 5, 6, 7
H_PAYER, I_CHECK, J_INVOICE, K_SOURCE, L_NOTES, M_CAUSE = 8, 9, 10, 11, 12, 13
N_FIXED = 14                      # Walter had to fix it?
FILL_COLS = list(range(1, 16))   # A to O; not the formula columns P to U (Group, Owner, calculated)
CAD_NOTE = "CAD"
# Reasons that are expected to be flagged (orange). Everything else the tool flags is "Needs review" (yellow).
KNOWN_REASONS = {"Refund, reversal or returned payment", "Vendor item or small Ramp credit",
                 "PayFabric payment", "Canadian payment"}


class WorkbookOpen(RuntimeError):
    """The workbook is open in Excel (or another program). Nothing was written."""


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
        raise WorkbookOpen(f"{tpl.name} is open. Close it first.")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tpl, out)
    wb = openpyxl.load_workbook(out)
    ws = wb[LINES_SHEET]
    for r in range(FIRST_ROW, LAST_ROW + 1):
        if str(ws.cell(r, L_NOTES).value or "").startswith("EXAMPLE"):
            for c in FILL_COLS:
                ws.cell(r, c).value = None
    daily = wb[DAILY_SHEET]
    for r in (6, 7):                                   # the two example days
        daily.cell(r, 1).value = None
        daily.cell(r, 6).value = None
    wb.properties.creator = "Suzan Oslin"
    wb.save(out)
    return out


def _norm(text) -> str:
    return " ".join(str(text or "").lower().split())


def _as_date(v):
    return v.date() if isinstance(v, dt.datetime) else v


def _payments(lines: List[JournalLine]) -> dict:
    """Group the journal lines into payments: one per check, however many invoices it pays.

    The key is payment date, payer and check or transaction number. A blank check
    number falls back to the item number in the lockbox file.
    """
    out: dict = {}
    for l in lines:
        payer = l.payer or l.account_name
        number = str(l.check_no or "").strip() or (f"item {l.item_no}" if l.item_no else "")
        p = out.setdefault((l.transaction_date, _norm(payer), number), {
            "date": l.transaction_date, "payer": payer, "number": number, "amount": Decimal("0"),
            "invoices": [], "reason": "", "notes": [], "cad": False, "known": False})
        p["amount"] += l.credit_amount
        if l.external_document_no and l.external_document_no not in p["invoices"]:
            p["invoices"].append(l.external_document_no)
        if l.known_exception:
            p["known"] = True
        if (l.currency or "").upper() == "CAD":         # Canadian: the invoice is in Canadian dollars
            p["cad"] = True
        if l.reason_code and not p["reason"]:          # the first flagged line sets the Reason
            p["reason"] = l.reason_code
        for t in (l.reason, l.note):
            if t and t not in p["notes"]:
                p["notes"].append(t)
    return out


def append_lines(workbook: str, lines: List[JournalLine], source: str = "Lockbox") -> dict:
    """Add one row per payment, or update the row a rerun finds.

    A rerun never adds a second row and never touches Walter's columns (C to F, N, O). It
    updates only the invoice(s) and reason, and only on a row that is
    not Closed. If the amount differs on a rerun, nothing is overwritten and the
    payment is listed under "changed". A new payment with the same date and check
    number as an existing row but another payer is added and listed under
    "possible_duplicates" (Reason: Invoice already paid (possible duplicate)).
    Raises WorkbookOpen, before writing anything, if the workbook is open.
    """
    path = Path(workbook)
    if _is_open(path):
        raise WorkbookOpen(f"{path.name} is open. Close it first.")
    wb = openpyxl.load_workbook(path)
    ws = wb[LINES_SHEET]
    by_key, by_number, free = {}, {}, []
    for r in range(FIRST_ROW, LAST_ROW + 1):
        d = ws.cell(r, A_DATE).value
        if d is None:
            free.append(r)
            continue
        number = str(ws.cell(r, I_CHECK).value or "")
        by_key[(_as_date(d), _norm(ws.cell(r, H_PAYER).value), number)] = r
        by_number.setdefault((_as_date(d), number), []).append(r)
    summary = {"added": 0, "updated": 0, "unchanged": 0, "changed": [], "possible_duplicates": []}
    for key, p in _payments(lines).items():
        amount, invoices = float(p["amount"]), ", ".join(p["invoices"]) or None
        r = by_key.get(key)
        if r is not None:
            closed = str(ws.cell(r, E_STATUS).value or "").strip().lower() == "closed"
            was = ws.cell(r, B_AMOUNT).value
            if was is not None and round(float(was), 2) != round(amount, 2):
                summary["changed"].append({"date": str(p["date"]), "payer": p["payer"],
                                           "check": p["number"], "was": float(was), "now": amount})
                continue
            if not closed and (ws.cell(r, J_INVOICE).value != invoices or
                               (ws.cell(r, G_REASON).value or "") != p["reason"]):
                ws.cell(r, J_INVOICE).value = invoices
                ws.cell(r, G_REASON).value = p["reason"] or None
                summary["updated"] += 1
            else:
                summary["unchanged"] += 1
            continue
        if not free:
            raise RuntimeError("The X-action Lines sheet is full (row 504). Extend the sheet first.")
        r = free.pop(0)
        notes = ([CAD_NOTE] if p["cad"] else []) + list(p["notes"])      # CAD first, easy to filter
        reason = p["reason"]
        twins = by_number.get((p["date"], p["number"])) if p["number"] else None
        if twins:
            other = ws.cell(twins[0], H_PAYER).value
            notes.append(f"Same date and check number as row {twins[0]} (payer {other}); check for a duplicate.")
            reason = reason or "Invoice already paid (possible duplicate)"
            summary["possible_duplicates"].append({"date": str(p["date"]), "payer": p["payer"],
                                                   "check": p["number"], "row": twins[0]})
        ws.cell(r, A_DATE).value = p["date"]
        ws.cell(r, K_SOURCE).value = source
        ws.cell(r, H_PAYER).value = p["payer"]
        ws.cell(r, I_CHECK).value = p["number"] or None
        ws.cell(r, B_AMOUNT).value = amount
        ws.cell(r, J_INVOICE).value = invoices
        if reason:                                      # flagged payment
            ws.cell(r, G_REASON).value = reason
            known = p["known"] or reason in KNOWN_REASONS
            ws.cell(r, M_CAUSE).value = "Known exception" if known else "Needs review"
            ws.cell(r, E_STATUS).value = "Open"
        text = "; ".join(notes)
        ws.cell(r, L_NOTES).value = text or None
        ws.row_dimensions[r].height = max(20, 16 * -(-len(text) // 40))   # room for wrapped notes
        by_key[key] = r
        by_number.setdefault((p["date"], p["number"]), []).append(r)
        summary["added"] += 1
    wb.save(path)
    return summary
