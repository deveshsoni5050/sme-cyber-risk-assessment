import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import risk_assessment as ra

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


class Tests(unittest.TestCase):
    def test_score_and_band(self):
        self.assertEqual(ra.score(5, 4), 20)
        self.assertEqual(ra.band(20), "Critical")
        self.assertEqual(ra.band(19), "High")
        self.assertEqual(ra.band(12), "High")
        self.assertEqual(ra.band(11), "Medium")
        self.assertEqual(ra.band(5), "Low")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            ra.score(6, 1)
        with self.assertRaises(ValueError):
            ra.score(0, 3)

    def test_baseline_ranking(self):
        ranked = ra.rank_rows(ra.read_csv(os.path.join(DATA, "risk_register.csv")))
        self.assertEqual([r["band"] for r in ranked[:3]], ["Critical"] * 3)
        self.assertEqual(ranked[-1]["threat"], "Website / DoS attack")

    def test_case_totals(self):
        cases = ra.summarize_cases(ra.read_csv(os.path.join(DATA, "case_studies.csv")))
        got = {k.split(":")[0]: (v["before"], v["after"]) for k, v in cases.items()}
        self.assertEqual(got, {"A": (71, 32), "B": (87, 48), "C": (83, 46)})


if __name__ == "__main__":
    unittest.main()
