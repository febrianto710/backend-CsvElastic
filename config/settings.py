from elasticsearch import Elasticsearch
import yaml
from enum import Enum

base_path = '.'

def load_config_elk():
    with open(base_path + '/config/connection_config.yaml', 'r') as file:
        elk_config = yaml.safe_load(file)
    return elk_config
elk_config = load_config_elk()

es = Elasticsearch(
    [elk_config["elk"]["url"]],
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=30,  # Request timeout (seconds)
    max_retries=10,  # Number of retries for failed requests
    retry_on_timeout=True,  # Retry on timeout error
)

# Indices
DEST_INDEX = elk_config["elk"]["index_destination"]
DATABASE_URL = elk_config["db"]["url"]


SCROLL_TIME = "2m"
BATCH_SIZE = 10000

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

class IndexType(Enum):
    EMPLOYEE = "employee"
    WEB_PORTAL = "web portal"
    QUOTA_DUKCAPIL = "quota dukcapil"

API_VERSION = "v1"