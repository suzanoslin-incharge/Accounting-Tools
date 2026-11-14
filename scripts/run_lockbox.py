"""Run the lockbox tool for one day: match, write the journal, write the measures, log the flags.

The BC lookups cannot be made from here (the read-only BC connector belongs to the
agent), so this script works in passes with a cache file:
  - It tries to match every check using only the lookups already in the cache.
  - Lookups it needs but does not have are printed as JSON and nothing is written
    (exit code 3). The agent fetches them from BC, adds them to the cache, and runs again.
  - When nothing is missing, it writes the journal and Transactions-and-Metrics workbook.

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
import transactions_metrics_writer as W
import list_sync as LS
import rules as R

BANK = Path.home() / "OneDrive - In Charge Service/Accounting - Internal - Documents/Bank"
TEMPLATE = Path(__file__).resolve().parent.parent / "references/deposit-journal/Template_Automated_Deposit_Journal.xlsx"
JOURNAL_DIR = BANK / "Checks Received/Automated_Deposit_Journals"
MEASURES = BANK / "Electronic Transaction Report/Transactions-and-Metrics.xlsx"
MEASURES_TEMPLATE = Path(__file__).resolve().parent.parent / "references/deposit-journal/Template_Transactions-and-Metrics.xlsx"


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


def _find_read(it, reads, items):
    """The read for one item. Item numbers restart in each bank batch, so a read carries its batch
    whenever the day has more than one batch."""
    mine = [r for r in reads if r["item"] == it.item]
    if len(mine) == 1 and mine[0].get("batch") is None:
        if sum(1 for x in items if x.item == it.item) > 1:
            raise ValueError(f"item {it.item} is in more than one batch; reads.json needs a \"batch\" on each read")
        return mine[0]
    for r in mine:
        if str(r.get("batch")) == str(it.batch):
            return r
    return None


def canadian_lines(items, reads, rules):
    """CAN lockbox: BC is connected to the US company only, so nothing is matched. Every item is
    flagged with its stub numbers for Walter, and the line is marked CAD."""
    lines = []
    for it in items:
        r = _find_read(it, reads, items) or {}
        stubs = ", ".join(r.get("stub_invoices") or [])
        m = M.MatchResult("flagged", "Canadian payment: Canadian deposits are not expected through this bank. "
                          "Known exception; not matched", code="Canadian payment",
                          note=f"Stub: {stubs}" if stubs else "")
        ls = J.lines_for_check(it.value_date, it.amount, r.get("payer", ""), [], [m],
                               check_no=it.check_no, rules=rules, item_no=str(it.item))
        for l in ls:
            l.currency, l.known_exception = "CAD", True
        lines += ls
    return lines


def build_lines(items, reads, fetch, rules, canadian=False):
    if canadian:
        return canadian_lines(items, reads, rules)
    lines = []
    for it in items:
        r = _find_read(it, reads, items)
        if r is None or r.get("unreadable"):
            m = [M.MatchResult("flagged", "check or stub could not be read; read it by hand",
                               code="Other (see notes)")]
            lines += J.lines_for_check(it.value_date, it.amount, (r or {}).get("payer", ""), [], m,
                                       check_no=it.check_no, rules=rules, item_no=str(it.item))
            continue
        stubs = r.get("stub_invoices") or []
        m = M.match_payment(fetch, r["payer"], float(it.amount), stubs, it.value_date,
                           lambda cust, payer: R.payer_ok(rules, cust, payer),
                           lambda cust: R.learned_depts(rules, cust))
        gl = not stubs and all(x.code == "No customer found" for x in m)      # nothing to match it to
        if gl:
            for x in m:
                x.reason += "; no invoice listed and the payer is not a BC customer: likely needs a G/L account from Lindsey Braswell (known exception)"
        amts = [None if a is None else Decimal(str(a)) for a in (r.get("stub_amounts") or [])] or None
        new = J.lines_for_check(it.value_date, it.amount, r["payer"], stubs, m, amts,
                                check_no=it.check_no, rules=rules, item_no=str(it.item))
        for l in new:
            l.known_exception = gl
        lines += new
    return lines


def main(argv=None):
    a = argparse.ArgumentParser()
    a.add_argument("--pdf", required=True); a.add_argument("--reads", required=True)
    a.add_argument("--cache", required=True); a.add_argument("--bank-total")
    a.add_argument("--dry-run", action="store_true"); a.add_argument("--out-dir")
    a.add_argument("--canadian", action="store_true", help="a CAN lockbox file: flag every item, match nothing")
    a = a.parse_args(argv)

    items = L.read_items(a.pdf)
    tie = L.tie_out(items, Decimal(a.bank_total) if a.bank_total else None)
    fetch = CachedFetch(a.cache)
    live = MEASURES if (MEASURES.exists() and not a.dry_run) else MEASURES_TEMPLATE
    try:
        rules, dept_note = R.load_rules(str(Lr.LEARNINGS), str(live)), None
    except Exception as e:                             # list unreadable: run without the department check, say so
        rules, dept_note = R.load_rules(str(Lr.LEARNINGS)), f"Dept codes list not read ({e}); department not checked"
    lines = build_lines(items, json.loads(Path(a.reads).read_text()), fetch, rules, a.canadian)
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
    summary = W.append_lines(str(measures), lines)
    list_changes = None
    if not a.dry_run:
        Lr.record_flags(lines, day)
        try:                                           # new rows in the live lists go into the template
            list_changes = LS.sync_lists(str(measures), str(MEASURES_TEMPLATE))
        except Exception as e:                         # never stop the run for this; say so in the summary
            list_changes = {"error": f"lists were not compared: {e}"}
    flagged = [l for l in lines if l.reason_code]
    print(json.dumps({"date": day, "items": len(items), "lines": len(lines), "tie_out": tie,
                      "journal": str(journal), "measures": str(measures), "measures_rows_added": summary["added"], "measures_summary": summary, "list_changes": list_changes, "dept_list_note": dept_note,
                      "flagged": [{"check": l.check_no, "invoice": l.external_document_no,
                                   "reason": l.reason_code, "detail": l.reason} for l in flagged]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
