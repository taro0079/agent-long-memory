#!/bin/sh
set -e

export PATH="/opt/venv/bin:$PATH"

# pyproject.toml等が更新された場合に依存関係を再同期
if [ ! -x /opt/venv/bin/rq ]; then
    echo "Installing dependencies..."
    uv sync --frozen --no-dev
fi

exec "$@"
