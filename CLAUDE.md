# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This project is a Claude Code **hook script** that captures conversation transcripts, logs them, and stores them as vector embeddings for later retrieval. It uses a two-process architecture: a lightweight CLI entry point (`main.py`) enqueues work via Redis/RQ, and a Docker-based worker (`tasks.py`) handles the heavy processing (logging + embedding).

## Setup

```bash
uv sync                    # install Python dependencies
docker compose up -d       # start Redis and the RQ worker
```

Python 3.14 is required (managed via `.python-version` and `uv`).

A `.env` file is required with Azure OpenAI credentials (used by `AzureOpenAIEmbeddings` in `tasks.py`).

## Architecture

**`main.py`** — Hook entry point, runs on the host. Reads a JSON event from stdin, extracts `transcript_path`, reads the transcript file, and enqueues its content to an RQ job queue via Redis (`localhost:6379`).

**`tasks.py`** — RQ worker task, runs inside Docker. The `process()` function:
1. Writes raw transcript to `output.txt`
2. Parses JSONL lines, extracts `user`/`assistant` messages (only `type: "text"` content blocks), and logs them to `logs/log.log`
3. Chunks the full transcript with `RecursiveCharacterTextSplitter` and stores embeddings in ChromaDB (`./chroma_db`) via Azure OpenAI's `text-embedding-3-large`

**Docker Compose** runs two services: `redis` (Alpine) and `worker` (Python 3.14-slim with uv). The worker mounts the project directory and a named volume for `chroma_db`.

## Commands

```bash
# Run the hook manually
echo '{"transcript_path": "/path/to/transcript.jsonl"}' | uv run main.py

# Start/stop infrastructure
docker compose up -d
docker compose down

# View worker logs
docker compose logs worker -f
```

## Registering as a Hook

In Claude Code settings (`~/.claude/settings.json`), add under `hooks`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cd /path/to/agent-long-memory && uv run main.py"
          }
        ]
      }
    ]
  }
}
```

## Log Output

Logs are written to `logs/log.log` (auto-created). Format:
```
2026-03-24 11:36:46 [INFO] User: <message>
2026-03-24 11:36:46 [INFO] Assistant: <text>
```
