# connectedpapers-py
The official python client for the connected papers API.

# Installation
```bash
pip install connectedpapers-py
```

# Usage
```python
from connectedpapers import ConnectedPapersClient

DEEPFRUITS_PAPER_ID = "9397e7acd062245d37350f5c05faf56e9cfae0d6"

client = ConnectedPapersClient()
remaining_uses_count = client.sync_get_remaining_usages()
print(f"Remaining uses count: {remaining_uses_count}")
free_access_papers = client.sync_get_free_access_papers()
print(f"Free access papers: {free_access_papers}")
graph = client.get_graph_sync(DEEPFRUITS_PAPER_ID)
assert graph.graph_json.start_id == DEEPFRUITS_PAPER_ID
```
See more on the [usage samples](https://github.com/ConnectedPapers/connectedpapers-py/tree/master/usage_samples) directory.

See graph structure at [graph.py](https://github.com/ConnectedPapers/connectedpapers-py/blob/master/connectedpapers/graph.py).

# Configuring server address and API key
There are multiple ways to configure the server address and API key:
1. Set the environment variables `CONNECTED_PAPERS_SERVER_ADDRESS` and `CONNECTED_PAPERS_API_KEY`:
    ```bash
   export CONNECTED_PAPERS_REST_API="https://api.connectedpapers.com"
   export CONNECTED_PAPERS_API_KEY="YOUR_API_KEY"
    ```
   (You do not need to configure the server address, uses the correct one by default)
2. Send parameters to the client's constructur:
   ```python
   from connectedpapers import ConnectedPapersClient
   
   client = ConnectedPapersClient(access_token="YOUR_API_KEY", server_addr="https://api.connectedpapers.com")
   ```
