"""Check recorded Harbor rewards, not just the runner's exit status."""
import argparse
import json
from pathlib import Path


def check(job,expected):
    trials=list(Path(job).glob('*/result.json'))
    if len(trials)!=1: raise ValueError('Expected exactly one completed trial')
    result=json.loads(trials[0].read_text())
    if result.get('exception_info') is not None: raise ValueError('Trial contains an exception')
    reward=result.get('verifier_result',{}).get('rewards',{}).get('reward')
    if reward!=expected: raise ValueError(f'Expected reward {expected}, got {reward}')
    evidence=trials[0].parent/'verifier/reward.txt'
    if float(evidence.read_text())!=expected: raise ValueError('Reward file does not match trial result')
    return {'reward':reward,'exception':None}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('job',type=Path)
    parser.add_argument('expected',type=int,choices=[0,1])
    args=parser.parse_args()
    print(json.dumps(check(args.job,args.expected)))
