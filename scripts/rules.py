"""What the lockbox tool has learned is normal, and the settings for learning.

Learned rules live in the "learned" section of Lockbox-Learnings.json (see learnings.py); there is
no separate rules file (2026-11-13). Two kinds: department codes accepted for a customer, and payer
names accepted for a customer (a check name that differs from the BC name). Standard rules (the
department code list, the reasons list) are in the Automation Lists sheet of the Transactions-and-Metrics
workbook, and the tool reads the Confirmed rows of the Dept codes table (dept_codes). The department on
the invoice is copied as is; a code that is not on the list is flagged so someone adds it (2026-11-13).

Nothing is learned without apply_proposal(), which is called only after Suzan approves. A rule can be
removed with retire_rule() or retire_payer_rule(). Every rule keeps why it exists and when it was approved.
"""
import json
from datetime import date
from pathlib import Path
from typing import Dict, List

DEFAULT = {"departments": {"default": [], "by_customer": {}},
           "payers": {"by_customer": {}},
           "min_confirmations": 3,
           "prune": {"answered_flag_days": 90, "unanswered_flag_days": 60, "decided_suggestion_days": 183}}


def _read(path: str) -> dict:
    p = Path(path) if path else None
    return json.loads(p.read_text()) if p is not None and p.is_file() else {}


def dept_codes(workbook: str) -> list:
    """The department codes in the Dept codes table (Automation Lists sheet).

    Every row with a code counts: whoever adds a row has confirmed it, and the team is told of the
    addition (2026-11-13). The "(blank)" row is not a code. Raises if the workbook or table cannot be read.
    """
    import openpyxl
    ws = openpyxl.load_workbook(workbook, data_only=True)["Automation Lists"]
    ref = ws.tables["DeptCodes"].ref
    first, last = ws[ref.split(":")[0]].row + 1, ws[ref.split(":")[1]].row
    out = []
    for r in range(first, last + 1):
        code = ws.cell(r, 10).value
        if code is not None and str(code).strip() not in ("", "(blank)"):
            out.append(str(code).strip())
    return out


def load_rules(path: str = "", workbook: str = "") -> dict:
    """The settings plus what is learned in the learnings file at path (none: settings only).

    With a workbook, the department codes are its Dept codes and an invoice
    department not on the list is flagged. Without one (empty list), nothing is flagged.
    """
    rules = json.loads(json.dumps(DEFAULT))
    if workbook:
        rules["departments"]["default"] = dept_codes(workbook)
    learned = _read(path).get("learned", {})
    rules["departments"]["by_customer"] = learned.get("departments", {})
    rules["payers"]["by_customer"] = learned.get("payers", {})
    return rules


def _save_learned(path: str, rules: dict) -> None:
    data = _read(path)
    data["learned"] = {"departments": rules["departments"]["by_customer"], "payers": rules["payers"]["by_customer"]}
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def norm_name(name: str) -> str:
    """A payer name for comparing: lower case, one space between words."""
    return " ".join(str(name or "").lower().split())


def payer_ok(rules: dict, customer_no: str, payer: str) -> bool:
    """True when this payer name has been accepted for this BC customer."""
    names = rules["payers"]["by_customer"].get(customer_no, {}).get("names", [])
    return norm_name(payer) in names


def learned_depts(rules: dict, customer_no: str) -> list:
    """Codes learned for a customer, used only when the invoice has no department."""
    return list(rules["departments"]["by_customer"].get(customer_no, {}).get("codes", []))


def department_ok(rules: dict, customer_no: str, dept: str) -> bool:
    d = rules["departments"]
    return dept in d["default"] or dept in d["by_customer"].get(customer_no, {}).get("codes", [])


def apply_proposal(path: str, proposal: dict, approved_by: str = "Suzan Oslin",
                   approved_on: str = "") -> dict:
    """Write one approved proposal into the learned section of the learnings file. Call this only after approval."""
    rules = load_rules(path)
    if proposal["type"] == "payer":
        entry = rules["payers"]["by_customer"].setdefault(proposal["customer"], {"names": []})
        if norm_name(proposal["code"]) not in entry["names"]:
            entry["names"].append(norm_name(proposal["code"]))
    else:
        assert proposal["type"] == "department"
        entry = rules["departments"]["by_customer"].setdefault(proposal["customer"], {"codes": []})
        if proposal["code"] not in entry["codes"]:
            entry["codes"].append(proposal["code"])
    entry["why"] = proposal["text"]
    entry["approved_by"], entry["approved_on"] = approved_by, approved_on or date.today().isoformat()
    _save_learned(path, rules)
    return rules


def retire_rule(path: str, customer: str, code: str) -> dict:
    """Remove one accepted code (for example, if it turns out to be wrong)."""
    rules = load_rules(path)
    entry = rules["departments"]["by_customer"].get(customer)
    if entry and code in entry["codes"]:
        entry["codes"].remove(code)
        if not entry["codes"]:
            del rules["departments"]["by_customer"][customer]
        _save_learned(path, rules)
    return rules


def retire_payer_rule(path: str, customer: str, name: str) -> dict:
    """Remove one accepted payer name (for example, if it turns out to be wrong)."""
    rules = load_rules(path)
    entry = rules["payers"]["by_customer"].get(customer)
    if entry and norm_name(name) in entry["names"]:
        entry["names"].remove(norm_name(name))
        if not entry["names"]:
            del rules["payers"]["by_customer"][customer]
        _save_learned(path, rules)
    return rules


def describe(rules: dict) -> str:
    """Plain list of the rules, for Suzan to read."""
    d = rules["departments"]
    lines = [f"Accepted for every customer: {', '.join(d['default'])}"]
    for c, e in sorted(d["by_customer"].items()):
        lines.append(f"Customer {c}: also {', '.join(e['codes'])} (approved {e.get('approved_on', '')})")
    for c, e in sorted(rules["payers"]["by_customer"].items()):
        lines.append(f"Customer {c}: payer name(s) accepted: {', '.join(e['names'])} (approved {e.get('approved_on', '')})")
    return "\n".join(lines)
