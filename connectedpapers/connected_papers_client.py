import asyncio
import dataclasses
import sys
import typing
from enum import Enum
from typing import Any, AsyncIterator, List, Optional

import aiohttp
import dacite
import nest_asyncio  # type: ignore

from .consts import ACCESS_TOKEN, CONNECTED_PAPERS_REST_API
from .graph import Graph, PaperID

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


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
    graph_json: Optional[Graph] = None
    progress: Optional[float] = None
    remaining_requests: Optional[int] = None


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
SLEEP_TIME_AFTER_ERROR = 5.0


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
        nest_asyncio.apply()
        retry_counter = 3
        while retry_counter > 0:
            try:
                async with aiohttp.ClientSession() as session:
                    newest_graph: Optional[Any] = None
                    while True:
                        async with session.get(
                            f"{self.server_addr}/papers-api/graph/{int(fresh_only)}/{paper_id}",
                            headers={"X-Api-Key": self.access_token},
                        ) as resp:
                            if resp.status != 200:
                                raise RuntimeError(f"Bad response: {resp.status}")
                            data = await resp.json()
                            if data["status"] not in GraphResponseStatuses.__dict__:
                                data["status"] = GraphResponseStatuses.ERROR.value
                            fresh_only = True
                            response = dacite.from_dict(
                                data_class=GraphResponse,
                                data=data,
                                config=dacite.Config(
                                    type_hooks={
                                        GraphResponseStatuses: GraphResponseStatuses
                                    }
                                ),
                            )
                            if response.graph_json is not None:
                                newest_graph = response.graph_json
                            if (
                                response.status in end_response_statuses
                                or not loop_until_fresh
                            ):
                                yield response
                                return
                            response.graph_json = newest_graph
                            yield response
                            await asyncio.sleep(SLEEP_TIME_BETWEEN_CHECKS)
            except Exception as e:
                retry_counter -= 1
                if retry_counter == 0:
                    raise e
                await asyncio.sleep(SLEEP_TIME_AFTER_ERROR)

    async def get_graph_async(
        self, paper_id: str, fresh_only: bool = True
    ) -> GraphResponse:
        nest_asyncio.apply()
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

    async def get_remaining_usages_async(self) -> int:
        nest_asyncio.apply()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.server_addr}/papers-api/remaining-usages",
                headers={"X-Api-Key": self.access_token},
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Bad response: {resp.status}")
                data = await resp.json()
                return typing.cast(int, data["remaining_uses"])

    def get_remaining_usages_sync(self) -> int:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_remaining_usages_async())
        finally:
            loop.close()

    async def get_free_access_papers_async(self) -> List[PaperID]:
        nest_asyncio.apply()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.server_addr}/papers-api/free-access-papers",
                headers={"X-Api-Key": self.access_token},
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Bad response: {resp.status}")
                data = await resp.json()
                return typing.cast(List[PaperID], data["papers"])

    def get_free_access_papers_sync(self) -> List[PaperID]:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_free_access_papers_async())
        finally:
            loop.close()
