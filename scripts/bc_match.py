"""Match a payment to Business Central (BC) sales invoices.

Shared by the lockbox tool and the later deposit tool. This module has no
lockbox logic and does not talk to BC itself. The caller passes in a `fetch`
function that reads BC (the agent uses the read-only BC connector; a script
could use the BC web API). Nothing here writes to BC.

fetch(entity, filter, select, top) -> list of dicts
    entity: "invoices" (Sales Invoices) or "customers" (Customers)
    filter: one OData filter. Use only one field per "or"; "and" across fields.
"""
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

Fetch = Callable[[str, str, str, int], List[dict]]

INVOICE_FIELDS = ("number,customerNumber,customerName,postingDate,"
                  "totalAmountExcludingTax,totalAmountIncludingTax,status,"
                  "externalDocumentNumber,shortcutDimension1Code,shortcutDimension2Code")
CENT = 0.005


@dataclass
class MatchResult:
    status: str                      # "matched" or "flagged"
    reason: str = ""                 # blank when matched
    how: str = ""                    # "invoice number" or "customer and amount"
    invoice: Optional[dict] = None   # BC invoice row when one is found
    candidates: List[dict] = field(default_factory=list)
    note: str = ""                   # for the reviewer (for example, the cleaned number)
    code: str = ""                   # a Reason from the measures workbook list; blank when matched


def clean_invoice_number(raw: str) -> Optional[str]:
    """Turn what is written on a stub into a BC invoice number, or None.

    S-INV012858, SINV012544, INV#13008, N012879 -> S-INV012858 / S-INV012544 /
    S-INV013008 / S-INV012879. A number from another system (Y4MIPZXN-0003) gives
    None. The result is only a guess until BC confirms it.
    """
    if not raw:
        return None
    s = re.sub(r"[\s#]", "", raw.upper())
    m = re.fullmatch(r"(?:S-?)?INV-?0*(\d{3,6})", s)       # S-INV, SINV, INV, with or without hyphens
    if not m:
        m = re.fullmatch(r"[A-Z]0*(\d{5,6})", s)           # one stray letter left of the digits
    if not m:
        m = re.fullmatch(r"0*(\d{6})", s)                  # digits only
    return f"S-INV{int(m.group(1)):06d}" if m else None


def _amount_ok(inv: dict, amount: float) -> bool:
    """The check can equal the total with tax or before tax (seen 2026-10-01)."""
    return any(abs(float(inv.get(k) or 0) - amount) < CENT
               for k in ("totalAmountIncludingTax", "totalAmountExcludingTax"))


def lookup_invoice(fetch: Fetch, number: str) -> Optional[dict]:
    rows = fetch("invoices", f"number eq '{number}'", INVOICE_FIELDS, 2)
    return rows[0] if rows else None


def find_customer(fetch: Fetch, payer_name: str) -> List[dict]:
    """Customers whose name contains the longest word group of the payer name."""
    words = [w for w in re.findall(r"[A-Za-z0-9&']+", payer_name or "") if len(w) > 2]
    if not words:
        return []
    key = " ".join(words[:2]).lower()
    return fetch("customers", f"contains(tolower(displayName),'{key}')", "number,displayName", 10)


def match_by_customer_and_amount(fetch: Fetch, payer_name: str, amount: float) -> MatchResult:
    custs = find_customer(fetch, payer_name)
    if len(custs) != 1:
        why, code = (("payer not found in BC", "No customer found") if not custs else
                     ("more than one BC customer fits the payer name", "Payer name unclear"))
        return MatchResult("flagged", why, candidates=custs, code=code)
    num = custs[0]["number"]
    found = {}
    for fld in ("totalAmountIncludingTax", "totalAmountExcludingTax"):   # one field per filter
        for r in fetch("invoices", f"customerNumber eq '{num}' and {fld} eq {amount}", INVOICE_FIELDS, 10):
            found[r["number"]] = r
    open_ = [r for r in found.values() if r.get("status") == "Open"]
    if len(open_) == 1:
        return MatchResult("matched", how="customer and amount", invoice=open_[0],
                           note="No usable invoice number on the stub; matched on customer and amount.")
    if len(open_) > 1:
        return MatchResult("flagged", "more than one open invoice has this amount",
                           candidates=open_, code="More than one possible match")
    if found:
        return MatchResult("flagged", "the invoice with this amount is already paid",
                           candidates=list(found.values()), code="Invoice already paid (possible duplicate)")
    return MatchResult("flagged", "no invoice for this customer and amount "
                       "(the invoice may not be posted yet)", code="No invoice found")


def match_payment(fetch: Fetch, payer_name: str, amount: float,
                  stub_invoice_numbers: List[str]) -> List[MatchResult]:
    """Match one payment (a check, or a deposit line) to invoices.

    Returns one result per stub invoice number, or one result when none is listed.
    The tool never guesses: anything unclear is flagged with a reason.
    """
    if not stub_invoice_numbers:
        r = match_by_customer_and_amount(fetch, payer_name, amount)
        if r.status == "flagged":
            r.reason = "no invoice listed on the stub; " + r.reason
        return [r]
    out = []
    one = len(stub_invoice_numbers) == 1
    for raw in stub_invoice_numbers:
        cleaned = clean_invoice_number(raw)
        if cleaned is None:
            r = match_by_customer_and_amount(fetch, payer_name, amount) if one else \
                MatchResult("flagged", "", code="No invoice found")
            if r.status == "flagged":
                r.reason = f"stub number {raw} is not a BC invoice number; " + r.reason
            else:
                r.note = f"Stub number {raw} is not a BC number. " + r.note
            out.append(r)
            continue
        inv = lookup_invoice(fetch, cleaned)
        if inv is None:
            out.append(MatchResult("flagged", f"invoice {cleaned} not found in BC (stub: {raw})",
                                   code="No invoice found"))
            continue
        note = f"Stub {raw} read as {cleaned}." if cleaned != raw.strip() else ""
        if one and not _amount_ok(inv, amount):
            short = amount < float(inv["totalAmountExcludingTax"] or 0)
            out.append(MatchResult("flagged",
                       f"check amount {amount:,.2f} differs from invoice {cleaned} "
                       f"({inv['totalAmountIncludingTax']:,.2f} with tax)",
                       how="invoice number", invoice=inv, note=note,
                       code="Short-pay or partial payment" if short else "Overpayment"))
        else:
            out.append(MatchResult("matched", how="invoice number", invoice=inv, note=note))
    return out
