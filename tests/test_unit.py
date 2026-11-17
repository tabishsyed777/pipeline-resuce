import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('grader',ROOT/'task/tests/grade.py')
grade=importlib.util.module_from_spec(spec);spec.loader.exec_module(grade)

class UnitTests(unittest.TestCase):
    def test_generated_fixture_is_deterministic(self):
        self.assertEqual(grade.generated(7),grade.generated(7))

    def test_generated_expected_paid_orders(self):
        for seed in [7,19,83]:
            _,answer=grade.generated(seed)
            self.assertEqual(sum(r['orders'] for r in answer['rows']),33)
            self.assertEqual(answer['rows'],sorted(answer['rows'],key=lambda r:(r['day'],r['currency'])))

    def test_fixture_coverage(self):
        cases=grade.fixtures()
        self.assertEqual(len({r[0] for r in cases}),len(cases))
        self.assertEqual(len(cases),28)
        self.assertEqual(sum(r[2] is None for r in cases),17)

    def test_output_bool_is_not_money_integer(self):
        bad={'rows':[{'day':'2025-01-01','currency':'USD','orders':True,'revenue_cents':29}]}
        self.assertFalse(grade.valid_shape(bad))

    def test_unknown_output_key_rejected(self):
        self.assertFalse(grade.valid_shape({'rows':[],'extra':0}))

    def test_csv_preservation_must_compare_bytes(self):
        data=grade.csv_text([grade.row()])
        self.assertIn('\r\n',data)
        self.assertNotEqual(data,data.replace('\r\n','\n'))

if __name__=='__main__': unittest.main()
