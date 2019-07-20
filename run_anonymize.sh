curl -s -XDELETE localhost:9200/msgs_24h_anon; curl -s -XDELETE localhost:9200/msgs_anon; echo

alias1=$(shuf -n1 /usr/share/dict/spanish)
alias2=$(shuf -n1 /usr/share/dict/spanish)

for f in chats/*; do python3 load_data.py --anonymize "javi artiga" "${alias1^} ${alias2^}" "$f"; done

curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs_24h_anon", "alias": "mensajes_anon"}}]}'; 
curl -s -XPOST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d '{"actions": [{"add": {"index": "msgs_anon", "alias": "mensajes_anon"}}]}'; echo
