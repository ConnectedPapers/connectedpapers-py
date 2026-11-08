import os

DEFAULT_REST_API = "https://rest.prod.connectedpapers.com"
CONNECTED_PAPERS_REST_API = os.environ.get(
    "CONNECTED_PAPERS_REST_API", DEFAULT_REST_API
)

TEST_TOKEN = "TEST_TOKEN"
ACCESS_TOKEN = os.environ.get("CONNECTED_PAPERS_API_KEY", TEST_TOKEN)
