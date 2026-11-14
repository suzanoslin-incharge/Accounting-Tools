"""Tests for bc_match, using the BC rows read on 2026-11-11 for the 2026-10-01 lockbox."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bc_match import clean_invoice_number as c, match_payment

def inv(n, cust, name, ex, inc, status="Paid"):
    return {"number": n, "customerNumber": cust, "customerName": name, "status": status,
            "totalAmountExcludingTax": ex, "totalAmountIncludingTax": inc,
            "shortcutDimension1Code": "2000", "shortcutDimension2Code": "P"}

INVOICES = [inv("S-INV012858","C04343","LA QUINTA CHEVROLET",845,845),
            inv("S-INV013008","C04431","New Century BMW",4008.16,4008.16),
            inv("S-INV013447","C04225","Southwest Vermont Supervisory Union",4896,4973.76,"Open"),
            inv("S-INV013862","C04225","Southwest Vermont Supervisory Union",640,640,"Open")]
CUSTOMERS = [{"number":"C04225","displayName":"Southwest Vermont Supervisory Union"}]

def fetch(entity, flt, select, top):
    if entity == "customers":
        return [x for x in CUSTOMERS if "southwest vermont" in flt]
    if flt.startswith("number eq"):
        n = flt.split("'")[1]; return [i for i in INVOICES if i["number"] == n]
    if "customerNumber eq 'C04225'" in flt:
        fld = "totalAmountIncludingTax" if "Including" in flt else "totalAmountExcludingTax"
        v = float(flt.split(" eq ")[-1]); return [i for i in INVOICES if i["customerNumber"]=="C04225" and i[fld]==v]
    return []

class T(unittest.TestCase):
    def test_clean(self):
        for raw, want in [("S-INV012858","S-INV012858"),("SINV012544","S-INV012544"),
                          ("INV#13008","S-INV013008"),("N012879","S-INV012879"),
                          (" s-inv 012880 ","S-INV012880"),("Y4MIPZXN-0003",None),("",None)]:
            self.assertEqual(c(raw), want, raw)
    def test_number_match(self):
        r = match_payment(fetch, "La Quinta", 845.00, ["S-INV012858"])[0]
        self.assertEqual(r.status, "matched")
    def test_cleaned_number(self):
        r = match_payment(fetch, "New Century BMW", 4008.16, ["INV#13008"])[0]
        self.assertEqual((r.status, r.invoice["number"]), ("matched", "S-INV013008"))
    def test_not_found(self):
        r = match_payment(fetch, "X", 10, ["S-INV999999"])[0]
        self.assertEqual(r.status, "flagged")
    def test_amount_differs(self):
        r = match_payment(fetch, "La Quinta", 800, ["S-INV012858"])[0]
        self.assertEqual(r.status, "flagged"); self.assertIn("differs", r.reason)
    def test_item5_before_tax(self):
        r = match_payment(fetch, "Southwest Vermont Supervisory Union", 4896.00, ["Y4MIPZXN-0003"])[0]
        self.assertEqual((r.status, r.invoice["number"]), ("matched", "S-INV013447"))
    def test_no_invoice_listed(self):
        r = match_payment(fetch, "Southwest Vermont Supervisory Union", 123.45, [])[0]
        self.assertEqual(r.status, "flagged"); self.assertIn("no invoice listed", r.reason)

class Review(unittest.TestCase):
    """Flags added on 2026-11-13: payer name, invoice dated after the payment, quote numbers, no department."""
    def mk(self, number, name, cust="C1", date="2026-09-01", dept="2000", amt=100, status="Open"):
        return {"number": number, "customerNumber": cust, "customerName": name, "status": status,
                "totalAmountExcludingTax": amt, "totalAmountIncludingTax": amt, "postingDate": date,
                "shortcutDimension1Code": dept, "shortcutDimension2Code": "P"}
    def fetcher(self, rows):
        def f(entity, flt, select, top):
            if entity == "invoices" and flt.startswith("number eq"):
                n = flt.split("'")[1]; return [r for r in rows if r["number"] == n]
            if entity == "invoices" and flt.startswith("customerNumber eq") and " and " not in flt:
                c = flt.split("'")[1]; return [r for r in rows if r["customerNumber"] == c]
            return []
        return f
    def test_clean_new_forms(self):
        for raw, want in [("13078", "S-INV013078"), ("PS-INV000783", "PS-INV000783"),
                          ("Q262631", None), ("Q-24878-1", None), ("INV007789A", None)]:
            self.assertEqual(c(raw), want, raw)
    def test_bare_number_is_tried(self):
        f = self.fetcher([self.mk("S-INV013078", "Braman Motors")])
        r = match_payment(f, "Braman Motors", 100, ["13078"], "2026-10-16")[0]
        self.assertEqual((r.status, r.invoice["number"]), ("matched", "S-INV013078"))
    def test_prefixed_number_is_looked_up_as_written(self):
        f = self.fetcher([self.mk("PS-INV000783", "Acme Co")])
        r = match_payment(f, "Acme", 100, ["PS-INV000783"], "2026-10-02")[0]
        self.assertEqual((r.status, r.invoice["number"]), ("matched", "PS-INV000783"))
    def test_quote_number_is_flagged_not_turned_into_an_invoice(self):
        base = self.fetcher([])
        f = lambda e, flt, sel, top: [{"number": "C1", "displayName": "Acme"}] if e == "customers" else base(e, flt, sel, top)
        r = match_payment(f, "Acme", 100, ["Q262631"], "2026-10-29")[0]
        self.assertEqual(r.status, "flagged"); self.assertIn("quote number", r.reason)
        self.assertEqual(r.code, "Payment before Closed Won or invoice not yet created")
    def test_other_payer_name_is_flagged(self):
        f = self.fetcher([self.mk("S-INV000001", "Martin Chevrolet")])
        r = match_payment(f, "Joe Giacomin Chevrolet", 100, ["S-INV000001"], "2026-10-19")[0]
        self.assertEqual((r.status, r.code), ("flagged", "Payer name unclear")); self.assertIn("differs", r.reason)
    def test_same_name_is_not_flagged(self):
        f = self.fetcher([self.mk("S-INV000001", "LA QUINTA CHEVROLET INC")])
        self.assertEqual(match_payment(f, "La Quinta Chevrolet", 100, ["S-INV000001"], "2026-10-19")[0].status, "matched")
    def test_invoice_dated_after_payment_is_flagged(self):
        f = self.fetcher([self.mk("S-INV000001", "Acme", date="2026-10-16")])
        r = match_payment(f, "Acme", 100, ["S-INV000001"], "2026-10-01")[0]
        self.assertEqual((r.status, r.invoice["number"]), ("flagged", "S-INV000001")); self.assertIn("after the payment", r.reason)
    def test_blank_department_taken_from_customers_other_invoices(self):
        f = self.fetcher([self.mk("S-INV000001", "Acme", dept=""), self.mk("S-INV000002", "Acme", dept="4160"),
                          self.mk("S-INV000003", "Acme", dept="4160")])
        r = match_payment(f, "Acme", 100, ["S-INV000001"], "2026-10-08")[0]
        self.assertEqual((r.status, r.invoice["shortcutDimension1Code"]), ("matched", "4160")); self.assertIn("no department", r.note)
    def test_blank_department_flagged_when_other_invoices_disagree(self):
        f = self.fetcher([self.mk("S-INV000001", "Acme", dept=""), self.mk("S-INV000002", "Acme", dept="1000"),
                          self.mk("S-INV000003", "Acme", dept="2000")])
        r = match_payment(f, "Acme", 100, ["S-INV000001"], "2026-10-08")[0]
        self.assertEqual(r.status, "flagged"); self.assertIn("no department", r.reason)
if __name__ == "__main__": unittest.main()
