import os, sys, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import run_lockbox as R
from lockbox_pdf import LockboxItem


def item(batch, n, check, amt):
    return LockboxItem(batch, n, "2026-10-13", "P", check, "USD", Decimal(amt))


class T(unittest.TestCase):
    def test_reads_are_found_by_batch_and_item(self):
        items = [item("527", 1, "111", "10"), item("529", 1, "222", "20")]
        reads = [{"batch": "527", "item": 1, "payer": "A"}, {"batch": "529", "item": 1, "payer": "B"}]
        self.assertEqual([R._find_read(i, reads, items)["payer"] for i in items], ["A", "B"])

    def test_read_without_batch_is_refused_when_item_repeats(self):
        items = [item("527", 1, "111", "10"), item("529", 1, "222", "20")]
        with self.assertRaises(ValueError):
            R._find_read(items[0], [{"item": 1, "payer": "A"}], items)

    def test_read_without_batch_is_fine_when_item_is_unique(self):
        items = [item("527", 1, "111", "10"), item("527", 2, "222", "20")]
        self.assertEqual(R._find_read(items[1], [{"item": 2, "payer": "B"}], items)["payer"], "B")

    def test_canadian_lockbox_flags_every_item_and_marks_cad(self):
        items = [item("1", 1, "420", "44746.57")]
        ls = R.build_lines(items, [{"item": 1, "payer": "Foreseeson", "stub_invoices": ["S-INV000460"]}],
                           None, {"departments": {"default": [], "by_customer": {}}}, canadian=True)
        self.assertEqual((len(ls), ls[0].currency, ls[0].reason_code), (1, "CAD", "Canadian payment"))
        self.assertTrue(ls[0].known_exception); self.assertIn("known exception", ls[0].reason.lower()); self.assertIn("S-INV000460", ls[0].note)


if __name__ == "__main__": unittest.main()
