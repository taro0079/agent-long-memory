import json
import sys
from pathlib import Path
import logging


log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "log.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)


def main():
    try:
        event_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logging.warning("stdin is not valid JSON")
        sys.exit(0)

    transcript_path = event_data.get("transcript_path")
    if not transcript_path:
        logging.warning("transcript_path not found in event_data")
        sys.exit(0)
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            message = entry.get("message")
            if not message:
                continue

            role = message.get("role")
            content = message.get("content")
            if not isinstance(content, list):
                continue

            if role == "user":
                for user_content in content:
                    if user_content["type"] == "text":
                        logging.info("User: " + user_content["text"])

            if role == "assistant":
                for agent_content in content:
                    if agent_content["type"] == "text":
                        logging.info("Assistant: " + agent_content["text"])


if __name__ == "__main__":
    main()
