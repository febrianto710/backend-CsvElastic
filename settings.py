import os
from elasticsearch import Elasticsearch
import yaml




base_path = '.'

def load_config_elk():
    with open(base_path + '/connection_config.yaml', 'r') as file:
        elk_config = yaml.safe_load(file)
    return elk_config

elk_config = load_config_elk()

# client = hvac.Client(
#     url=elk_config['vault']['url'],
#     token=elk_config['vault']['token'],
#     verify=False
# )

# elk_secret = client.secrets.kv.v2.read_secret_version(path='elasticsearch',mount_point='54086')

# es_nodes = [
#     elk_secret['data']['data']['elkhub_connstring']
# ]

# es = Elasticsearch(
#     es_nodes,
#     verify_certs=False,
#     ssl_show_warn=False,
#     request_timeout=30,         # Request timeout (seconds)
#     max_retries=10,     # Number of retries for failed requests
#     retry_on_timeout=True  # Retry on timeout error
#     )

es = Elasticsearch(
    [elk_config["elk_local"]["url"]],
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=30,  # Request timeout (seconds)
    max_retries=10,  # Number of retries for failed requests
    retry_on_timeout=True,  # Retry on timeout error
)

# Indices
SOURCE_INDEX = elk_config["elk_local"]["index_destination"]
DEST_INDEX = "test-csv-upload"

SOURCE_RECON_INDEX = "test-csv-upload"
DEST_RECON_INDEX = "test-csv-upload"

# Scroll settings
SCROLL_TIME = "2m"
BATCH_SIZE = 10000

# Scheduler settings
MAX_CONCURRENT_JOBS = 2
MAX_CONCURRENT_RECON_JOBS = 1
MAX_RETRIES = 3
RETRY_DELAY = 10
JOB_UNIT = "seconds"
JOB_INTERVAL = 5

