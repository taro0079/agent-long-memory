import sys
import json
from typing import TextIO
from redis import Redis
from rq import Queue
from tasks import process

redis_conn = Redis(host="localhost", port=6379)
q = Queue(connection=redis_conn)


def handle_user_request(user_message: TextIO):
    data = user_message.read()

    # stdinのJSONからtranscript_pathを取得し、ファイル内容を読み込む
    try:
        event_data = json.loads(data)
    except json.JSONDecodeError:
        print("stdin is not valid JSON", file=sys.stderr)
        sys.exit(0)

    transcript_path = event_data.get("transcript_path")
    if not transcript_path:
        print("transcript_path not found in event_data", file=sys.stderr)
        sys.exit(0)

    # ホスト上でトランスクリプトファイルを読み込み、内容をキューに渡す
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()
    except FileNotFoundError:
        print(f"Transcript file not found: {transcript_path}", file=sys.stderr)
        sys.exit(0)

    q.enqueue(process, transcript_content)


if __name__ == "__main__":
    handle_user_request(sys.stdin)
