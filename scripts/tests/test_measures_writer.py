import datetime as dt, os, sys, tempfile, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl
import measures_writer as W
from journal_writer import JournalLine

TPL = os.path.expanduser("~/OneDrive - In Charge Service/Accounting - Internal - Documents/Automation/"
      "Bank-Deposits-Automation/Bank-Deposits-Automation_KPI-Tracker-Template.xlsx")
def line(inv, code=""):
    return JournalLine(dt.date(2026,10,1), "BC Name", Decimal("845"), "Customer", "C1", "2000", "P",
                       inv, "detail" if code else "", code, "note", "Payer", "112938")

@unittest.skipUnless(os.path.exists(TPL), "template not available")
class T(unittest.TestCase):
    def test_flow(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "m.xlsx")
            W.create_from_template(TPL, out)
            ws = openpyxl.load_workbook(out)[W.LINES_SHEET]
            self.assertIsNone(ws["A5"].value); self.assertTrue(str(ws["H5"].value).startswith("=IF"))
            self.assertEqual(W.append_lines(out, [line("S-INV1"), line("S-INV2", "No invoice found")]), 2)
            self.assertEqual(W.append_lines(out, [line("S-INV1")]), 0)           # no duplicates
            ws = openpyxl.load_workbook(out)[W.LINES_SHEET]
            self.assertEqual([ws.cell(5, c).value for c in (2, 3, 4, 5, 6, 7)],
                             ["Lockbox", "Payer", "112938", 845.0, "S-INV1", None])
            self.assertEqual([ws.cell(6, c).value for c in (7, 10, 14)],
                             ["No invoice found", "Payment problem", "Open"])
            with self.assertRaises(FileExistsError): W.create_from_template(TPL, out)
if __name__ == "__main__": unittest.main()
