#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#author: jartigag
#date: 2019-07-16

from elasticsearch import Elasticsearch, helpers
from datetime import datetime
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('file')
args = parser.parse_args()

if args.file:
    try:
        data = open(args.file).readlines()
        lines = [l.strip() for l in data]
        lines = lines[1:]
        msgs = []
        for i,l in enumerate(lines):
            print("loading line {}".format(i))
            pattern = re.compile('\d{1,2}\/\d{1,2}\/\d{2}')
            if not pattern.match(l):                                  # if line doesn't start with a '%d/%m/%y' datetime:
                msgs[-1]['text'] = "{} {}".format(msgs[-1]['text'],l) #     put this line with the previous line
            else:
                str_tstamp = l.split(' - ')[0]
                sender = l.split(' - ')[1].split(':')[0]
                text = l.split(': ')[1]
                msgs.append( {
                    'time':datetime.strptime(str_tstamp, '%d/%m/%y %H:%M').isoformat(),
                    'sender':sender,
                    'text': text
                } )
                print("{} - {}".format(i, msgs[-1]))

        client = Elasticsearch()
        actions = []
        for m in msgs:
            actions.append( {
                "_index": "msgs",
                "_source": {
                    "@timestamp": m['time'],
                    "sender": m['sender'],
                    "text": m['text']
                }
           } )
        
        helpers.bulk(client,actions)

    except FileNotFoundError as e:
        print(e)
