"""Reference implementation; not part of the agent image."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime,timezone

FIELDS={'event_id','order_id','event_time','status','amount','currency'}
TIME=re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',re.ASCII)
MONEY=re.compile(r'[0-9]+(?:\.[0-9]{1,2})?',re.ASCII)


def transform(path):
    seen={};latest={}
    with open(path,encoding='utf-8',newline='') as handle:
        reader=csv.DictReader(handle,strict=True)
        names=reader.fieldnames
        if names is None or len(names)!=len(FIELDS) or set(names)!=FIELDS:
            raise ValueError('Invalid headers')
        for row in reader:
            if set(row)!=FIELDS or any(v is None or not isinstance(v,str) or v=='' for v in row.values()):
                raise ValueError('Missing or extra field')
            for field in ('event_id','order_id'):
                if row[field]!=row[field].strip(): raise ValueError('Invalid ID')
            if not TIME.fullmatch(row['event_time']): raise ValueError('Invalid timestamp format')
            stamp=datetime.fromisoformat(row['event_time'].replace('Z','+00:00')).astimezone(timezone.utc)
            if row['status'] not in ('paid','refunded','cancelled'): raise ValueError('Invalid status')
            if not re.fullmatch('[A-Z]{3}',row['currency'],re.ASCII): raise ValueError('Invalid currency')
            if not MONEY.fullmatch(row['amount']): raise ValueError('Invalid amount')
            whole,_,fraction=row['amount'].partition('.')
            cents=int(whole)*100+int((fraction+'00')[:2])
            event=row['event_id']
            if event in seen:
                if seen[event]!=row: raise ValueError('Conflicting event ID')
                continue
            seen[event]=row
            order=row['order_id']
            candidate=(stamp,event,row,cents)
            if order not in latest or candidate[:2]>latest[order][:2]: latest[order]=candidate
    groups={}
    for stamp,event,row,cents in latest.values():
        if row['status']!='paid': continue
        key=(stamp.date().isoformat(),row['currency'])
        group=groups.setdefault(key,{'day':key[0],'currency':key[1],'orders':0,'revenue_cents':0})
        group['orders']+=1
        group['revenue_cents']+=cents
    return {'rows':[groups[key] for key in sorted(groups)]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve(): raise ValueError('Input and output must differ')
    result=transform(args.input)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=args.output.parent,delete=False) as handle:
            temporary=handle.name
            json.dump(result,handle,sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary,args.output)
        temporary=None
    finally:
        if temporary: os.unlink(temporary)

if __name__=='__main__': main()
