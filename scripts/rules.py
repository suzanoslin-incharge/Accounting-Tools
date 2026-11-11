"""The lockbox rules file and the logic that keeps it up to date.

The rules file (references/deposit-journal/Lockbox-Rules.json) holds what the tool
has been told is normal, so it stops flagging it. Today it has one kind of rule:
department codes accepted for a customer. The default codes are 1000 and 2000.

The evidence and the proposals live in a separate file, Lockbox-Learnings.json (see
learnings.py). Nothing changes this file without apply_proposal(), which is called only
after Suzan approves. A rule can be removed with retire_rule(). Every rule keeps why it
exists and when it was approved.
"""
import json
from datetime import date
from pathlib import Path
from typing import Dict, List

DEFAULT = {"version": 1,
           "note": "Rules the lockbox tool reads at the start of each run. Changed only after Suzan approves a proposal.",
           "departments": {"default": ["1000", "2000"], "by_customer": {}},
           "min_confirmations": 3,
           "prune": {"answered_flag_days": 90, "unanswered_flag_days": 60, "decided_suggestion_days": 183}}

def load_rules(path: str) -> dict:
    p = Path(path) if path else None
    if p is None or not p.is_file():
        return json.loads(json.dumps(DEFAULT))
    return json.loads(p.read_text())


def save_rules(path: str, rules: dict) -> None:
    Path(path).write_text(json.dumps(rules, indent=2, ensure_ascii=False) + "\n")


def department_ok(rules: dict, customer_no: str, dept: str) -> bool:
    d = rules["departments"]
    return dept in d["default"] or dept in d["by_customer"].get(customer_no, {}).get("codes", [])


def apply_proposal(path: str, proposal: dict, approved_by: str = "Suzan Oslin",
                   approved_on: str = "") -> dict:
    """Write one approved proposal into the rules file. Call this only after approval."""
    rules = load_rules(path)
    assert proposal["type"] == "department"
    entry = rules["departments"]["by_customer"].setdefault(proposal["customer"], {"codes": []})
    if proposal["code"] not in entry["codes"]:
        entry["codes"].append(proposal["code"])
    entry["why"] = proposal["text"]
    entry["approved_by"], entry["approved_on"] = approved_by, approved_on or date.today().isoformat()
    save_rules(path, rules)
    return rules


def retire_rule(path: str, customer: str, code: str) -> dict:
    """Remove one accepted code (for example, if it turns out to be wrong)."""
    rules = load_rules(path)
    entry = rules["departments"]["by_customer"].get(customer)
    if entry and code in entry["codes"]:
        entry["codes"].remove(code)
        if not entry["codes"]:
            del rules["departments"]["by_customer"][customer]
        save_rules(path, rules)
    return rules


def describe(rules: dict) -> str:
    """Plain list of the rules, for Suzan to read."""
    d = rules["departments"]
    lines = [f"Accepted for every customer: {', '.join(d['default'])}"]
    for c, e in sorted(d["by_customer"].items()):
        lines.append(f"Customer {c}: also {', '.join(e['codes'])} (approved {e.get('approved_on', '')})")
    return "\n".join(lines)
