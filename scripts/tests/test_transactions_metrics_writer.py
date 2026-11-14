import datetime as dt, os, sys, tempfile, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl
import transactions_metrics_writer as W
from journal_writer import JournalLine

TPL = os.path.join(os.path.dirname(__file__), "../../references/deposit-journal/Template_Transactions-and-Metrics.xlsx")
def line(inv, code="", amt="845", check="112938", payer="Payer", item=""):
    return JournalLine(dt.date(2026,10,1), "BC Name", Decimal(amt), "Customer", "C1", "2000", "P",
                       inv, "detail" if code else "", code, "note", payer, check, item_no=item)

@unittest.skipUnless(os.path.exists(TPL), "template not available")
class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.d.name, "m.xlsx")
        W.create_from_template(TPL, self.out)
    def tearDown(self): self.d.cleanup()
    def sheet(self): return openpyxl.load_workbook(self.out)[W.LINES_SHEET]

    def test_template_is_clean(self):
        ws = self.sheet()
        self.assertIsNone(ws["A4"].value); self.assertTrue(str(ws["P4"].value).startswith("=IF"))
        with self.assertRaises(FileExistsError): W.create_from_template(TPL, self.out)

    def test_one_row_per_payment(self):
        s = W.append_lines(self.out, [line("S-INV1", amt="500"), line("S-INV2", amt="345")])
        self.assertEqual((s["added"], s["updated"], s["unchanged"]), (1, 0, 0))
        ws = self.sheet()
        self.assertEqual([ws.cell(4, c).value for c in (11, 8, 9, 2, 10, 7, 6)],
                         ["Lockbox", "Payer", "112938", 845.0, "S-INV1, S-INV2", None, None])   # remittance link stays blank
        self.assertIsNone(ws["A5"].value)

    def test_flagged_payment(self):
        W.append_lines(self.out, [line("S-INV2", "No invoice found")])
        ws = self.sheet()
        self.assertEqual([ws.cell(4, c).value for c in (7, 13, 5)], ["No invoice found", "Needs review", "Open"])      # the tool is unsure: orange

    def test_rerun_adds_nothing_and_keeps_walters_columns(self):
        W.append_lines(self.out, [line("S-INV1", "No invoice found")])
        wb = openpyxl.load_workbook(self.out); ws = wb[W.LINES_SHEET]
        ws["N4"], ws["L4"], ws["M4"] = "Yes", "Walter's note", "Tool problem"; wb.save(self.out)
        s = W.append_lines(self.out, [line("S-INV1", "No invoice found")])
        self.assertEqual((s["added"], s["updated"], s["unchanged"]), (0, 0, 1))
        ws = self.sheet()
        self.assertEqual((ws["N4"].value, ws["L4"].value, ws["M4"].value), ("Yes", "Walter's note", "Tool problem"))
        self.assertIsNone(ws["A5"].value)

    def test_rerun_updates_tool_columns_on_an_open_row_only(self):
        W.append_lines(self.out, [line("S-INV1", "No invoice found")])
        s = W.append_lines(self.out, [line("S-INV1")])                       # now matched
        self.assertEqual(s["updated"], 1)
        self.assertIsNone(self.sheet()["G4"].value)
        wb = openpyxl.load_workbook(self.out); wb[W.LINES_SHEET]["E4"] = "Closed"; wb[W.LINES_SHEET]["G4"] = "Overpayment"; wb.save(self.out)
        s = W.append_lines(self.out, [line("S-INV1")])
        self.assertEqual((s["updated"], s["unchanged"]), (0, 1))             # closed rows are not touched
        self.assertEqual(self.sheet()["G4"].value, "Overpayment")

    def test_amount_change_on_rerun_is_reported_not_overwritten(self):
        W.append_lines(self.out, [line("S-INV1")])
        s = W.append_lines(self.out, [line("S-INV1", amt="900")])
        self.assertEqual(s["changed"], [{"date": "2026-10-01", "payer": "Payer", "check": "112938", "was": 845.0, "now": 900.0}])
        self.assertEqual(self.sheet()["B4"].value, 845.0)

    def test_same_check_number_other_payer_is_flagged(self):
        W.append_lines(self.out, [line("S-INV1")])
        s = W.append_lines(self.out, [line("S-INV9", payer="Payer Inc")])
        self.assertEqual((s["added"], len(s["possible_duplicates"])), (1, 1))
        ws = self.sheet()
        self.assertEqual(ws["G5"].value, "Invoice already paid (possible duplicate)")
        self.assertIn("row 4", ws["L5"].value)

    def test_blank_check_number_uses_item_number(self):
        W.append_lines(self.out, [line("S-INV1", check="", item="4")])
        self.assertEqual(self.sheet()["I4"].value, "item 4")
        s = W.append_lines(self.out, [line("S-INV1", check="", item="4")])
        self.assertEqual(s["unchanged"], 1)

    def test_payer_spacing_and_case_do_not_matter(self):
        W.append_lines(self.out, [line("S-INV1", payer="Payer  Inc")])
        s = W.append_lines(self.out, [line("S-INV1", payer="payer inc")])
        self.assertEqual((s["added"], s["unchanged"]), (0, 1))

    def test_canadian_payment_gets_cad_first_in_notes(self):
        cad, usd = line("S-INV1", payer="Maple Ltd", check="1"), line("S-INV2", payer="Eagle Inc", check="2")
        cad.currency = "CAD"
        W.append_lines(self.out, [cad, usd])
        ws = self.sheet()
        self.assertEqual(ws["L4"].value, "CAD; note")
        self.assertEqual(ws["L5"].value, "note")

    def test_known_exceptions_are_marked(self):
        cad = line("S-INV1", "Canadian payment", payer="Maple Ltd", check="1"); cad.currency, cad.known_exception = "CAD", True
        refund = line("", "Refund, reversal or returned payment", payer="State Refund", check="2")
        W.append_lines(self.out, [cad, refund])
        ws = self.sheet()
        self.assertEqual([ws["M4"].value, ws["M5"].value], ["Known exception", "Known exception"])   # yellow
        self.assertEqual(ws["G4"].value, "Canadian payment")

    def test_open_workbook_is_not_written(self):
        open(os.path.join(self.d.name, "~$m.xlsx"), "w").close()
        with self.assertRaises(W.WorkbookOpen): W.append_lines(self.out, [line("S-INV1")])
        os.remove(os.path.join(self.d.name, "~$m.xlsx"))
        self.assertIsNone(self.sheet()["A4"].value)
if __name__ == "__main__": unittest.main()
