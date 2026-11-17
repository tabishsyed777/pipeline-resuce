from pathlib import Path
import tempfile
import unittest
from verify import verify, ROOT

class ContainerTests(unittest.TestCase):
    def test_reference_passes_every_check(self):
        with tempfile.TemporaryDirectory() as out:
            result=verify(ROOT/'task/solution/pipeline.py',out)
        self.assertEqual(result['reward'],1,result)
        self.assertEqual(result['passed'],46)

    def test_starter_fails(self):
        with tempfile.TemporaryDirectory() as out:
            result=verify(ROOT/'task/environment/pipeline.py',out)
        self.assertEqual(result['reward'],0)
        self.assertLess(result['passed'],result['total'])

    def test_hardcoded_sample_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate=Path(tmp)/'pipeline.py'
            candidate.write_text('import argparse,json\np=argparse.ArgumentParser()\np.add_argument("--input")\np.add_argument("--output")\na=p.parse_args()\nwith open(a.output,"w") as f: json.dump({"rows":[]},f)\n')
            result=verify(candidate,Path(tmp)/'evidence')
        self.assertEqual(result['reward'],0)

if __name__=='__main__': unittest.main()
