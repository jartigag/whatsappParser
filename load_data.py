#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#author: jartigag
#date: 2019-07-21

#TODO: separate time/size/resp_time by weekday/weekend

from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import dateutil.parser
import argparse
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('--anonymize', metavar=("my_username","my_random_alias"), nargs=2) # needed for setting the same name for myself on all chats
args = parser.parse_args()

if args.file:
    try:
        data = open(args.file).readlines()
        lines = [l.strip() for l in data]
        lines = lines[1:] # it removes "Los mensajes y llamadas en este chat ahora estan protegidos con cifrado de extremo a extremo. Toca para mas informacion."
        msgs = []

        # in order to get both names on the chat:
        name1=''; name2=''
        for l in lines:
            pattern = re.compile('\d{1,2}\/\d{1,2}\/\d{2}')
            if not pattern.match(l):                                  # if line doesn't start with a '%d/%m/%y' datetime:
                continue                                              #     ignore line
            name = l.split(' - ')[1].split(':')[0]
            if not name1:
                name1 = name
            elif not name2:
                if name1!=name:
                    name2 = name
            else:
                break

        if args.anonymize:
            output = subprocess.check_output("shuf -n4 /usr/share/dict/spanish", shell=True).decode('utf8')
            words = output.split('\n')[:-1] # output is like 'paco\n\pupas\npaca\npipas\n'
            anonymous = {}
            anonymous[name1] = "{} {}".format(words[0].capitalize(),words[1].capitalize())
            anonymous[name2] = "{} {}".format(words[2].capitalize(),words[3].capitalize())
            anonymous[args.anonymize[0]] = args.anonymize[1]

        for l in lines:
            pattern = re.compile('\d{1,2}\/\d{1,2}\/\d{2}')
            if not pattern.match(l):                                  # if line doesn't start with a '%d/%m/%y' datetime:
                msgs[-1]['text'] = "{} {}".format(msgs[-1]['text'],l) #     put this line with the previous line
            else:
                str_tstamp = l.split(' - ')[0]
                sender = l.split(' - ')[1].split(':')[0]
                receiver = name2 if sender==name1 else name1
                text = l.split(': ')[1]
                if args.anonymize:
                    sender = anonymous[sender]
                    receiver = anonymous[receiver]
                resp_time = 0
                if len(msgs)>1:
                    if sender!=msgs[-1]['sender']:
                        prev_time = dateutil.parser.parse(msgs[-1]['tstamp'])
                        actual_time = datetime.strptime(str_tstamp, '%d/%m/%y %H:%M')
                        aux_resp_time = ( actual_time - prev_time).total_seconds()
                        if aux_resp_time < 60*60*8: # threshold: a message is a reply if it's sent <8h after last previous message
                            resp_time = aux_resp_time
                msgs.append( {
                    'tstamp': datetime.strptime(str_tstamp, '%d/%m/%y %H:%M').isoformat(),                # date of the message
                    'time': datetime.strptime("{} {}".format(                                             # time of the message, shifted to yesterday
                        (datetime.today()-timedelta(1)).strftime("%d/%m/%y"),str_tstamp.split(' ')[1]),   # (so messages can be grouped by hour)
                        '%d/%m/%y %H:%M').isoformat(),
                    'resp_time': resp_time,
                    'sender': sender,
                    'receiver': receiver,
                    'text': text,
                    'size': len(text) #TODO: in practice, it's encrypted, so.. maybe just normalizing size? as [very] small/medium/big, for example
                } )

        client = Elasticsearch()
        actions1 = []; actions2 = []
        if args.anonymize:
            index_msgs = 'msgs_anon'; index_msgs_24h = 'msgs_24h_anon'
        else:
            index_msgs = 'msgs'; index_msgs_24h = 'msgs_24h'

        for m in msgs:
            actions1.append( {
                "_index": index_msgs,
                "_source": {
                    "@timestamp": m['tstamp'],
                    'resp_time': m['resp_time'],
                    "sender": m['sender'],
                    "receiver": m['receiver'],
                    "text": m['text'],
                    "size": m['size']
                }
            } )
            actions2.append( { "_index": index_msgs_24h,
                "_source": {
                    "@time": m['time'], # different datetime field. this will be used to show just 24h
                    'resp_time': m['resp_time'],
                    "sender": m['sender'],
                    "receiver": m['receiver'],
                    "text": m['text'],
                    "size": m['size']
                }
            } )
        
        helpers.bulk(client,actions1)
        helpers.bulk(client,actions2)
        print("{} docs inserted on the elasticsearch index '{}'".format(len(actions1), index_msgs))
        print("{} docs inserted on the elasticsearch index '{}'".format(len(actions2), index_msgs_24h))

    except FileNotFoundError as e:
        print(e)
