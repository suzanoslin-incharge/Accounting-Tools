import datetime as dt, os, shutil, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl
import list_sync as S

TPL = os.path.join(os.path.dirname(__file__), "../../references/deposit-journal/Template_Transactions-and-Metrics.xlsx")


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.live, self.tpl = (os.path.join(self.d.name, n) for n in ("live.xlsx", "tpl.xlsx"))
        shutil.copyfile(TPL, self.live); shutil.copyfile(TPL, self.tpl)
    def tearDown(self): self.d.cleanup()
    def edit_live(self, fn):
        wb = openpyxl.load_workbook(self.live); fn(wb[S.SHEET]); wb.save(self.live)
    def tpl_sheet(self): return openpyxl.load_workbook(self.tpl)[S.SHEET]

    def test_nothing_new(self):
        r = S.sync_lists(self.live, self.tpl)
        self.assertEqual((r["added"], r["changed"], r["only_in_template"], r["not_copied"]), ([], [], [], False))

    def test_new_rows_are_copied_to_the_template(self):
        def add(ws):
            ws["A23"], ws["B23"], ws["C23"] = "Wire fee", "6. Not a customer invoice payment", "Lindsey"
            ws["J13"], ws["K13"], ws["N13"] = "4161", "A new code", "Unconfirmed"
        self.edit_live(add)
        r = S.sync_lists(self.live, self.tpl)
        self.assertEqual(sorted(x["list"] for x in r["added"]), ["Dept code", "Reason"])
        ws = self.tpl_sheet()
        self.assertEqual((ws["A23"].value, ws["C23"].value), ("Wire fee", "Lindsey"))
        self.assertEqual((ws["J13"].value, ws["N13"].value), ("4161", "Unconfirmed"))
        self.assertEqual(S.sync_lists(self.live, self.tpl)["added"], [])          # a second run adds nothing

    def test_edited_row_is_reported_not_copied(self):
        self.edit_live(lambda ws: ws.cell(5, 11).__setattr__("value", "Something else"))   # meaning of 1000
        r = S.sync_lists(self.live, self.tpl)
        self.assertEqual([(x["list"], x["key"]) for x in r["changed"]], [("Dept code", "1000")])
        self.assertEqual(self.tpl_sheet()["K5"].value, "Generally non-service payments")

    def test_row_only_in_template_is_reported(self):
        self.edit_live(lambda ws: [ws.cell(12, c).__setattr__("value", None) for c in range(10, 16)])   # (blank) row
        r = S.sync_lists(self.live, self.tpl)
        self.assertEqual([(x["list"], x["key"]) for x in r["only_in_template"]], [("Dept code", "(blank)")])
        self.assertEqual(self.tpl_sheet()["J12"].value, "(blank)")

    def test_full_dept_table_is_extended(self):
        def fill(ws):
            for i in range(13):                                  # the table has 12 rows, rows 5 to 16; add below
                ws.cell(17 + i, 10).value = f"{7000 + i}"
            ws.tables["DeptCodes"].ref = "J4:O29"                  # Excel grows the table when a row is typed under it
        self.edit_live(fill)
        r = S.sync_lists(self.live, self.tpl)
        self.assertEqual(len(r["added"]), 13)
        wb = openpyxl.load_workbook(self.tpl)
        self.assertEqual(wb[S.SHEET].tables["DeptCodes"].ref, "J4:O25")

    def test_open_template_is_not_written(self):
        self.edit_live(lambda ws: ws.__setitem__("A23", "Wire fee"))
        open(os.path.join(self.d.name, "~$tpl.xlsx"), "w").close()
        r = S.sync_lists(self.live, self.tpl)
        self.assertTrue(r["not_copied"]); self.assertEqual(len(r["added"]), 1)
        self.assertIsNone(self.tpl_sheet()["A23"].value)


if __name__ == "__main__": unittest.main()
