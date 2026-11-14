"""The learnings file: what the lockbox tool has flagged, how Walter answered, and what it suggests.

Kept in the repo (references/deposit-journal/Lockbox-Learnings.json), apart from the
workbooks others use, so nobody else edits it and it does not depend on any wording in
Notes. It holds five things:
  learned    rules Suzan approved: department codes and payer names per customer (see rules.py)
  flags      every flag the tool raised, with a structured key (type, customer, code)
  responses  Walter's answer for each flag, copied from the Transactions-and-Metrics workbook when seen
  summaries  old flags rolled up into counts per case, so the file stays small (see prune)
  proposals  suggested rules: pending, approved or declined

Daily run order: record_flags() after writing the workbooks; later record_responses()
and make_proposals(). Suggestions are shown to Suzan in the good morning routine. A rule is
written only after approve(). A declined suggestion stays quiet until Walter confirms
more lines than before.

Command line:
    python3 learnings.py update WORKBOOK     read Walter's answers, make suggestions, then prune
    python3 learnings.py prune               keep the file small
    python3 learnings.py pending             list pending suggestions
    python3 learnings.py approve ID | decline ID | reopen ID
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List

import openpyxl

import rules as R

REPO = Path(__file__).resolve().parent.parent
LEARNINGS = REPO / "references" / "deposit-journal" / "Lockbox-Learnings.json"
EMPTY = {"version": 1, "learned": {"departments": {}, "payers": {}}, "flags": [], "summaries": [], "proposals": []}


def load(path=LEARNINGS) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.is_file() else json.loads(json.dumps(EMPTY))


def save(data: dict, path=LEARNINGS) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _key(f: dict):
    return (f["payment_date"], str(f["check_no"]), f["invoice"], f["type"])


def record_flags(lines, run_date: str = "", path=LEARNINGS) -> int:
    """Log the structured flags from a day's journal lines. Returns how many are new."""
    data, seen, added = load(path), set(), 0
    seen = {_key(f) for f in data["flags"]}
    for l in lines:
        if not l.flag_type:
            continue
        f = {"raised_on": run_date or date.today().isoformat(), "type": l.flag_type,
             "customer": l.flag_customer, "code": l.flag_code, "payment_date": l.transaction_date.isoformat(),
             "check_no": str(l.check_no), "invoice": l.external_document_no, "response": None}
        if l.flag_detail:
            f["detail"] = l.flag_detail                      # the BC customer name, for a payer-name flag
        if _key(f) not in seen:
            data["flags"].append(f); seen.add(_key(f)); added += 1
    save(data, path)
    return added


def record_responses(workbook: str, path=LEARNINGS, seen_on: str = "") -> int:
    """Copy Walter's answers from the Transactions-and-Metrics workbook onto flags that have none yet."""
    from transactions_metrics_writer import LINES_SHEET, FIRST_ROW, LAST_ROW, I_CHECK, J_INVOICE, E_STATUS, M_CAUSE, N_FIXED
    ws = openpyxl.load_workbook(workbook, data_only=True)[LINES_SHEET]
    rows = {}
    for r in range(FIRST_ROW, LAST_ROW + 1):
        d = ws.cell(r, 1).value
        if d is not None:
            d = d.date().isoformat() if hasattr(d, "date") else str(d)
            invs = [i.strip() for i in str(ws.cell(r, J_INVOICE).value or "").split(",") if i.strip()] or [""]
            for i in invs:                                  # one row per payment; its invoices are in one cell
                rows[(d, str(ws.cell(r, I_CHECK).value), i)] = r
    data, n = load(path), 0
    for f in data["flags"]:
        r = rows.get((f["payment_date"], f["check_no"], f["invoice"]))
        if f["response"] is not None or r is None:
            continue
        fixed, status, cause = ws.cell(r, N_FIXED).value, ws.cell(r, E_STATUS).value, ws.cell(r, M_CAUSE).value
        if fixed in ("Yes", "No") and status == "Closed":     # Walter has answered and closed the line
            f["response"] = {"fixed": fixed, "cause": cause, "seen_on": seen_on or date.today().isoformat()}
            n += 1
    save(data, path)
    return n


def _code(kind: str, code: str) -> str:
    """The code part of a case key. Payer names are compared without case or extra spaces."""
    return R.norm_name(code) if kind == "payer" else code


def _counts(data: dict) -> dict:
    """Confirmed-fine, against and date range per (type, customer, code): summaries plus live flags."""
    c = {}
    for x in data.get("summaries", []):
        if x["type"] in ("department", "payer"):
            c[(x["type"], x["customer"], _code(x["type"], x["code"]))] = {
                "fine": x["fine"], "against": x["against"], "first": x["first"], "last": x["last"], "detail": ""}
    for f in data["flags"]:
        if f["type"] not in ("department", "payer") or f["response"] is None:
            continue
        key = (f["type"], f["customer"], _code(f["type"], f["code"]))
        g = c.setdefault(key, {"fine": 0, "against": 0, "first": f["payment_date"], "last": f["payment_date"], "detail": ""})
        if f["type"] == "department" and not f["code"]:        # blank department: the code Walter typed is not read yet
            continue
        if f["type"] == "department":                          # fixed: Yes is expected here; a code typed in the journal is the evidence
            bad = f["response"]["cause"] == "Tool problem"
        else:
            bad = f["response"]["fixed"] == "Yes" or f["response"]["cause"] == "Tool problem"
        g["against" if bad else "fine"] += 1
        g["first"], g["last"] = min(g["first"], f["payment_date"]), max(g["last"], f["payment_date"])
        g["detail"] = f.get("detail") or g["detail"]
    return c


def make_proposals(path=LEARNINGS, today: str = "") -> List[dict]:
    """Add a pending suggestion for each case Walter has confirmed fine often enough.

    Two kinds: a department code for a customer, and a payer name for a customer (a check name
    that differs from the BC name). Needs min_confirmations confirmed lines and none against.
    A declined suggestion comes back only when there are more confirmed lines than when it
    was declined.
    """
    rules, data = R.load_rules(str(path)), load(path)
    new = []
    for (kind, cust, code), g in sorted(_counts(data).items()):
        n = g["fine"]
        known = R.payer_ok(rules, cust, code) if kind == "payer" else code in R.learned_depts(rules, cust)
        if known or g["against"] or n < rules["min_confirmations"]:
            continue
        old = [p for p in data["proposals"] if p["type"] == kind and p["customer"] == cust and p["code"] == code]
        if any(p["status"] == "pending" or (p["status"] == "declined" and n <= p["confirmed_count"]) for p in old):
            continue
        if kind == "payer":
            text = (f"Accept payer name '{code}' for customer {cust}" + (f" ({g['detail']})" if g["detail"] else "") +
                    f"? Flagged {n} times, Walter changed nothing ({g['first']} to {g['last']}).")
        else:
            text = (f"Use department {code} for customer {cust} when the invoice has none? Walter typed it in the "
                    f"journal {n} times ({g['first']} to {g['last']}).")
        p = {"id": f"P{max([int(x['id'][1:]) for x in data['proposals']] + [0]) + 1:03d}", "type": kind,
             "customer": cust, "code": code, "confirmed_count": n, "first_date": g["first"], "last_date": g["last"],
             "status": "pending", "created_on": today or date.today().isoformat(), "decided_on": "", "text": text}
        data["proposals"].append(p); new.append(p)
    save(data, path)
    return new


def record_journal_departments(journal_dir, path=LEARNINGS) -> dict:
    """For blank-department flags Walter has closed, read the code he typed in the ADP journal.

    Walter fixes the journal before he imports it into BC (rule, 2026-11-13); an edit after the import
    is not seen. The journal is ADP_yyyy.mm.dd.xlsx in journal_dir/yyyy_mm, found by the payment date;
    the line is found by customer and invoice. A missing journal or line, or a Department still blank,
    is skipped and counted.
    """
    data, read, skipped, cache = load(path), 0, 0, {}
    for f in data["flags"]:
        if f["type"] != "department" or f["code"] or f["response"] is None or f["response"].get("journal_read"):
            continue
        d = f["payment_date"]
        if d not in cache:
            jp = Path(journal_dir) / f"{d[:4]}_{d[5:7]}" / f"ADP_{d.replace('-', '.')}.xlsx"
            cache[d] = openpyxl.load_workbook(jp, data_only=True)["Lockbox"] if jp.is_file() else None
        ws, code = cache[d], ""
        if ws is not None:
            for row in ws.iter_rows(min_row=2, values_only=True):
                if str(row[1] or "") == f["customer"] and str(row[7] or "") == f["invoice"] and row[10]:
                    code = str(row[10]).strip(); break
        if code:
            f["code"] = code; read += 1
        else:
            skipped += 1
    save(data, path)
    return {"codes_read": read, "skipped": skipped}


def prune(path=LEARNINGS, today: str = "") -> dict:
    """Keep the file small. Safe to run every day; git keeps the earlier versions.

    Answered flags older than answered_flag_days, and unanswered flags older than
    unanswered_flag_days, are added to a summary row for their case and deleted.
    Approved suggestions older than decided_suggestion_days are deleted (the learned
    section keeps every approved rule). Pending and declined suggestions are never deleted, so a
    declined one stays quiet until it is reopened or Walter confirms more lines.
    """
    cfg = R.DEFAULT["prune"]
    t = date.fromisoformat(today) if today else date.today()
    data = load(path)
    data.setdefault("summaries", [])
    keep, rolled = [], 0
    for f in data["flags"]:
        age = (t - date.fromisoformat(f["payment_date"])).days
        limit = cfg["answered_flag_days"] if f["response"] else cfg["unanswered_flag_days"]
        if age <= limit:
            keep.append(f); continue
        s = next((x for x in data["summaries"] if (x["type"], x["customer"], _code(x["type"], x["code"])) ==
                  (f["type"], f["customer"], _code(f["type"], f["code"]))), None)
        if s is None:
            s = {"type": f["type"], "customer": f["customer"], "code": f["code"], "fine": 0, "against": 0,
                 "no_answer": 0, "first": f["payment_date"], "last": f["payment_date"]}
            data["summaries"].append(s)
        if f["response"] is None:
            s["no_answer"] += 1
        elif f["response"]["fixed"] == "Yes" or f["response"]["cause"] == "Tool problem":
            s["against"] += 1
        else:
            s["fine"] += 1
        s["first"], s["last"] = min(s["first"], f["payment_date"]), max(s["last"], f["payment_date"])
        rolled += 1
    data["flags"] = keep
    before = len(data["proposals"])
    data["proposals"] = [p for p in data["proposals"] if p["status"] != "approved" or
                         (t - date.fromisoformat(p["decided_on"])).days <= cfg["decided_suggestion_days"]]
    save(data, path)
    return {"flags_kept": len(keep), "flags_rolled_up": rolled, "suggestions_removed": before - len(data["proposals"]),
            "summaries": len(data["summaries"])}


def reopen(pid: str, path=LEARNINGS, today: str = "") -> dict:
    """Put a declined suggestion back to pending, for example when something has changed."""
    data = load(path)
    p = next(x for x in data["proposals"] if x["id"] == pid)
    if p["status"] != "declined":
        raise ValueError(f"{pid} is {p['status']}; only a declined suggestion can be reopened.")
    p["status"], p["decided_on"] = "pending", ""
    p["reopened_on"] = today or date.today().isoformat()
    save(data, path)
    return p


def pending(path=LEARNINGS) -> List[dict]:
    return [p for p in load(path)["proposals"] if p["status"] == "pending"]


def decide(pid: str, approve: bool, path=LEARNINGS, today: str = "") -> dict:
    """Record Suzan's answer. Approving writes the rule; declining only records the answer."""
    data = load(path)
    p = next(x for x in data["proposals"] if x["id"] == pid)
    if p["status"] != "pending":
        raise ValueError(f"{pid} is already {p['status']}.")
    p["status"], p["decided_on"] = ("approved" if approve else "declined"), today or date.today().isoformat()
    save(data, path)
    if approve:                                       # re-reads the file, so save the status first
        R.apply_proposal(str(path), p, approved_on=p["decided_on"])
    return p


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pending"
    if cmd == "update":
        from run_lockbox import JOURNAL_DIR
        n = record_responses(sys.argv[2])
        print(n, "answers read;", record_journal_departments(JOURNAL_DIR), len(make_proposals()), "new suggestions;", prune())
    elif cmd == "prune":
        print(prune())
    elif cmd == "pending":
        for p in pending(): print(p["id"], p["text"])
    elif cmd == "reopen":
        print(reopen(sys.argv[2])["status"])
    elif cmd in ("approve", "decline"):
        print(decide(sys.argv[2], cmd == "approve")["status"])
