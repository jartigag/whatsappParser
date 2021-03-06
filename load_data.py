#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#author: jartigag
#date: 2019-10-25

from elasticsearch import Elasticsearch, helpers
import csv
from datetime import datetime, timedelta
import dateutil.parser
import argparse
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('-g','--group', action='store_true')
parser.add_argument('-a','--anonymize', action='store_true')
parser.add_argument('-o','--output', choices=['csv','elastic'], default='csv')
args = parser.parse_args()
anonymous = {}

def dump_to_elastic(msgs):
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
                "content": m['content'],
                "size": m['size']
            }
        } )
        actions2.append( { "_index": index_msgs_24h,
            "_source": {
                "@time": m['daytime'], # different datetime field. this will be used to show just 24h
                'resp_time': m['resp_time'],
                "sender": m['sender'],
                "receiver": m['receiver'],
                "content": m['content'],
                "size": m['size']
            }
        } )

    helpers.bulk(client,actions1)
    helpers.bulk(client,actions2)
    print("{} docs inserted on the elasticsearch index '{}'".format(len(actions1), index_msgs),file=sys.stderr)
    print("{} docs inserted on the elasticsearch index '{}'".format(len(actions2), index_msgs_24h),file=sys.stderr)

def dump_to_csv(msgs):
    with open("output.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=list(msgs[0].keys())) #TODO: order keys (tstamp,sender,content..)
        writer.writeheader()
        for row in msgs:
            writer.writerow(row)

def anonymize(name):
    if name not in anonymous:
        output = subprocess.check_output("shuf -n2 /usr/share/dict/spanish", shell=True).decode('utf8')
        words = output.split('\n')[:-1] # output is like 'paco\n\pupas\n'
        anonymous[name] = "{} {}".format(words[0].capitalize(),words[1].capitalize())
        print("ANON[\"{}\"]=\"{}\"".format(name,anonymous[name]))
    return anonymous[name]

if args.file:
    try:
        data = open(args.file).readlines()
        lines = [l.strip() for l in data]
        if "Los mensajes y llamadas en este chat ahora están protegidos con cifrado de extremo a extremo. Toca para más información." in lines[0]: lines = lines[1:]
        msgs = []

        if args.anonymize:
            print("declare -A ANON")

        if not args.group:
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

        for l in lines:
            try:
                pattern = re.compile('\d{1,2}\/\d{1,2}\/\d{2}')
                if not pattern.match(l):                                  # if line doesn't start with a '%d/%m/%y' datetime:
                    msgs[-1]['content'] = "{} {}".format(msgs[-1]['content'],l) #     put this line with the previous line
                else:
                    splitter = ':'
                    for c in ["cambió el asunto","Cambiaste el asunto","eliminó el asunto","Eliminaste el asunto"]:
                        if c in l:
                            content = "[CAMBIO ASUNTO]"
                            splitter = c
                    for c in ["cambió el ícono","Cambiaste el ícono","eliminó el ícono","Eliminaste el ícono"]:
                        if c in l:
                            content = "[CAMBIO ÍCONO]"
                            splitter = c
                    for c in ["cambió la descripción","Cambiaste la descripción","eliminó la descripción","Eliminaste la descripción", "borró la descripción", "Borraste la descripción"]:
                        if c in l:
                            content = "[CAMBIO DESCRIPCIÓN]"
                            splitter = c
                    for c in ["añadió a","Añadiste a"]:
                        if c in l:
                            content = "[AÑADIDO MIEMBRO]"
                            splitter = c
                    for c in ["salió del","Saliste del"]:
                        if c in l:
                            content = "[SALIDA MIEMBRO]"
                            splitter = c
                    for c in ["eliminó a","Eliminaste a"]:
                        if c in l:
                            content = "[ELIMINADO MIEMBRO]"
                            splitter = c
                    for c in ["Ahora eres admin","Ya no eres admin"]:
                        if c in l:
                            content = "[CAMBIO ADMIN]"
                            splitter = c
                    text = ''
                    if splitter==":" and l[-1]!=":":
                        text = l.split(': ')[1]
                        if text[-18:]==" (archivo adjunto)":
                            if text[-21:-18]=="jpg":
                                content = "[IMAGEN]"
                            elif text[-21:-18]=="mp4":
                                    content = "[VÍDEO]"
                            elif text[-21:-18]=="pdf":
                                    content = "[ARCHIVO]"
                            elif text[-22:-18]=="opus":
                                    content = "[AUDIO]"
                            elif text[-22:-18]=="webp":
                                    content = "[STICKER]"
                            if args.anonymize:
                                content = "".join(["x" for i in range(len(text))])
                        else:
                            content = text
                    sender = l.split(' - ')[1].split(splitter)[0]
                    str_tstamp = l.split(' - ')[0]
                    if args.group:
                        receiver = 'grupo'
                    else:
                        receiver = name2 if sender==name1 else name1
                    if args.anonymize:
                        sender = anonymize(sender)
                        receiver = anonymize(receiver)
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
                        'daytime': datetime.strptime("{} {}".format(                                             # time of the message, shifted to yesterday
                            (datetime.today()-timedelta(1)).strftime("%d/%m/%y"),str_tstamp.split(' ')[1]),   # (so messages can be grouped by hour)
                            '%d/%m/%y %H:%M').isoformat(),
                        'resp_time': resp_time,
                        'sender': sender,
                        'receiver': receiver,
                        'content': content,
                        'size': len(content)
                    } )
            except Exception as e:
                print("error: {}".format(e),file=sys.stderr)
                print(l,file=sys.stderr)
        if args.output=="elastic":
            dump_to_elastic(msgs)
        elif args.output=="csv":
            dump_to_csv(msgs)

    except FileNotFoundError as e:
        print(e,file=sys.stderr)
