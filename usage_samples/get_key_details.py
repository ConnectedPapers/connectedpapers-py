import sys

from connectedpapers import ConnectedPapersClient


def main() -> int:
    client = ConnectedPapersClient()
    remaining_uses_count = client.sync_get_remaining_usages()
    print(f"Remaining uses count: {remaining_uses_count}")
    free_access_papers = client.sync_get_free_access_papers()
    print(f"Free access papers: {free_access_papers}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
