# install elasticsearch 7.2.0 (2019-06-25)
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.2.0-amd64.deb
sudo dpkg -i elasticsearch-7.2.0-amd64.deb
# if you prefer to add their APT package repository, follow the steps on:
# https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html#deb-repo

# install grafana 6.2.5 (2019-06-25)
wget https://dl.grafana.com/oss/release/grafana_6.2.5_amd64.deb
sudo dpkg -i grafana_6.2.5_amd64.deb
# if you prefer to add their APT package repository, follow the steps on:
# https://grafana.com/docs/installation/debian/#apt-repository

sudo systemctl start elasticsearch
sudo grafana-cli plugins install neocat-cal-heatmap-panel
sudo systemctl start grafana-server
