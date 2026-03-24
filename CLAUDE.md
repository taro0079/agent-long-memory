# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This project is a Claude Code **hook script** that logs conversation transcripts. It reads event data from stdin (as provided by Claude Code's hook system), extracts the transcript, and appends user/assistant messages to `logs/log.log`.

## Setup

```bash
uv sync        # install dependencies (currently none beyond stdlib)
uv run main.py # run the script
```

Python 3.14 is required (managed via `.python-version` and `uv`).

## How It Works

`main.py` is intended to be registered as a Claude Code hook (e.g., a `Stop` hook). Claude Code passes a JSON event object via stdin containing a `transcript_path` field. The script:

1. Reads the JSONL transcript file at `transcript_path`
2. Extracts `user` and `assistant` role messages — both are arrays of content blocks; only `type: "text"` entries are logged
3. Logs them to `logs/log.log` with timestamps

## Testing

To test manually, pipe a JSON object with a `transcript_path` pointing to a JSONL transcript file:

```bash
echo '{"transcript_path": "/path/to/transcript.jsonl"}' | uv run main.py
```

`test.json` can be used as sample input for the hook event payload (currently empty — populate it with a real hook event JSON before use).

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

**Note:** `main.py:42` contains a `logging.info(content)` call that logs the raw content array before the formatted role-specific lines. This appears to be a debug leftover — each message is logged twice (raw + formatted).
