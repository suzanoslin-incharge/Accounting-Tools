import datetime as dt, os, sys, tempfile, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl, rules as R, learnings as Lr, transactions_metrics_writer as W, journal_writer as J
from bc_match import MatchResult

INV = {"number": "S-INV012544", "customerNumber": "C01871", "customerName": "Unfi",
       "shortcutDimension1Code": "4160", "shortcutDimension2Code": "P"}
TPL = os.path.join(os.path.dirname(__file__), "../../references/deposit-journal/Template_Transactions-and-Metrics.xlsx")

def lines(codes=("1000", "2000"), d="2026-10-01"):
    rules = R.load_rules("")
    rules["departments"]["default"] = list(codes)
    return J.lines_for_check(d, Decimal("300"), "UNFI", ["S-INV012544"],
                             [MatchResult("matched", invoice=dict(INV))], check_no="7", rules=rules)

class T(unittest.TestCase):
    def test_code_not_on_list_is_flagged_then_accepted(self):
        l = lines()[0]
        self.assertIn("not on the Dept codes list", l.reason)
        self.assertEqual((l.department, l.flag_type), ("4160", ""))          # copied as is, nothing to learn
        self.assertEqual(lines(("1000", "2000", "4160"))[0].reason, "")

    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_reads_codes_from_workbook(self):
        with tempfile.TemporaryDirectory() as d:
            wb = os.path.join(d, "m.xlsx"); W.create_from_template(TPL, wb)
            self.assertEqual(R.dept_codes(wb), ["1000", "2000", "5100", "4160", "9999", "2600", "2400"])
            w = openpyxl.load_workbook(wb); ws = w["Automation Lists"]
            ws["J13"] = "4161"; w.save(wb)                                  # a row someone adds counts at once
            self.assertIn("4161", R.dept_codes(wb))
            self.assertEqual(R.load_rules("", wb)["departments"]["default"][:2], ["1000", "2000"])

    def test_apply_and_retire(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            R.apply_proposal(p, {"type": "payer", "customer": "C1", "code": "Braman  Motors", "text": "t"}, approved_on="2026-11-11")
            self.assertTrue(R.payer_ok(R.load_rules(p), "C1", "braman motors"))
            R.retire_payer_rule(p, "C1", "Braman Motors")
            self.assertFalse(R.payer_ok(R.load_rules(p), "C1", "braman motors"))

    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_walter_fix_blocks_proposal(self):
        import bc_match as M
        bc = dict(PayerNames.BCINV)
        fetch = lambda e, f, s, t: [dict(bc)] if f.startswith("number eq") else []
        with tempfile.TemporaryDirectory() as d:
            wb, lp = os.path.join(d, "m.xlsx"), os.path.join(d, "learn.json")
            W.create_from_template(TPL, wb)
            for i, day in enumerate(("2026-10-01", "2026-10-02", "2026-10-05")):
                m = M.match_payment(fetch, "Braman  Motors", 100, ["S-INV013078"], day, None)
                ls = J.lines_for_check(day, Decimal("100"), "Braman  Motors", ["S-INV013078"], m, check_no=str(i))
                W.append_lines(wb, ls); Lr.record_flags(ls, day, lp)
            w = openpyxl.load_workbook(wb); ws = w[W.LINES_SHEET]
            for r, v in ((4, "No"), (5, "No"), (6, "Yes")): ws.cell(r, 14).value, ws.cell(r, 5).value = v, "Closed"
            w.save(wb); Lr.record_responses(wb, lp)
            self.assertEqual(Lr.make_proposals(lp), [])
class BlankDepartment(unittest.TestCase):
    """A blank invoice department: flagged, Walter types the code in the ADP journal, learned after three, then used."""
    def inv(self, n, dept):
        return {"number": n, "customerNumber": "C7", "customerName": "Acme", "status": "Open", "postingDate": "2026-09-01",
                "totalAmountExcludingTax": 100, "totalAmountIncludingTax": 100,
                "shortcutDimension1Code": dept, "shortcutDimension2Code": "P"}

    def fetcher(self, n):
        rows = [self.inv(f"S-INV00000{i}", "") for i in range(1, 4)]
        return lambda e, f, s, t: [r for r in rows if r["number"] == f.split("'")[1]] if f.startswith("number eq") else rows

    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_cycle(self):
        import bc_match as M
        with tempfile.TemporaryDirectory() as d:
            wb, lp = os.path.join(d, "m.xlsx"), os.path.join(d, "learn.json")
            W.create_from_template(TPL, wb)
            tpl_j = os.path.join(os.path.dirname(__file__), "../../references/deposit-journal/Template_Automated_Deposit_Journal.xlsx")
            for i, day in enumerate(("2026-10-01", "2026-10-02", "2026-10-05")):
                n = f"S-INV00000{i + 1}"
                m = M.match_payment(self.fetcher(i), "Acme", 100, [n], day, None, lambda c: [])
                self.assertEqual((m[0].status, m[0].flag[0]), ("flagged", "department"))
                ls = J.lines_for_check(day, Decimal("100"), "Acme", [n], m, check_no=str(i))
                W.append_lines(wb, ls); Lr.record_flags(ls, day, lp)
                out = os.path.join(d, day[:4] + "_" + day[5:7], "ADP_" + day.replace("-", ".") + ".xlsx")
                J.write_journal(tpl_j, out, ls)
                j = openpyxl.load_workbook(out); j["Lockbox"].cell(2, 11).value = "4160"; j.save(out)   # Walter types it
            w = openpyxl.load_workbook(wb); ws = w[W.LINES_SHEET]
            for r in (4, 5, 6): ws.cell(r, 14).value, ws.cell(r, 5).value = "Yes", "Closed"
            w.save(wb)
            self.assertEqual(Lr.record_responses(wb, lp), 3)
            self.assertEqual(Lr.record_journal_departments(d, lp), {"codes_read": 3, "skipped": 0})
            new = Lr.make_proposals(lp)
            self.assertEqual([(p["type"], p["customer"], p["code"]) for p in new], [("department", "C7", "4160")])
            Lr.decide(new[0]["id"], True, lp)
            rules = R.load_rules(lp)
            m = M.match_payment(self.fetcher(0), "Acme", 100, ["S-INV000001"], "2026-10-06", None,
                                lambda c: R.learned_depts(rules, c))
            self.assertEqual((m[0].status, m[0].invoice["shortcutDimension1Code"]), ("matched", "4160"))

    def test_two_learned_codes_still_flag(self):
        import bc_match as M
        m = M.match_payment(self.fetcher(0), "Acme", 100, ["S-INV000001"], "2026-10-06", None, lambda c: ["4160", "2000"])
        self.assertEqual(m[0].status, "flagged")


class PayerNames(unittest.TestCase):
    """A payer name that differs from the BC customer is flagged, learned after Walter confirms it, then accepted."""
    BCINV = {"number": "S-INV013078", "customerNumber": "C04456", "customerName": "Braman Cadillac",
             "status": "Paid", "postingDate": "2026-09-28", "totalAmountExcludingTax": 100,
             "totalAmountIncludingTax": 100, "shortcutDimension1Code": "2000", "shortcutDimension2Code": "P"}

    def fetch(self, entity, flt, select, top):
        return [dict(self.BCINV)] if flt.startswith("number eq") else []

    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_payer_name_learning_cycle(self):
        import bc_match as M
        with tempfile.TemporaryDirectory() as d:
            wb, lp = (os.path.join(d, n) for n in ("m.xlsx", "learn.json")); rp = lp
            W.create_from_template(TPL, wb)
            rules = R.load_rules(rp)
            known = lambda c, p: R.payer_ok(rules, c, p)
            days = ("2026-10-01", "2026-10-02", "2026-10-05")
            for i, day in enumerate(days):
                m = M.match_payment(self.fetch, "Braman  Motors", 100, ["S-INV013078"], day, known)
                self.assertEqual((m[0].status, m[0].code), ("flagged", "Payer name unclear"))
                ls = J.lines_for_check(day, Decimal("100"), "Braman  Motors", ["S-INV013078"], m, check_no=str(i), rules=rules)
                self.assertEqual((ls[0].flag_type, ls[0].flag_customer, ls[0].flag_detail), ("payer", "C04456", "Braman Cadillac"))
                W.append_lines(wb, ls); Lr.record_flags(ls, day, lp)
            w = openpyxl.load_workbook(wb); ws = w[W.LINES_SHEET]
            for r in (4, 5, 6): ws.cell(r, 14).value, ws.cell(r, 5).value = "No", "Closed"
            w.save(wb)
            self.assertEqual(Lr.record_responses(wb, lp), 3)
            new = Lr.make_proposals(lp)
            self.assertEqual([(p["type"], p["customer"], p["code"]) for p in new], [("payer", "C04456", "braman motors")])
            self.assertIn("Braman Cadillac", new[0]["text"])
            Lr.decide(new[0]["id"], True, lp)
            rules = R.load_rules(rp)
            known = lambda c, p: R.payer_ok(rules, c, p)
            m = M.match_payment(self.fetch, "BRAMAN MOTORS", 100, ["S-INV013078"], "2026-10-06", known)
            self.assertEqual(m[0].status, "matched")                                   # accepted now
            self.assertEqual(Lr.make_proposals(lp), [])                            # and not suggested again
            R.retire_payer_rule(rp, "C04456", "Braman Motors")
            self.assertFalse(R.payer_ok(R.load_rules(rp), "C04456", "braman motors"))


if __name__ == "__main__": unittest.main()

class Prune(unittest.TestCase):
    def _flag(self, day, resp):
        return {"raised_on": day, "type": "department", "customer": "C1", "code": "4160", "payment_date": day,
                "check_no": "1", "invoice": "I" + day, "response": resp}
    def test_prune(self):
        ok = {"fixed": "No", "cause": "Payment problem", "seen_on": "x"}
        with tempfile.TemporaryDirectory() as d:
            lp = rp = os.path.join(d, "l.json")
            data = Lr.load(lp)
            data["flags"] = [self._flag("2026-06-01", ok), self._flag("2026-06-02", ok), self._flag("2026-06-03", ok),
                             self._flag("2026-08-01", None), self._flag("2026-11-01", ok), self._flag("2026-09-20", None)]
            data["proposals"] = [{"id": "P001", "type": "department", "customer": "Z", "code": "1", "status": "declined",
                                  "decided_on": "2026-01-01", "confirmed_count": 3},
                                 {"id": "P002", "type": "department", "customer": "Y", "code": "1", "status": "pending",
                                  "decided_on": "", "confirmed_count": 3}]
            Lr.save(data, lp)
            out = Lr.prune(lp, "2026-11-11")
            self.assertEqual((out["flags_rolled_up"], out["flags_kept"], out["suggestions_removed"]), (4, 2, 0))
            data = Lr.load(lp)
            s = data["summaries"][0]
            self.assertEqual((s["fine"], s["no_answer"], s["first"]), (3, 1, "2026-06-01"))
            self.assertEqual([p["id"] for p in data["proposals"]], ["P001", "P002"])   # declined and pending stay
            self.assertEqual(Lr.reopen("P001", lp, "2026-11-11")["status"], "pending")
            with self.assertRaises(ValueError): Lr.reopen("P002", lp)
            # the counts still drive suggestions: 3 rolled-up fine + 1 live fine = 4
            self.assertEqual(Lr.make_proposals(lp, "2026-11-11")[0]["confirmed_count"], 4)
            self.assertEqual(Lr.prune(lp, "2026-11-11")["flags_rolled_up"], 0)   # running twice changes nothing
if __name__ == "__main__": unittest.main()
