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
remaining_uses_count = client.get_remaining_usages_sync()
print(f"Remaining uses count: {remaining_uses_count}")
free_access_papers = client.get_free_access_papers_sync()
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
   (You do not need to configure the server address, uses the correct one by default).
   Then you can use the client without parameters:
   ```python
    from connectedpapers import ConnectedPapersClient
   
    client = ConnectedPapersClient()
    ```
2. Send parameters to the client's constructur:
   ```python
   from connectedpapers import ConnectedPapersClient
   
   client = ConnectedPapersClient(access_token="YOUR_API_KEY", server_addr="https://api.connectedpapers.com")
   ```
# API
Most functions offer a synchronous and an asynchronous version.

## API structure
We have the following API calls available:
* Fetching a graph
* Getting the remaining usages count for your API key
* Getting the list of papers that are free to access

### Free re-access to papers
If you have fetched a paper, it remains free to access
for a month after the first access without counting 
towards your usages count.

## Synchronous API

```python
from connectedpapers import ConnectedPapersClient

client = ConnectedPapersClient()
client.get_graph_sync("YOUR_PAPER_ID")  # Fetch a graph for a single paper
client.get_remaining_usages_sync()  # Get the remaining usages count for your API key
client.get_free_access_papers_sync()  # Get the list of papers that are free to access
```

## Asynchronous API

```python
from connectedpapers import ConnectedPapersClient

client = ConnectedPapersClient()


async def usage_sample() -> None:
   await client.get_graph_async("YOUR_PAPER_ID")  # Fetch a graph for a single paper
   await client.get_remaining_usages_async()  # Get the remaining usages count for your API key
   await client.get_free_access_papers_async()  # Get the list of papers that are free to access

usage_sample()
```