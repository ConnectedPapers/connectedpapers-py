import pytest

from connectedpapers import ConnectedPapersClient
from connectedpapers.connected_papers_client import GraphResponseStatuses
from connectedpapers.consts import TEST_TOKEN

TEST_FAKE_PAPER_ID = "1234567890123456789012345678901234567890"
pytestmark = pytest.mark.integration


def test_old_graph() -> None:
    connected_papers_api = ConnectedPapersClient(access_token=TEST_TOKEN, verbose=True)
    old_graph = connected_papers_api.get_graph_sync(
        TEST_FAKE_PAPER_ID, fresh_only=False
    )
    print("old_graph.status", old_graph.status)
    assert old_graph.status == GraphResponseStatuses.OLD_GRAPH
    assert old_graph.graph_json is not None
    assert old_graph.progress is None
