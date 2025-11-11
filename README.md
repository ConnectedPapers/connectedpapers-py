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
    OVERLOADED = "OVERLOADED"


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
        self, paper_id: str, fresh_only: bool = False, wait_until_complete: bool = True
    ) -> AsyncIterator[GraphResponse]:
        # ...
```

### Understanding the Parameters

**`fresh_only` (bool, default=False)**: Controls API behavior
- `False`: Accept cached/old graph if available
- `True`: Force a fresh graph rebuild, ignore cached graphs

**`wait_until_complete` (bool, default=True)**: Controls client waiting behavior
- `True`: Wait until a terminal status is reached (FRESH_GRAPH, OLD_GRAPH, or error)
- `False`: Return immediately with current status (QUEUED, IN_PROGRESS, etc.)

### Common Usage Patterns

**Accept cached graph or wait for new one:**
```python
# fresh_only=False, wait_until_complete=True (default)
async for response in client.get_graph_async_iterator(paper_id):
    if response.status == GraphResponseStatuses.OLD_GRAPH:
        # Got cached graph immediately
    elif response.status == GraphResponseStatuses.FRESH_GRAPH:
        # No cache existed, waited for new graph
```

**Force fresh rebuild and wait:**
```python
# fresh_only=True, wait_until_complete=True
async for response in client.get_graph_async_iterator(paper_id, fresh_only=True):
    # Waits through QUEUED → IN_PROGRESS → FRESH_GRAPH
```

**Quick status check without waiting:**
```python
# wait_until_complete=False
async for response in client.get_graph_async_iterator(paper_id, wait_until_complete=False):
    # Returns immediately with current status (might be QUEUED or IN_PROGRESS)
    break  # Get first response only
```

The graph_json field will contain the graph corresponding
to each of these responses, and will remain non-None
as long as there is any version of the graph available.

# Rate Limiting and Overload Handling

## OVERLOADED Status
As of the 2025-11 API update, the API may return an `OVERLOADED` status when:
- Your API key exceeds the rate limit (default: 5 builds per minute)
- The system is temporarily overloaded

Previously, throttling returned HTTP 500 errors. Now it returns HTTP 200 with `status: "OVERLOADED"`.

## Automatic Retry with Exponential Backoff
By default, the client automatically retries when the server returns `OVERLOADED` status with exponential backoff delays of 5, 10, 20, and 40 seconds.

```python
from connectedpapers import ConnectedPapersClient

# Default behavior: automatic retries enabled
client = ConnectedPapersClient(access_token="YOUR_API_KEY")

# The client will automatically retry with exponential backoff: 5s, 10s, 20s, 40s
graph = client.get_graph_sync("YOUR_PAPER_ID")
```

When `retry_on_overload=True` (default):
- The client will automatically retry up to 4 times with delays of 5, 10, 20, and 40 seconds
- If all retries are exhausted, it will return the `OVERLOADED` status

To disable automatic retries:
```python
# Disable automatic retries
client = ConnectedPapersClient(
    access_token="YOUR_API_KEY",
    retry_on_overload=False
)
```

When `retry_on_overload=False`:
- The client will immediately return the `OVERLOADED` status without retrying
- You can handle this status in your code and implement your own retry logic

## Avoiding Rate Limits
To minimize rate limit hits, you can check which papers are available for free re-access:

```python
# Papers accessed within the last 31 days don't count toward rate limit
free_papers = client.get_free_access_papers_sync()
print(f"Free access papers: {free_papers}")
```

Papers accessed within 31 days can be re-accessed without counting toward your rate limit.

# Verbose Logging

## Enable Real-Time Status Updates
By default, the client operates silently. You can enable verbose logging to see real-time progress updates during API operations:

```python
from connectedpapers import ConnectedPapersClient

# Enable verbose logging
client = ConnectedPapersClient(
    access_token="YOUR_API_KEY",
    verbose=True  # Default is False
)

# Now you'll see timestamped status updates in the console
graph = client.get_graph_sync("YOUR_PAPER_ID")
```

### Example Output

With `verbose=True`, you'll see timestamped updates like:

```
[14:23:01] Requesting graph for paper: 9397e7acd062245d37350f5c05faf56e9cfae0d6
[14:23:02] Status: QUEUED - Graph build queued, waiting...
[14:23:03] Status: IN_PROGRESS - Building graph: 15% complete
[14:23:04] Status: IN_PROGRESS - Building graph: 42% complete
[14:23:05] Status: IN_PROGRESS - Building graph: 78% complete
[14:23:06] Status: IN_PROGRESS - Building graph: 95% complete
[14:23:07] Status: FRESH_GRAPH - Graph ready
```

When rate limiting occurs:
```
[14:25:01] Requesting graph for paper: abc123
[14:25:02] Status: OVERLOADED - Server busy, retrying in 5s (attempt 1/4)
[14:25:07] Status: OVERLOADED - Server busy, retrying in 10s (attempt 2/4)
[14:25:17] Status: IN_PROGRESS - Building graph: 23% complete
```

### What Gets Logged

Verbose mode provides visibility into:
- **Graph requests** - Paper ID being requested
- **Build progress** - Real-time percentage updates during graph generation
- **Queue status** - When your request is queued
- **Rate limiting** - Retry attempts with exponential backoff delays
- **Errors** - Connection issues and retry attempts
- **API usage** - Remaining request count
- **Free access papers** - Count of papers available for free re-access

This is especially useful for:
- Long-running graph builds (can take up to 60 seconds)
- Monitoring retry behavior during high load
- Debugging API integration issues
- Understanding API quota usage

### Testing Verbose Mode

Use the included CLI tool to test verbose logging:

```bash
# Default: Wait for complete graph (through QUEUED, IN_PROGRESS, OVERLOADED states)
python usage_samples/test_verbose.py <PAPER_ID> --api-key YOUR_API_KEY

# Accept cached/old graph if available (return immediately)
python usage_samples/test_verbose.py <PAPER_ID> --api-key YOUR_API_KEY --accept-old

# Quick status check without waiting (return immediately)
python usage_samples/test_verbose.py <PAPER_ID> --api-key YOUR_API_KEY --no-wait

# Display all papers in the graph after completion
python usage_samples/test_verbose.py <PAPER_ID> --api-key YOUR_API_KEY --show-papers
```

**Behavior modes:**
- **Default**: Always waits for a complete graph (FRESH_GRAPH status)
- **--accept-old**: Returns cached graph immediately if available
- **--no-wait**: Returns current status immediately without waiting

### Testing Basic API Calls

For a simple demonstration of the core API functionality, use the `get_key_details.py` script:

```bash
# Basic usage (uses TEST_TOKEN by default or CONNECTED_PAPERS_API_KEY env variable)
python usage_samples/get_key_details.py
```

This script demonstrates the three main API calls:
- **`get_remaining_usages_sync()`** - Check your API quota
- **`get_free_access_papers_sync()`** - List papers available for free re-access
- **`get_graph_sync()`** - Fetch a paper's graph

The script validates the API integration by fetching the test paper (DEEPFRUITS) and asserting the graph structure is correct. It's useful for:
- Verifying your API key is working
- Quick testing of API connectivity
- Understanding the basic API workflow
