"""Transfer only pipeline.py to a fresh, offline verifier container."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

ROOT=Path(__file__).resolve().parent
IMAGE='pipeline-rescue:local'


def command(*args,**kwargs):
    return subprocess.run(['docker',*args],check=True,capture_output=True,text=True,timeout=120,**kwargs)


def verify(candidate,out):
    candidate=Path(candidate).resolve()
    if not candidate.is_file() or candidate.is_symlink() or candidate.stat().st_size>100000:
        raise ValueError('Submit a regular Python file no larger than 100KB')
    command('build','-t',IMAGE,str(ROOT/'task/environment'))
    container='pipeline-rescue-'+uuid.uuid4().hex[:12]
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    try:
        command('run','-d','--name',container,'--network','none','--memory','256m','--cpus','1',
                '--pids-limit','64','--cap-drop','ALL','--cap-add','SETUID','--cap-add','SETGID','--cap-add','FOWNER','--cap-add','DAC_OVERRIDE',
                '--security-opt','no-new-privileges',IMAGE)
        command('cp',str(candidate),container+':/app/pipeline.py')
        command('cp',str(ROOT/'task/tests'),container+':/tests')
        command('exec',container,'chmod','644','/app/pipeline.py')
        command('exec',container,'sh','/tests/test.sh')
        command('cp',container+':/logs/verifier/report.json',str(out/'report.json'))
        command('cp',container+':/logs/verifier/reward.txt',str(out/'reward.txt'))
        report=json.loads((out/'report.json').read_text())
        if report['reward'] not in (0,1) or int((out/'reward.txt').read_text())!=report['reward']:
            raise RuntimeError('Invalid verifier reward')
        return report
    finally:
        subprocess.run(['docker','rm','-f',container],capture_output=True,timeout=30)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate',type=Path)
    parser.add_argument('--out',type=Path,default=Path('work/verification'))
    args=parser.parse_args()
    result=verify(args.candidate,args.out)
    print(json.dumps({'reward':result['reward'],'passed':result['passed'],'total':result['total']},indent=2))
