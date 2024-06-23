import datetime
import os
import time

from connectedpapers import ConnectedPapersClient
from connectedpapers.connected_papers_client import GraphResponseStatuses
from connectedpapers.consts import TEST_TOKEN

TEST_FAKE_PAPER_ID = "1234567890123456789012345678901234567890"


def test_old_graph() -> None:
    connected_papers_api = ConnectedPapersClient(access_token=TEST_TOKEN)
    old_graph = connected_papers_api.get_graph_sync(
        TEST_FAKE_PAPER_ID, fresh_only=False
    )
    print("old_graph.status", old_graph.status)
    assert old_graph.status == GraphResponseStatuses.OLD_GRAPH
    assert old_graph.graph_json is not None
    assert old_graph.progress is None


def test_new_graph() -> None:
    if "ENABLE_SLOW_TEST" not in os.environ:
        return
    connected_papers_api = ConnectedPapersClient()
    current_time = datetime.datetime.utcnow()
    current_second_in_minute_mod20 = current_time.second % 20
    time_to_sleep_to_1_mod_20 = 20 - current_second_in_minute_mod20 + 1
    time.sleep(time_to_sleep_to_1_mod_20)
    start_time = datetime.datetime.utcnow()
    connected_papers_api.get_graph_sync(TEST_FAKE_PAPER_ID)
    end_time = datetime.datetime.utcnow()
    # The fake ID causes a "build" to be simulated in the rest API, status is cyclic every 20 seconds
    assert (end_time - start_time).seconds > 12
    assert (end_time - start_time).seconds < 20
