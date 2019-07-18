#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#author: jartigag
#date: 2019-07-16

from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('file')
args = parser.parse_args()

if args.file:
    try:
        data = open(args.file).readlines()
        lines = [l.strip() for l in data]
        lines = lines[1:] # it removes "Los mensajes y llamadas en este chat ahora estan protegidos con cifrado de extremo a extremo. Toca para mas informacion."
        msgs = []
        for i,l in enumerate(lines):
            pattern = re.compile('\d{1,2}\/\d{1,2}\/\d{2}')
            if not pattern.match(l):                                  # if line doesn't start with a '%d/%m/%y' datetime:
                msgs[-1]['text'] = "{} {}".format(msgs[-1]['text'],l) #     put this line with the previous line
            else:
                str_tstamp = l.split(' - ')[0]
                sender = l.split(' - ')[1].split(':')[0]
                text = l.split(': ')[1]
                msgs.append( {
                    'tstamp': datetime.strptime(str_tstamp, '%d/%m/%y %H:%M').isoformat(),                # date of the message
                    'time': datetime.strptime("{} {}".format(                                             # time of the message, shifted to yesterday
                        (datetime.today()-timedelta(1)).strftime("%d/%m/%y"),str_tstamp.split(' ')[1]),   # (so messages can be grouped by hour)
                        '%d/%m/%y %H:%M').isoformat(),
                    'sender': sender,
                    'text': text,
                    'size': len(text) #TODO: in practice, it's encrypted, so.. maybe just normalizing size? as [very] small/medium/big, for example
                } )

        client = Elasticsearch()
        actions1 = []
        actions2 = []
        for m in msgs:
            actions1.append( {
                "_index": "msgs",
                "_source": {
                    "@timestamp": m['tstamp'],
                    "sender": m['sender'],
                    "text": m['text'],
                    "size": m['size']
                }
            } )
            actions2.append( { "_index": "msgs2",
                "_source": {
                    "@time": m['time'], # different datetime field. this will be used to show just 24h
                    "sender": m['sender'],
                    "text": m['text'],
                    "size": m['size']
                }
            } )
        
        helpers.bulk(client,actions1)
        helpers.bulk(client,actions2)
        print("{} docs inserted on the elasticsearch index 'msgs'".format(len(actions1)))
        print("{} docs inserted on the elasticsearch index 'msgs2'".format(len(actions2)))

    except FileNotFoundError as e:
        print(e)
