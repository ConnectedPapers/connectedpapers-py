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

# TEST_TOKEN allows access ONLY to the paper with the id DEEPFRUITS_PAPER_ID
client = ConnectedPapersClient(access_token="TEST_TOKEN")
remaining_uses_count = client.get_remaining_usages_sync()
print(f"Remaining uses count: {remaining_uses_count}")
free_access_papers = client.get_free_access_papers_sync()
print(f"Free access papers: {free_access_papers}")
graph = client.get_graph_sync(DEEPFRUITS_PAPER_ID)
assert graph.graph_json.start_id == DEEPFRUITS_PAPER_ID
```
See more on the [usage samples](https://github.com/ConnectedPapers/connectedpapers-py/tree/master/usage_samples) directory.

See graph structure at [graph.py](https://github.com/ConnectedPapers/connectedpapers-py/blob/master/connectedpapers/graph.py).

# Configuring the API key
There are multiple ways to configure the server address and API key:
1. Set the environment variable `CONNECTED_PAPERS_API_KEY`:
    ```bash
   export CONNECTED_PAPERS_API_KEY="YOUR_API_KEY"
    ```
   Then you can use the client without parameters:
   ```python
    from connectedpapers import ConnectedPapersClient
   
    client = ConnectedPapersClient()
    ```
2. Send parameters to the client's constructur:
   ```python
   from connectedpapers import ConnectedPapersClient
   
   client = ConnectedPapersClient(access_token="YOUR_API_KEY")
   ```

## Getting an access token
Contact us at `hello@connectedpapers.com` to get
an early-access access token.

Using the token `TEST_TOKEN` or not passing a token at all,
will allow you to access the graph of the paper with the id 
`9397e7acd062245d37350f5c05faf56e9cfae0d6` for testing purposes.

## Paper IDs
We use the ShaIDs from [Semantic Scholar](https://www.semanticscholar.org/) as paper IDs.
You can find the ShaID of a paper by searching for it on Semantic Scholar and copying the ID from the URL.

# API
Most functions offer a synchronous and an asynchronous version.

If a graph is already built, you can get it within a standard API call latency.
If it is outdated (older than 1 month), you can still get it using the `fresh_only=False` parameter.
If you wait for a rebuild (either `fresh_only=True` and graph older than 30 days, or no graph built for the paper)
a rebuild will be triggered; A graph build can take up to 1 minute, and usually around 10 seconds.

The graph structure is documented at [graph.py](https://github.com/ConnectedPapers/connectedpapers-py/blob/master/connectedpapers/graph.py).

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

client = ConnectedPapersClient(access_token="YOUR_API_KEY")
client.get_graph_sync("YOUR_PAPER_ID")  # Fetch a graph for a single paper
client.get_remaining_usages_sync()  # Get the remaining usages count for your API key
client.get_free_access_papers_sync()  # Get the list of papers that are free to access
```

## Asynchronous API

```python
from connectedpapers import ConnectedPapersClient

client = ConnectedPapersClient(access_token="YOUR_API_KEY")


async def usage_sample() -> None:
   await client.get_graph_async("YOUR_PAPER_ID")  # Fetch a graph for a single paper
   await client.get_remaining_usages_async()  # Get the remaining usages count for your API key
   await client.get_free_access_papers_async()  # Get the list of papers that are free to access

usage_sample()
```

## Async iterator API
The client offers support for Python's [asynchronous iterator](https://peps.python.org/pep-0525/) 
access to the API, allowing for real-time monitoring of
the progress of graph builds and retrieval of both current
and rebuilt papers.

The method `get_graph_async_iterator` returns an asynchronous
iterator, generating values of the `GraphResponse`
type. Here's what the `GraphResponse` and related
`GraphResponseStatuses` looks like in Python:
```python
class GraphResponseStatuses(Enum):
    BAD_ID = "BAD_ID"
    ERROR = "ERROR"
    NOT_IN_DB = "NOT_IN_DB"
    OLD_GRAPH = "OLD_GRAPH"
    FRESH_GRAPH = "FRESH_GRAPH"
    IN_PROGRESS = "IN_PROGRESS"
    QUEUED = "QUEUED"
    BAD_TOKEN = "BAD_TOKEN"
    BAD_REQUEST = "BAD_REQUEST"
    OUT_OF_REQUESTS = "OUT_OF_REQUESTS"


@dataclasses.dataclass
class GraphResponse:
    status: GraphResponseStatuses
    graph_json: Optional[Graph] = None
    progress: Optional[float] = None
    remaining_requests: Optional[int] = None
```
Once the status falls into one of the terminal states (BAD_ID, ERROR, NOT_IN_DB, BAD_TOKEN, BAD_REQUEST, OUT_OF_REQUESTS), the iterator will cease to yield further values.

Here's the signature for invoking this method:

```python
class ConnectedPapersClient:
    # ...
    async def get_graph_async_iterator(
        self, paper_id: str, fresh_only: bool = False, loop_until_fresh: bool = True
    ) -> AsyncIterator[GraphResponse]:
        # ...
```
Call this method with fresh_only=False and loop_until_fresh=True
to request the existing graph and continue waiting
for a rebuild if necessary.

The initial response will contain the status GraphResponseStatuses.OLD_GRAPH,
then transition through GraphResponseStatuses.QUEUED and
GraphResponseStatuses.IN_PROGRESS, with the progress
field reflecting the percentage of the graph build
completed. Upon completion of the rebuild,
the status will change to GraphResponseStatuses.FRESH_GRAPH,
and the iteration will end.

The graph_json field will contain the graph corresponding
to each of these responses, and will remain a non-None
as long as there is any version of the graph available.
