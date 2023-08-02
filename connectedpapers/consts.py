import os

# CONNECTED_PAPERS_REST_API = os.environ.get(
#     "CONNECTED_PAPERS_REST_API", "https://rest.connectedpapers.com"
# )
CONNECTED_PAPERS_REST_API = os.environ.get(
    "CONNECTED_PAPERS_REST_API", "http://localhost:8002"
)
ACCESS_TOKEN = os.environ.get("CONNECTED_PAPERS_KEY", "TEST_TOKEN")
