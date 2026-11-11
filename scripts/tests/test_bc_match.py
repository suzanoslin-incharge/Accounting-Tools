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
if __name__ == "__main__": unittest.main()
