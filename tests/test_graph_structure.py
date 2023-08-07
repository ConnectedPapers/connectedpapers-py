import asyncio
import os

import pytest

from connectedpapers import ConnectedPapersClient

DEEPFRUITS_PAPER_ID = "9397e7acd062245d37350f5c05faf56e9cfae0d6"


def test_graph_structure() -> None:
    connected_papers_api = ConnectedPapersClient()
    deepfruits_graph = connected_papers_api.get_graph_sync(
        DEEPFRUITS_PAPER_ID, fresh_only=True
    )
    assert deepfruits_graph.graph_json.start_id == DEEPFRUITS_PAPER_ID
    assert len(deepfruits_graph.graph_json.nodes) > 10
    assert len(deepfruits_graph.graph_json.edges) > 100


PAPER_IDS_LIST = [
    "0d44970499a233c3be99995f615a91980becf3d4",
    "0b4c513b66754d5e7c700508629e2d28b1061609",
    "ddbdf0af38c36a4c6f67455266e71187bbe687dc",
    "0f366de3ea595932dad06389f6e61fe0dd8cbe74",
    "365b31515028f2c7444d5b5afd865d242b229bd2",
    "2292d90d224e1fdaa2151027f700b4499fecde69",
    "eaf9a6e54ef9e078985447b9c5fa56468795bb90",
    "3bb4c3127c77ffb06a81cfe09862716a0828114c",
    "98882d201890680e156fef2b111630f401168092",
    "5ea70d18d71a5247f745930045345d246aed4695",
    "b81b1a6af54f6c44005ac9eed1e31df1a09dad43",
    "873fd583c4daf1ad3c8910e825d8003d805a1c60",
    "0625832ae5d3cb9345b711e3c0ebb14b10b86a00",
]


@pytest.mark.asyncio
async def test_get_many_papers() -> None:
    if "TEST_REAL_PAPERS" not in os.environ:
        return
    promises = []
    connected_papers_api = ConnectedPapersClient()
    for paper_id in PAPER_IDS_LIST:
        promises.append(connected_papers_api.get_graph_async(paper_id))
    results = await asyncio.gather(*promises)
    x = 1
