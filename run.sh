curl -s -XDELETE localhost:9200/msgs_24h; curl -s -XDELETE localhost:9200/msgs; echo

for f in chats/*; do python3 load_data.py "$f"; done

curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs_24h", "alias": "mensajes"}}]}'; 
curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs", "alias": "mensajes"}}]}'; echo
