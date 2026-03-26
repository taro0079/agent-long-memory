import sys
import json
from tasks import search


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run search.py <query>", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    results = search(query)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
