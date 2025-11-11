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
    OVERLOADED = "OVERLOADED"


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
        retry_on_overload: bool = True,
        verbose: bool = False,
    ) -> None:
        self.access_token = access_token
        self.server_addr = server_addr
        self.nested_asyncio: bool = True
        self.retry_on_overload = retry_on_overload
        self.verbose = verbose

    def nest_asyncio(self) -> None:
        if self.nested_asyncio:
            nest_asyncio.apply()

    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            from datetime import datetime

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    async def get_graph_async_iterator(
        self, paper_id: str, fresh_only: bool = False, wait_until_complete: bool = True
    ) -> AsyncIterator[GraphResponse]:
        """
        Get graph as an async iterator, yielding status updates.

        Args:
            paper_id: The paper ID to get the graph for
            fresh_only: If True, force a fresh graph rebuild (ignore cached graphs)
            wait_until_complete: If True, wait until a terminal status is reached
                                (FRESH_GRAPH, OLD_GRAPH, or error). If False, return
                                immediately with current status.

        Yields:
            GraphResponse objects with status updates (QUEUED, IN_PROGRESS, FRESH_GRAPH, etc.)
        """
        self.nest_asyncio()
        self._log(f"Requesting graph for paper: {paper_id}")
        retry_counter = 3
        overload_retry_delays = [5, 10, 20, 40]  # Exponential backoff delays in seconds
        overload_retry_index = 0

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
                            response = dacite.from_dict(
                                data_class=GraphResponse,
                                data=data,
                                config=dacite.Config(
                                    type_hooks={
                                        GraphResponseStatuses: GraphResponseStatuses
                                    }
                                ),
                            )

                            # Log status based on response type
                            if response.status == GraphResponseStatuses.IN_PROGRESS:
                                progress_pct = (
                                    response.progress
                                    if response.progress is not None
                                    else 0
                                )
                                self._log(
                                    f"Status: IN_PROGRESS - Building graph: {progress_pct:.0f}% complete"
                                )
                            elif response.status == GraphResponseStatuses.QUEUED:
                                self._log(
                                    "Status: QUEUED - Graph build queued, waiting..."
                                )
                            elif response.status == GraphResponseStatuses.OLD_GRAPH:
                                self._log(
                                    "Status: OLD_GRAPH - Using cached graph, requesting fresh build..."
                                )
                            elif response.status == GraphResponseStatuses.FRESH_GRAPH:
                                self._log("Status: FRESH_GRAPH - Graph ready")
                            elif response.status in end_response_statuses:
                                self._log(
                                    f"Status: {response.status.value} - Request failed"
                                )

                            # Handle OVERLOADED status with exponential backoff
                            if response.status == GraphResponseStatuses.OVERLOADED:
                                if (
                                    self.retry_on_overload
                                    and overload_retry_index
                                    < len(overload_retry_delays)
                                ):
                                    delay = overload_retry_delays[overload_retry_index]
                                    attempt_num = overload_retry_index + 1
                                    self._log(
                                        f"Status: OVERLOADED - Server busy, retrying in {delay}s (attempt {attempt_num}/4)"
                                    )
                                    overload_retry_index += 1
                                    await asyncio.sleep(delay)
                                    continue  # Retry the request
                                else:
                                    # Return OVERLOADED response if retries disabled or exhausted
                                    self._log(
                                        "Status: OVERLOADED - Max retries exhausted"
                                    )
                                    yield response
                                    return

                            # Reset overload retry counter on successful non-OVERLOADED response
                            overload_retry_index = 0

                            if response.graph_json is not None:
                                newest_graph = response.graph_json

                            # If fresh_only was originally False and we got OLD_GRAPH, that's what was requested
                            if (
                                response.status == GraphResponseStatuses.OLD_GRAPH
                                and not fresh_only
                            ):
                                yield response
                                return

                            if (
                                response.status in end_response_statuses
                                or not wait_until_complete
                            ):
                                yield response
                                return

                            # If we got OLD_GRAPH and wait_until_complete=True, request fresh on next iteration
                            if (
                                response.status == GraphResponseStatuses.OLD_GRAPH
                                and wait_until_complete
                            ):
                                fresh_only = True

                            response.graph_json = newest_graph
                            yield response
                            await asyncio.sleep(SLEEP_TIME_BETWEEN_CHECKS)
            except Exception as e:
                retry_counter -= 1
                attempt_num = 4 - retry_counter
                error_type = type(e).__name__
                if retry_counter == 0:
                    self._log(
                        f"Error: {error_type} - Max retries exhausted, raising exception"
                    )
                    raise e
                self._log(
                    f"Error: {error_type} - Retrying in {SLEEP_TIME_AFTER_ERROR:.0f}s (attempt {attempt_num}/3)"
                )
                await asyncio.sleep(SLEEP_TIME_AFTER_ERROR)

    async def get_graph_async(
        self, paper_id: str, fresh_only: bool = True
    ) -> GraphResponse:
        self.nest_asyncio()
        generator = self.get_graph_async_iterator(
            paper_id, fresh_only=fresh_only, wait_until_complete=True
        )
        result = GraphResponse(
            status=GraphResponseStatuses.ERROR, graph_json=None, progress=None
        )
        async for response in generator:
            result = response
        return result

    def get_graph_sync(self, paper_id: str, fresh_only: bool = True) -> GraphResponse:
        self.nest_asyncio()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_graph_async(paper_id, fresh_only))
        finally:
            loop.close()

    async def get_remaining_usages_async(self) -> int:
        self.nest_asyncio()
        self._log("Fetching remaining API usage...")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.server_addr}/papers-api/remaining-usages",
                headers={"X-Api-Key": self.access_token},
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Bad response: {resp.status}")
                data = await resp.json()
                remaining = typing.cast(int, data["remaining_uses"])
                self._log(f"Remaining requests: {remaining}")
                return remaining

    def get_remaining_usages_sync(self) -> int:
        self.nest_asyncio()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_remaining_usages_async())
        finally:
            loop.close()

    async def get_free_access_papers_async(self) -> List[PaperID]:
        self.nest_asyncio()
        self._log("Fetching free access papers...")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.server_addr}/papers-api/free-access-papers",
                headers={"X-Api-Key": self.access_token},
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Bad response: {resp.status}")
                data = await resp.json()
                papers = typing.cast(List[PaperID], data["papers"])
                self._log(f"Found {len(papers)} free access papers")
                return papers

    def get_free_access_papers_sync(self) -> List[PaperID]:
        self.nest_asyncio()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_free_access_papers_async())
        finally:
            loop.close()
