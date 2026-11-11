import datetime as dt, os, sys, tempfile, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl
from bc_match import MatchResult
import journal_writer as J

TPL = os.path.expanduser("~/OneDrive - In Charge Service/Accounting - Internal - Documents/Bank/"
      "Checks Received/Automated_Deposit_Journals/Template_Automated_Deposit_Journal.xlsx")
INV = {"number":"S-INV012858","customerNumber":"C04343","customerName":"LA QUINTA CHEVROLET",
       "shortcutDimension1Code":"2000","shortcutDimension2Code":"071273626"}

class T(unittest.TestCase):
    def test_line(self):
        ls = J.lines_for_check("2026-10-01", Decimal("845.00"), "La Quinta", ["S-INV012858"],
                               [MatchResult("matched", how="invoice number", invoice=INV)])
        l = ls[0]
        self.assertEqual((l.account_no, l.department, l.project_code, l.credit_amount),
                         ("C04343", "2000", "071273626", Decimal("845.00")))
    def test_several_without_amounts_flagged(self):
        ms = [MatchResult("matched", invoice=INV), MatchResult("matched", invoice=INV)]
        ls = J.lines_for_check("2026-10-01", Decimal("100"), "X", ["a", "b"], ms)
        self.assertTrue(all(l.reason for l in ls))
    def test_flagged_keeps_payer(self):
        ls = J.lines_for_check("2026-10-01", Decimal("5"), "Some Payer", ["Z"],
                               [MatchResult("flagged", "not found")])
        self.assertEqual((ls[0].account_name, ls[0].reason), ("Some Payer", "not found"))
    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_write_and_no_overwrite(self):
        ls = J.lines_for_check("2026-10-01", Decimal("845.00"), "La Quinta", ["S-INV012858"],
                               [MatchResult("matched", invoice=INV)])
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "2026_10", "ADP_2026.10.01.xlsx")
            J.write_journal(TPL, out, ls)
            ws = openpyxl.load_workbook(out)["Lockbox"]
            self.assertEqual([c.value for c in ws[2]][1:9],
                ["LA QUINTA CHEVROLET", 845.0, "Customer", "C04343", "ELECTRNIC LOCKBOX CR",
                 "2000", "071273626", "Payment"])
            self.assertEqual(ws["K2"].value, "S-INV012858")
            self.assertGreaterEqual(ws["B2"].font.size, 12)
            with self.assertRaises(FileExistsError): J.write_journal(TPL, out, ls)
if __name__ == "__main__": unittest.main()
