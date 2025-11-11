#!/usr/bin/env python3
"""CLI tool to test the verbose mode of the Connected Papers API client."""

import argparse
import sys
from typing import Optional

from connectedpapers import ConnectedPapersClient
from connectedpapers.connected_papers_client import GraphResponse


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a paper graph with verbose logging enabled"
    )
    parser.add_argument("paper_id", help="The paper ID (Semantic Scholar SHA)")
    parser.add_argument(
        "--api-key",
        required=True,
        help="Your Connected Papers API key",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Force a fresh graph rebuild (ignore cached graphs)",
    )
    parser.add_argument(
        "--accept-old",
        action="store_true",
        help="Accept old/cached graph if available (return immediately)",
    )
    parser.add_argument(
        "--show-papers",
        action="store_true",
        help="Display all papers in the graph",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for graph to be ready (return immediately with current status)",
    )

    args = parser.parse_args()

    print(f"\nFetching graph for paper: {args.paper_id}")

    # Determine the mode
    if args.no_wait:
        fresh_only = False
        print("Mode: Quick check (no waiting)")
    elif args.accept_old:
        fresh_only = False
        print("Mode: Accept cached graph if available")
    else:
        fresh_only = True  # Default: wait for complete graph
        if args.fresh:
            print("Mode: Force fresh rebuild (ignore cache)")
        else:
            print("Mode: Wait for complete graph")

    print("-" * 60)

    # Enable verbose logging and automatic retries for OVERLOADED status
    client = ConnectedPapersClient(
        access_token=args.api_key,
        verbose=True,
        retry_on_overload=True,  # Automatically retry when server is overloaded
    )

    try:
        if args.no_wait:
            # Use the iterator to get just the first response without waiting
            print("\n[Quick check - returning immediately with current status]")

            async def get_first_response() -> Optional[GraphResponse]:
                async for response in client.get_graph_async_iterator(
                    args.paper_id, fresh_only=False, wait_until_complete=False
                ):
                    return response
                return None

            import asyncio

            response = asyncio.run(get_first_response())
            if response is None:
                print("No response received")
                return 1
        else:
            # Use fresh_only to control waiting behavior
            if fresh_only:
                print("\n[Waiting for complete graph - this may take up to 60 seconds]")
                print("[Will automatically retry if server is OVERLOADED]")
            else:
                print(
                    "\n[Will return cached graph if available, otherwise wait for completion]"
                )
            print()
            response = client.get_graph_sync(args.paper_id, fresh_only=fresh_only)

        print("-" * 60)
        print(f"\nFinal Status: {response.status.value}")

        if response.graph_json:
            print(f"Graph contains {len(response.graph_json.nodes)} papers")
            print(f"Start paper ID: {response.graph_json.start_id}")

            if args.show_papers:
                print("\n" + "=" * 60)
                print("PAPERS IN GRAPH")
                print("=" * 60)
                for i, (paper_id, paper) in enumerate(
                    response.graph_json.nodes.items(), 1
                ):
                    print(f"\n{i}. {paper.title}")
                    print(f"   ID: {paper_id}")
                    if paper.year:
                        print(f"   Year: {paper.year}")
                    if paper.authors:
                        author_names = ", ".join([a.name for a in paper.authors[:3]])
                        if len(paper.authors) > 3:
                            author_names += f" (+ {len(paper.authors) - 3} more)"
                        print(f"   Authors: {author_names}")
                    if paper.venue:
                        print(f"   Venue: {paper.venue}")
                print("\n" + "=" * 60)
        else:
            print("No graph data received")

        if response.remaining_requests is not None:
            print(f"Remaining API requests: {response.remaining_requests}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
