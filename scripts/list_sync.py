"""Copy new rows from the lists in the live Transactions-and-Metrics workbook into the template.

The lists are on the "Automation Lists" sheet: the Reason list (columns A to C) and the Dept codes
table. Customer-specific codes and payer names are not listed there; the tool learns them (see
learnings.py). Anyone can add a row in the live workbook. This copies
only NEW rows into the template, so a fresh workbook starts with every rule. A row that was
edited in the live workbook, or that is only in the template, is reported and never copied.
Status travels with the row (an Unconfirmed row is copied as Unconfirmed). The live workbook
is only read. If the template is open in Excel, nothing is written and the new rows are
reported as "not copied".
"""
import copy
import datetime as dt
import subprocess
from pathlib import Path
from typing import Dict, List

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

SHEET = "Automation Lists"
# kind "range": plain cells. kind "table": an Excel table, extended when it is full.
LISTS = {
    "Reason": {"kind": "range", "key": 1, "cols": (1, 2, 3), "first": 5, "last": 30},
    "Dept code": {"kind": "table", "name": "DeptCodes", "key": 10, "cols": tuple(range(10, 16)), "last": 29},
}


def _norm(v):
    if isinstance(v, dt.datetime):
        v = v.date()
    return "" if v is None else str(v).strip()


def _bounds(ws, spec):
    if spec["kind"] == "range":
        return spec["first"], spec["last"]
    t = ws.tables[spec["name"]]
    top = int(openpyxl.utils.cell.coordinate_from_string(t.ref.split(":")[0])[1])
    bottom = int(openpyxl.utils.cell.coordinate_from_string(t.ref.split(":")[1])[1])
    return top + 1, bottom


def _rows(ws, spec) -> Dict[str, list]:
    first, last = _bounds(ws, spec)
    out = {}
    for r in range(first, last + 1):
        key = _norm(ws.cell(r, spec["key"]).value)
        if key:
            out[key] = [_norm(ws.cell(r, c).value) for c in spec["cols"]]
    return out


def _is_open(path: Path) -> bool:
    if (path.parent / f"~${path.name}").exists():
        return True
    return bool(subprocess.run(["lsof", str(path)], capture_output=True, text=True).stdout.strip())


def sync_lists(live: str, template: str) -> dict:
    """Return {"added": [...], "changed": [...], "only_in_template": [...], "not_copied": bool}."""
    lws = openpyxl.load_workbook(live, data_only=True)[SHEET]
    twb = openpyxl.load_workbook(template)
    tws = twb[SHEET]
    summary = {"added": [], "changed": [], "only_in_template": [], "not_copied": False}
    pending = []                                           # (list name, key, row values as in live)
    for name, spec in LISTS.items():
        live_rows, tpl_rows = _rows(lws, spec), _rows(tws, spec)
        for key, vals in live_rows.items():
            if key not in tpl_rows:
                summary["added"].append({"list": name, "key": key, "row": vals})
                pending.append((name, key))
            elif tpl_rows[key] != vals:
                summary["changed"].append({"list": name, "key": key, "was": tpl_rows[key], "now": vals})
        for key in tpl_rows:
            if key not in live_rows:
                summary["only_in_template"].append({"list": name, "key": key})
    if not pending:
        return summary
    tpath = Path(template)
    if _is_open(tpath):
        summary["not_copied"] = True
        return summary
    for name, key in pending:
        spec = LISTS[name]
        src = next(r for r in range(*(_bounds(lws, spec)[0], _bounds(lws, spec)[1] + 1))
                   if _norm(lws.cell(r, spec["key"]).value) == key)
        first, last = _bounds(tws, spec)
        dest = next((r for r in range(first, last + 1) if not _norm(tws.cell(r, spec["key"]).value)), None)
        if dest is None:                                   # the list is full: extend the table by one row
            if last + 1 > spec["last"]:
                summary.setdefault("full", []).append(name)
                continue
            dest = last + 1
            if spec["kind"] == "table":
                t = tws.tables[spec["name"]]
                c1, r1, c2, _ = range_boundaries(t.ref)
                t.ref = f"{get_column_letter(c1)}{r1}:{get_column_letter(c2)}{dest}"
            for c in spec["cols"]:
                tws.cell(dest, c)._style = copy.copy(tws.cell(dest - 1, c)._style)
        for c in spec["cols"]:
            tws.cell(dest, c).value = lws.cell(src, c).value
    twb.save(template)
    return summary
