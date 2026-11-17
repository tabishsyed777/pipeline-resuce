"""Broken starter: repair this file according to the instruction."""
import argparse
import csv
import json


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    groups={}
    with open(args.input) as handle:
        for row in csv.DictReader(handle):
            if row['status'] != 'paid': continue
            key=(row['event_time'][:10],row['currency'])
            item=groups.setdefault(key,{'day':key[0],'currency':key[1],'orders':0,'revenue_cents':0})
            item['orders']+=1
            item['revenue_cents']+=int(float(row['amount'])*100)
    with open(args.output,'w') as handle:
        json.dump({'rows':list(groups.values())},handle)

if __name__=='__main__': main()
