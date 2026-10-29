import asyncio
from typing import Any

import pytest
from dacite import MissingValueError

from connectedpapers.connected_papers_client import GraphResponseStatuses as Status
from connectedpapers.graph import CommonAuthor, Graph
from tests.conftest import LocalAPI


def run_async(coroutine: Any) -> Any:
    # The SDK patches asyncio.run via nest_asyncio. Own the loop explicitly so
    # sync calls in earlier tests cannot leave this call using a closed loop.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()
        asyncio.set_event_loop(None)


def graph_json() -> Any:
    return {
        "start_id": "paper",
        "nodes": {},
        "edges": [],
        "path_lengths": {},
        "common_authors": [
            {
                "id": "author",
                "name": "Ada",
                "url": "",
                "mentions": [],
                "mention_indexes": [],
            }
        ],
        "common_references": [],
        "common_citations": [],
    }


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_graph_auth_and_deserialization(api: LocalAPI, mode: str) -> None:
    api.reply(
        {"status": "FRESH_GRAPH", "graph_json": graph_json(), "remaining_requests": 7}
    )
    client = api.client()
    result = (
        client.get_graph_sync("paper")
        if mode == "sync"
        else run_async(client.get_graph_async("paper"))
    )
    assert result.status == Status.FRESH_GRAPH
    assert result.remaining_requests == 7
    assert isinstance(result.graph_json, Graph)
    assert result.graph_json.start_id == "paper"
    assert isinstance(result.graph_json.common_authors[0], CommonAuthor)
    assert result.graph_json.common_authors[0].name == "Ada"
    assert api.requests == [("/papers-api/graph/1/paper", "local-key")]
    assert api.delays == []


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    "method,path,payload,expected",
    [
        ("get_remaining_usages", "remaining-usages", {"remaining_uses": 7}, 7),
        (
            "get_free_access_papers",
            "free-access-papers",
            {"papers": ["a", "b"]},
            ["a", "b"],
        ),
    ],
)
def test_account_endpoints(
    api: LocalAPI, mode: str, method: str, path: str, payload: Any, expected: Any
) -> None:
    api.reply(payload)
    call = getattr(api.client(), method + "_" + mode)
    assert (call() if mode == "sync" else run_async(call())) == expected
    assert api.requests == [("/papers-api/" + path, "local-key")]


@pytest.mark.parametrize("method", ["get_remaining_usages", "get_free_access_papers"])
@pytest.mark.parametrize("mode", ["sync", "async"])
def test_auth_failure(api: LocalAPI, method: str, mode: str) -> None:
    api.reply({"error": "bad key"}, status=401)
    call = getattr(api.client(), method + "_" + mode)
    with pytest.raises(RuntimeError, match="Bad response: 401"):
        call() if mode == "sync" else run_async(call())
    assert len(api.requests) == 1


def test_polling_carries_graph_and_progress(api: LocalAPI) -> None:
    api.reply({"status": "OLD_GRAPH", "graph_json": graph_json()})
    api.reply({"status": "QUEUED"})
    api.reply({"status": "IN_PROGRESS", "progress": 42})
    api.reply({"status": "FRESH_GRAPH", "graph_json": graph_json()})

    async def collect() -> Any:
        return [
            r
            async for r in api.client().get_graph_async_iterator(
                "paper", fresh_only=True
            )
        ]

    results = run_async(collect())
    assert [r.status for r in results] == [
        Status.OLD_GRAPH,
        Status.QUEUED,
        Status.IN_PROGRESS,
        Status.FRESH_GRAPH,
    ]
    assert all(r.graph_json.start_id == "paper" for r in results)
    assert results[2].progress == 42
    assert api.requests == [("/papers-api/graph/1/paper", "local-key")] * 4
    assert api.delays == [1, 1, 1]


def test_cached_graph_returns_without_rebuild(api: LocalAPI) -> None:
    api.reply({"status": "OLD_GRAPH", "graph_json": graph_json()})
    assert (
        api.client().get_graph_sync("paper", fresh_only=False).status
        == Status.OLD_GRAPH
    )
    assert api.requests == [("/papers-api/graph/0/paper", "local-key")]
    assert api.delays == []


def test_no_wait_returns_progress(api: LocalAPI) -> None:
    api.reply({"status": "IN_PROGRESS", "progress": 12})

    async def collect() -> Any:
        return [
            r
            async for r in api.client().get_graph_async_iterator(
                "paper", wait_until_complete=False
            )
        ]

    results = run_async(collect())
    assert len(results) == 1
    assert results[0].status == Status.IN_PROGRESS
    assert results[0].progress == 12
    assert api.delays == []


@pytest.mark.parametrize(
    "status",
    [
        "BAD_ID",
        "BAD_TOKEN",
        "BAD_REQUEST",
        "ERROR",
        "NOT_IN_DB",
        "OUT_OF_REQUESTS",
        "UNKNOWN",
    ],
)
def test_terminal_status(api: LocalAPI, status: str) -> None:
    api.reply({"status": status})
    assert api.client().get_graph_sync("paper").status == (
        Status.ERROR if status == "UNKNOWN" else Status(status)
    )
    assert len(api.requests) == 1
    assert api.delays == []


@pytest.mark.parametrize(
    "enabled,attempts,delays", [(False, 1, []), (True, 5, [5, 10, 20, 40])]
)
def test_overload_retry_limit(
    api: LocalAPI, enabled: bool, attempts: int, delays: Any
) -> None:
    for _ in range(attempts):
        api.reply({"status": "OVERLOADED"})
    assert (
        api.client(retry_on_overload=enabled).get_graph_sync("paper").status
        == Status.OVERLOADED
    )
    assert len(api.requests) == attempts
    assert api.delays == delays


def test_overload_backoff_resets_after_success(api: LocalAPI) -> None:
    for status in ["OVERLOADED", "QUEUED", "OVERLOADED", "FRESH_GRAPH"]:
        api.reply({"status": status})
    assert api.client().get_graph_sync("paper").status == Status.FRESH_GRAPH
    assert api.delays == [5, 1, 5]
    assert len(api.requests) == 4


def test_transient_http_error_recovers(api: LocalAPI) -> None:
    api.reply({}, status=503)
    api.reply({"status": "FRESH_GRAPH"})
    assert api.client().get_graph_sync("paper").status == Status.FRESH_GRAPH
    assert len(api.requests) == 2
    assert api.delays == [5]


@pytest.mark.parametrize(
    "payload,status,error",
    [
        ({}, 401, RuntimeError),
        ({}, 200, KeyError),
        ({"status": "FRESH_GRAPH", "graph_json": {}}, 200, MissingValueError),
    ],
)
def test_bad_graph_response_exhausts_retries(
    api: LocalAPI, payload: Any, status: int, error: Any
) -> None:
    for _ in range(3):
        api.reply(payload, status=status)
    with pytest.raises(error):
        api.client().get_graph_sync("paper")
    assert len(api.requests) == 3
    assert api.delays == [5, 5]


def test_sync_client_inside_running_loop(api: LocalAPI) -> None:
    api.reply({"status": "FRESH_GRAPH", "graph_json": graph_json()})

    async def nested() -> Any:
        return api.client().get_graph_sync("paper")

    assert run_async(nested()).status == Status.FRESH_GRAPH
