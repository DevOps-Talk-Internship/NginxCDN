## NginxCDN By Iman and Satyar

## Getting Started

#### Create virtual environment
python3 -m venv venv
#### Activate virtual environment (Linux)
source ./venv/bin/activate
<!-- 
#### Install needed ubuntu deps
sudo apt install -y libmariadb-dev -->

<!-- #### Install Pip requirements
pip install -r requirements.txt -->

#### Install Pip requirements
pip install flask

#### Running the docker-compose
##### Run these before running the docker-compose
```bash 
mkdir -p ./data/grafana_data ./data/prometheus_data && sudo chmod -R 777 ./data/grafana_data ./data/prometheus_data
```

```bash
sudo docker-compose up -d
sudo docker-compose down
```
