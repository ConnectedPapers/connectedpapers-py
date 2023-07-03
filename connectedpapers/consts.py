import os

CONNECTED_PAPERS_REST_API = os.environ.get(
    "CONNECTED_PAPERS_REST_API", "https://rest.connectedpapers.com"
)
ACCESS_TOKEN = os.environ.get("CONNECTED_PAPERS_TOKEN", "TEST_TOKEN")
