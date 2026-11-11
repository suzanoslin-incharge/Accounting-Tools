"""Run the lockbox tool for one day: match, write the journal, write the measures, log the flags.

The BC lookups cannot be made from here (the read-only BC connector belongs to the
agent), so this script works in passes with a cache file:
  - It tries to match every check using only the lookups already in the cache.
  - Lookups it needs but does not have are printed as JSON and nothing is written
    (exit code 3). The agent fetches them from BC, adds them to the cache, and runs again.
  - When nothing is missing, it writes the journal and measures workbook.

Inputs written by the agent:
  reads.json  [{"item": 1, "payer": "...", "stub_invoices": ["S-INV012858"],
                "stub_amounts": [null], "unreadable": false}]
  cache.json  {"<entity>|<filter>": [rows as returned by BC], ...}

Usage:
  python3 run_lockbox.py --pdf PDF --reads reads.json --cache cache.json --bank-total 16362.68 \\
      [--dry-run --out-dir DIR]
Without --dry-run it writes to the real folders and logs flags to the learnings file.
"""
import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

import bc_match as M
import journal_writer as J
import learnings as Lr
import lockbox_pdf as L
import measures_writer as W
import rules as R

BANK = Path.home() / "OneDrive - In Charge Service/Accounting - Internal - Documents/Bank"
TEMPLATE = BANK / "Checks Received/Automated_Deposit_Journals/Template_Automated_Deposit_Journal.xlsx"
JOURNAL_DIR = BANK / "Checks Received/Automated_Deposit_Journals"
MEASURES = BANK / "Electronic Transaction Report/Bank-Deposits-Automation_Measures-Workbook.xlsx"
MEASURES_TEMPLATE = (Path.home() / "OneDrive - In Charge Service/Accounting - Internal - Documents/Automation/"
                     "Bank-Deposits-Automation/Bank-Deposits-Automation_KPI-Tracker-Template.xlsx")


class CachedFetch:
    def __init__(self, path):
        self.path = Path(path)
        self.cache = json.loads(self.path.read_text()) if self.path.is_file() else {}
        self.missing = {}

    def __call__(self, entity, flt, select, top):
        key = f"{entity}|{flt}"
        if key in self.cache:
            return self.cache[key]
        self.missing[key] = {"entity": entity, "filter": flt, "select": select, "top": top}
        return []


def build_lines(items, reads, fetch, rules):
    by_item = {r["item"]: r for r in reads}
    lines = []
    for it in items:
        r = by_item.get(it.item)
        if r is None or r.get("unreadable"):
            m = [M.MatchResult("flagged", "check or stub could not be read; read it by hand",
                               code="Remittance wrong or unclear")]
            lines += J.lines_for_check(it.value_date, it.amount, (r or {}).get("payer", ""), [], m,
                                       check_no=it.check_no, rules=rules)
            continue
        stubs = r.get("stub_invoices") or []
        m = M.match_payment(fetch, r["payer"], float(it.amount), stubs)
        amts = [None if a is None else Decimal(str(a)) for a in (r.get("stub_amounts") or [])] or None
        lines += J.lines_for_check(it.value_date, it.amount, r["payer"], stubs, m, amts,
                                   check_no=it.check_no, rules=rules)
    return lines


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--pdf", required=True); a.add_argument("--reads", required=True)
    a.add_argument("--cache", required=True); a.add_argument("--bank-total")
    a.add_argument("--dry-run", action="store_true"); a.add_argument("--out-dir")
    a = a.parse_args(argv)

    items = L.read_items(a.pdf)
    tie = L.tie_out(items, Decimal(a.bank_total) if a.bank_total else None)
    fetch = CachedFetch(a.cache)
    rules = R.load_rules(str(Lr.RULES))
    lines = build_lines(items, json.loads(Path(a.reads).read_text()), fetch, rules)
    if fetch.missing:
        print(json.dumps({"needs_lookup": list(fetch.missing.values())}, indent=2))
        return 3

    day = items[0].value_date
    ymd = day.replace("-", ".")
    if a.dry_run:
        out = Path(a.out_dir)
        journal, measures = out / f"ADP_{ymd}.xlsx", out / "Measures.xlsx"
    else:
        journal = JOURNAL_DIR / f"{day[:4]}_{day[5:7]}" / f"ADP_{ymd}.xlsx"
        measures = MEASURES
    J.write_journal(str(TEMPLATE), str(journal), lines)
    if not measures.exists():
        W.create_from_template(str(MEASURES_TEMPLATE), str(measures))
    added = W.append_lines(str(measures), lines)
    if not a.dry_run:
        Lr.record_flags(lines, day)
    flagged = [l for l in lines if l.reason_code]
    print(json.dumps({"date": day, "items": len(items), "lines": len(lines), "tie_out": tie,
                      "journal": str(journal), "measures": str(measures), "measures_rows_added": added,
                      "flagged": [{"check": l.check_no, "invoice": l.external_document_no,
                                   "reason": l.reason_code, "detail": l.reason} for l in flagged]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
