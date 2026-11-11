import datetime as dt, os, sys, tempfile, unittest
from decimal import Decimal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl, rules as R, learnings as Lr, measures_writer as W, journal_writer as J
from bc_match import MatchResult

INV = {"number": "S-INV012544", "customerNumber": "C01871", "customerName": "Unfi",
       "shortcutDimension1Code": "4160", "shortcutDimension2Code": "P"}
TPL = os.path.expanduser("~/OneDrive - In Charge Service/Accounting - Internal - Documents/Automation/"
      "Bank-Deposits-Automation/Bank-Deposits-Automation_KPI-Tracker-Template.xlsx")

def lines(rules=None, d="2026-10-01"):
    return J.lines_for_check(d, Decimal("300"), "UNFI", ["S-INV012544"],
                             [MatchResult("matched", invoice=dict(INV))], check_no="7", rules=rules)

class T(unittest.TestCase):
    def test_flag_then_accept(self):
        self.assertTrue(lines()[0].reason)
        rules = R.load_rules("")
        rules["departments"]["by_customer"]["C01871"] = {"codes": ["4160"]}
        self.assertEqual(lines(rules)[0].reason, "")
    def test_apply_and_retire(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            R.apply_proposal(p, {"type": "department", "customer": "C01871", "code": "4160", "text": "t"}, approved_on="2026-11-11")
            self.assertTrue(R.department_ok(R.load_rules(p), "C01871", "4160"))
            self.assertFalse(R.department_ok(R.load_rules(p), "C99999", "4160"))
            R.retire_rule(p, "C01871", "4160")
            self.assertFalse(R.department_ok(R.load_rules(p), "C01871", "4160"))

    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_learning_cycle(self):
        with tempfile.TemporaryDirectory() as d:
            wb, lp, rp = (os.path.join(d, n) for n in ("m.xlsx", "learn.json", "rules.json"))
            W.create_from_template(TPL, wb)
            days = ("2026-10-01", "2026-10-02", "2026-10-05")
            for day in days:
                ls = lines(d=day); W.append_lines(wb, ls); Lr.record_flags(ls, day, lp)
            Lr.record_flags(lines(d=days[0]), days[0], lp)                       # no duplicate flags
            self.assertEqual(len(Lr.load(lp)["flags"]), 3)
            def answer(fixed, rows):
                w = openpyxl.load_workbook(wb); ws = w[W.LINES_SHEET]
                for r in rows: ws.cell(r, 11).value, ws.cell(r, 14).value = fixed, "Closed"
                w.save(wb)
            self.assertEqual(Lr.record_responses(wb, lp), 0)                      # nothing answered yet
            answer("No", [5, 6, 7])
            self.assertEqual(Lr.record_responses(wb, lp), 3)
            new = Lr.make_proposals(rp, lp)
            self.assertEqual((new[0]["customer"], new[0]["code"], new[0]["confirmed_count"]), ("C01871", "4160", 3))
            self.assertEqual(Lr.make_proposals(rp, lp), [])                       # not proposed twice
            Lr.decide(new[0]["id"], False, lp, rp)                                # Suzan declines
            self.assertEqual(Lr.make_proposals(rp, lp), [])                       # stays quiet
            self.assertFalse(R.department_ok(R.load_rules(rp), "C01871", "4160"))
            ls = lines(d="2026-10-06"); W.append_lines(wb, ls); Lr.record_flags(ls, "2026-10-06", lp)
            answer("No", [8]); Lr.record_responses(wb, lp)
            again = Lr.make_proposals(rp, lp)                                     # one more confirmed line: asks again
            self.assertEqual(again[0]["confirmed_count"], 4)
            Lr.decide(again[0]["id"], True, lp, rp, "2026-11-12")                 # Suzan approves
            self.assertTrue(R.department_ok(R.load_rules(rp), "C01871", "4160"))
            self.assertEqual(lines(R.load_rules(rp))[0].reason, "")
    @unittest.skipUnless(os.path.exists(TPL), "template not available")
    def test_walter_fix_blocks_proposal(self):
        with tempfile.TemporaryDirectory() as d:
            wb, lp, rp = (os.path.join(d, n) for n in ("m.xlsx", "learn.json", "rules.json"))
            W.create_from_template(TPL, wb)
            for day in ("2026-10-01", "2026-10-02", "2026-10-05"):
                ls = lines(d=day); W.append_lines(wb, ls); Lr.record_flags(ls, day, lp)
            w = openpyxl.load_workbook(wb); ws = w[W.LINES_SHEET]
            for r, v in ((5, "No"), (6, "No"), (7, "Yes")): ws.cell(r, 11).value, ws.cell(r, 14).value = v, "Closed"
            w.save(wb); Lr.record_responses(wb, lp)
            self.assertEqual(Lr.make_proposals(rp, lp), [])
if __name__ == "__main__": unittest.main()

class Prune(unittest.TestCase):
    def _flag(self, day, resp):
        return {"raised_on": day, "type": "department", "customer": "C1", "code": "4160", "payment_date": day,
                "check_no": "1", "invoice": "I" + day, "response": resp}
    def test_prune(self):
        ok = {"fixed": "No", "cause": "Payment problem", "seen_on": "x"}
        with tempfile.TemporaryDirectory() as d:
            lp, rp = os.path.join(d, "l.json"), os.path.join(d, "r.json")
            R.save_rules(rp, R.load_rules(""))
            data = Lr.load(lp)
            data["flags"] = [self._flag("2026-06-01", ok), self._flag("2026-06-02", ok), self._flag("2026-06-03", ok),
                             self._flag("2026-08-01", None), self._flag("2026-11-01", ok), self._flag("2026-09-20", None)]
            data["proposals"] = [{"id": "P001", "type": "department", "customer": "Z", "code": "1", "status": "declined",
                                  "decided_on": "2026-01-01", "confirmed_count": 3},
                                 {"id": "P002", "type": "department", "customer": "Y", "code": "1", "status": "pending",
                                  "decided_on": "", "confirmed_count": 3}]
            Lr.save(data, lp)
            out = Lr.prune(rp, lp, "2026-11-11")
            self.assertEqual((out["flags_rolled_up"], out["flags_kept"], out["suggestions_removed"]), (4, 2, 0))
            data = Lr.load(lp)
            s = data["summaries"][0]
            self.assertEqual((s["fine"], s["no_answer"], s["first"]), (3, 1, "2026-06-01"))
            self.assertEqual([p["id"] for p in data["proposals"]], ["P001", "P002"])   # declined and pending stay
            self.assertEqual(Lr.reopen("P001", lp, "2026-11-11")["status"], "pending")
            with self.assertRaises(ValueError): Lr.reopen("P002", lp)
            # the counts still drive suggestions: 3 rolled-up fine + 1 live fine = 4
            self.assertEqual(Lr.make_proposals(rp, lp, "2026-11-11")[0]["confirmed_count"], 4)
            self.assertEqual(Lr.prune(rp, lp, "2026-11-11")["flags_rolled_up"], 0)   # running twice changes nothing
if __name__ == "__main__": unittest.main()
