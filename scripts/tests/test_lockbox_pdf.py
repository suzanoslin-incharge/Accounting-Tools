"""Test on the real 2026-10-01 lockbox PDF (skipped if the file is not on this Mac)."""
import os, sys, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import lockbox_pdf as L

PDF = os.path.expanduser("~/OneDrive - In Charge Service/Accounting - Internal - Documents/Bank/"
                         "Checks Received/Received into QB by O2C/Lockbox 2026.10.01.pdf")

@unittest.skipUnless(os.path.exists(PDF), "lockbox PDF not available")
class T(unittest.TestCase):
    def test_2026_10_01(self):
        items = L.read_items(PDF)
        self.assertEqual([i.check_no for i in items], ["112938","262484","6875","7253097","103817","516206"])
        self.assertEqual([str(i.amount) for i in items],
                         ["845.00","3033.54","4008.16","300.00","4896.00","3279.98"])
        self.assertEqual(sum(len(i.pages) for i in items), 13)
        self.assertEqual(items[0].value_date, "2026-10-01")
        self.assertTrue(L.tie_out(items, Decimal("16362.68"))["ties"])
        self.assertFalse(L.tie_out(items, Decimal("16362.69"))["ties"])
if __name__ == "__main__": unittest.main()
