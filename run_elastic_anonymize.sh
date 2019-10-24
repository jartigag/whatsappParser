curl -s -XDELETE localhost:9200/msgs_24h_anon; curl -s -XDELETE localhost:9200/msgs_anon; echo

for f in chats/*; do sed -i 's/\xe2\x80\x8e//' "$f"; sed -i 's/\xe2\x80\x8d//' "$f"; eval `python3 load_data.py --anonymize --output elastic "$f"`; done
#                    ^^^^^ remove <U+200E>           ^^^^^ remove <U+200D>           ^^^^^ because .py prints ANON["user"]="alias"
#WIP: keep every name<->alias across the chats

curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs_24h_anon", "alias": "mensajes_anon"}}]}';
curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs_anon", "alias": "mensajes_anon"}}]}'; echo
