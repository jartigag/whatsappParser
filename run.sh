curl -s -XDELETE localhost:9200/msgs_24h; curl -s -XDELETE localhost:9200/msgs; echo

for f in chats/*; do sed -i 's/\xe2\x80\x8e//' $f; python3 load_data.py "$f"; done
#                    ^^^^^ remove <U+200E>

curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs_24h", "alias": "mensajes"}}]}'; 
curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs", "alias": "mensajes"}}]}'; echo
