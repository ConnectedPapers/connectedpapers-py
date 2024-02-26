import asyncio

from connectedpapers import ConnectedPapersClient
from connectedpapers.connected_papers_client import GraphResponse, GraphResponseStatuses
from connectedpapers.consts import TEST_TOKEN
from tests.test_connected_papers_api import TEST_FAKE_PAPER_ID


async def wrapper_for_old_graph(no_nest: bool = False) -> GraphResponse:
    connected_papers_api = ConnectedPapersClient(access_token=TEST_TOKEN)
    if no_nest:
        connected_papers_api.nested_asyncio = False
    old_graph = connected_papers_api.get_graph_sync(
        TEST_FAKE_PAPER_ID, fresh_only=False
    )
    return old_graph


def sync_wrapper_2(no_nest: bool = False) -> GraphResponse:
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(wrapper_for_old_graph(no_nest))


async def async_wrapper_2(no_nest: bool = False) -> GraphResponse:
    return sync_wrapper_2(no_nest)


def test_nested_asyncio() -> None:
    loop = asyncio.new_event_loop()
    result: GraphResponse = loop.run_until_complete(async_wrapper_2())
    assert result.status == GraphResponseStatuses.OLD_GRAPH
