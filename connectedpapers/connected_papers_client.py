import asyncio
import dataclasses
from enum import Enum
from typing import Any, AsyncIterator, Optional

import aiohttp

from .consts import ACCESS_TOKEN, CONNECTED_PAPERS_REST_API


class GraphResponseStatuses(Enum):
    """Statuses for API"""

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
    """A response for the external graphs API"""

    status: GraphResponseStatuses
    graph_json: Optional[Any] = None
    progress: Optional[float] = None


end_response_statuses = {
    GraphResponseStatuses.BAD_ID,
    GraphResponseStatuses.ERROR,
    GraphResponseStatuses.NOT_IN_DB,
    GraphResponseStatuses.FRESH_GRAPH,
    GraphResponseStatuses.BAD_TOKEN,
    GraphResponseStatuses.BAD_REQUEST,
    GraphResponseStatuses.OUT_OF_REQUESTS,
}

SLEEP_TIME_BETWEEN_CHECKS = 1.0


class ConnectedPapersClient:
    def __init__(
        self,
        access_token: str = ACCESS_TOKEN,
        server_addr: str = CONNECTED_PAPERS_REST_API,
    ) -> None:
        self.access_token = access_token
        self.server_addr = server_addr

    async def get_graph_async_iterator(
        self, paper_id: str, fresh_only: bool = False, loop_until_fresh: bool = True
    ) -> AsyncIterator[GraphResponse]:
        async with aiohttp.ClientSession() as session:
            newest_graph: Optional[Any] = None
            while True:
                async with session.get(
                    f"{self.server_addr}/papers-api/{int(fresh_only)}/{paper_id}",
                    headers={"X-Api-Key": self.access_token},
                ) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Bad response: {resp.status}")
                    data = await resp.json()
                    fresh_only = True
                    response = GraphResponse(**data)
                    if response.status in GraphResponseStatuses.__dict__:  # type: ignore
                        response.status = GraphResponseStatuses[response.status]  # type: ignore
                    else:
                        response.status = GraphResponseStatuses.ERROR
                    if response.graph_json is not None:
                        newest_graph = response.graph_json
                    if response.status in end_response_statuses or not loop_until_fresh:
                        yield response
                        return
                    response.graph_json = newest_graph
                    yield response
                    await asyncio.sleep(SLEEP_TIME_BETWEEN_CHECKS)

    async def get_graph_async(
        self, paper_id: str, fresh_only: bool = True
    ) -> GraphResponse:
        generator = self.get_graph_async_iterator(
            paper_id, fresh_only=fresh_only, loop_until_fresh=fresh_only
        )
        result = GraphResponse(
            status=GraphResponseStatuses.ERROR, graph_json=None, progress=None
        )
        async for response in generator:
            result = response
        return result

    def get_graph_sync(self, paper_id: str, fresh_only: bool = True) -> GraphResponse:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_graph_async(paper_id, fresh_only))
        finally:
            loop.close()
