import asyncio

from connectedpapers import ConnectedPapersClient
from connectedpapers.connected_papers_client import GraphResponseStatuses

TEST_FAKE_PAPER_ID = "1234567890123456789012345678901234567890"


def test_connected_papers_api():
    connected_papers_api = ConnectedPapersClient()
    old_graph = connected_papers_api.get_graph_sync(TEST_FAKE_PAPER_ID)
    assert old_graph.status == GraphResponseStatuses.OLD_GRAPH
    assert old_graph.graph_json is not None
    assert old_graph.progress is None
