"""Independent behavioral verifier. Never imports candidate or reference code."""
import csv
import io
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

HEADER=['event_id','order_id','event_time','status','amount','currency']


def csv_text(rows,header=HEADER):
    out=io.StringIO(newline='')
    writer=csv.writer(out);writer.writerow(header);writer.writerows(rows)
    return out.getvalue()


def row(event='e1',order='o1',time='2025-01-01T12:00:00Z',status='paid',amount='0.29',currency='USD'):
    return [event,order,time,status,amount,currency]


def expected(*rows): return {'rows':list(rows)}


def generated(seed):
    rng=random.Random(seed);records=[];totals={}
    for i in range(45):
        cents=rng.randrange(1,200000);currency=rng.choice(['USD','EUR','JPY'])
        day=1+i%9;status='refunded' if i%4==0 else 'paid'
        event=row(f'{i}-old',f'order-{i}',f'2025-02-{day:02}T00:00:00Z','paid','999.99',currency)
        final=row(f'{i}-latest',f'order-{i}',f'2025-02-{day:02}T03:00:00+02:00',status,f'{cents//100}.{cents%100:02}',currency)
        records += [event,final,final.copy()]
        if status=='paid':
            key=(f'2025-02-{day:02}',currency)
            count,total=totals.get(key,(0,0));totals[key]=(count+1,total+cents)
    rng.shuffle(records)
    answer=expected(*[{'day':d,'currency':c,'orders':v[0],'revenue_cents':v[1]} for (d,c),v in sorted(totals.items())])
    return csv_text(records),answer


def fixtures():
    single=expected({'day':'2025-01-01','currency':'USD','orders':1,'revenue_cents':29})
    cases=[('exact_cents',csv_text([row()]),single),
           ('empty',csv_text([]),expected()),
           ('duplicate_event',csv_text([row(),row()]),single),
           ('latest_refund',csv_text([row('z',time='2025-01-02T00:00:00Z',status='refunded'),row()]),expected()),
           ('utc_boundary',csv_text([row(time='2025-01-02T00:30:00+02:00')]),single),
           ('tie_break',csv_text([row('z',amount='0.29'),row('a',status='cancelled')]),single),
           ('currency_and_sort',csv_text([row('b','b',amount='5',currency='USD'),row('a','a',amount='1.2',currency='EUR')]),expected(
               {'day':'2025-01-01','currency':'EUR','orders':1,'revenue_cents':120},
               {'day':'2025-01-01','currency':'USD','orders':1,'revenue_cents':500})),
           ('large_integer_money',csv_text([row(amount='90071992547409.93')]),expected({'day':'2025-01-01','currency':'USD','orders':1,'revenue_cents':9007199254740993}))]
    for seed in [7,19,83]:
        data,answer=generated(seed);cases.append((f'generated_{seed}',data,answer))
    invalid=[('conflicting_duplicate',csv_text([row(),row(amount='1')])),
             ('missing_header','event_id,order_id\ne1,o1\n'),
             ('duplicate_header',csv_text([row()],HEADER[:-1]+['amount'])),
             ('extra_field',csv_text([row()+['extra']])),
             ('missing_field',csv_text([row()[:-1]])),
             ('bad_status',csv_text([row(status='unknown')])),
             ('bad_currency',csv_text([row(currency='usd')])),
             ('bad_id',csv_text([row(order=' o1')])),
             ('naive_time',csv_text([row(time='2025-01-01T12:00:00')])),
             ('invalid_date',csv_text([row(time='2025-02-30T00:00:00Z')]))]
    for amount in ['NaN','Infinity','-1','+1','1e3','0.001',' 1']:
        invalid.append(('invalid_money_'+repr(amount),csv_text([row(amount=amount)])))
    return cases+[(name,data,None) for name,data in invalid]


def valid_shape(value):
    return (type(value) is dict and set(value)=={'rows'} and type(value['rows']) is list
            and all(type(r) is dict and set(r)=={'day','currency','orders','revenue_cents'}
                    and type(r['day']) is str and type(r['currency']) is str
                    and type(r['orders']) is int and type(r['revenue_cents']) is int for r in value['rows']))


def invoke(candidate,source,target):
    kwargs={}
    if os.geteuid()==0: kwargs={'user':65534,'group':65534,'extra_groups':[]}
    return subprocess.run([sys.executable,'-I',str(candidate),'--input',str(source),'--output',str(target)],
        timeout=3,capture_output=True,cwd='/tmp',env={'PATH':'/usr/local/bin:/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'},**kwargs)


def verify(candidate):
    results=[]
    with tempfile.TemporaryDirectory(prefix='pipeline-check-') as name:
        base=Path(name);base.chmod(0o755)
        for index,(title,data,answer) in enumerate(fixtures()):
            for existing in ([True,False] if answer is None else [True]):
                folder=base/f'{index}-{existing}';folder.mkdir();folder.chmod(0o777)
                source=folder/'events.csv';source.write_text(data,encoding='utf-8');source.chmod(0o444)
                target=folder/'result.json'
                if existing: target.write_text('existing output must survive invalid input');target.chmod(0o666)
                inode=target.stat().st_ino if existing else None
                try:
                    proc=invoke(candidate,source,target)
                    if answer is None:
                        passed=proc.returncode!=0 and (target.read_text()=='existing output must survive invalid input' if existing else not target.exists())
                    else:
                        actual=json.loads(target.read_text())
                        passed=(proc.returncode==0 and valid_shape(actual) and actual==answer
                                and target.stat().st_ino!=inode)
                    error=None
                except Exception as exc: passed,error=False,type(exc).__name__+': '+str(exc)
                results.append({'name':title+('_existing' if existing else '_absent'),'passed':bool(passed),'error':error})
        folder=base/'same-path';folder.mkdir();folder.chmod(0o777)
        source=folder/'events.csv';data=csv_text([row()]);source.write_text(data);source.chmod(0o666)
        try:
            proc=invoke(candidate,source,source)
            passed=proc.returncode!=0 and source.read_bytes()==data.encode()
        except Exception: passed=False
        results.append({'name':'same_input_output_rejected','passed':passed})
    return {'reward':int(all(r['passed'] for r in results)), 'passed':sum(r['passed'] for r in results),
            'total':len(results),'checks':results}

if __name__=='__main__':
    report=verify(Path(sys.argv[1] if len(sys.argv)>1 else '/app/pipeline.py'))
    output=Path('/logs/verifier');output.mkdir(parents=True,exist_ok=True)
    (output/'reward.txt').write_text(str(report['reward'])+'\n')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    # Verifier itself completed normally even when the candidate earns zero.
