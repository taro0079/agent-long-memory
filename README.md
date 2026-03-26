# agent-long-memory

Claude Code / GitHub Copilot (VS Code) のフックスクリプト。会話トランスクリプトをログに記録し、ベクトル埋め込みとして保存することで、過去の会話を後から検索・参照できるようにします。

## セットアップ

```bash
uv sync                    # Python 依存関係のインストール
docker compose up -d       # Redis と RQ ワーカーの起動
```

`.env` ファイルに Azure OpenAI の認証情報が必要です（`tasks.py` の `AzureOpenAIEmbeddings` で使用）。

## アーキテクチャ

- **`main.py`** — フックのエントリポイント（ホスト上で実行）。stdin から JSON イベントを読み込み、`transcript_path` を取得してトランスクリプトを Redis キューに enqueue する。
- **`tasks.py`** — RQ ワーカータスク（Docker 内で実行）。トランスクリプトのログ記録と ChromaDB へのベクトル埋め込み保存を行う。

---

## Claude Code フックとして登録する

`~/.claude/settings.json` の `hooks` セクションに以下を追加します。

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

Claude Code がセッションを終了するたびに `main.py` が起動し、トランスクリプトが処理されます。

---

## GitHub Copilot (VS Code) フックとして登録する

VS Code の Copilot エージェントは **Claude Code と同じ `~/.claude/settings.json`** を読み込みます。そのため、Claude Code 用の設定をすでに書いている場合は追加作業不要です。

### 設定ファイルの場所

| スコープ | パス |
|---|---|
| ユーザー共通（推奨） | `~/.claude/settings.json` |
| ワークスペースのみ | `.claude/settings.json` / `.claude/settings.local.json` |

### 設定例

`~/.claude/settings.json` に以下を追記します（Claude Code と共有できます）。

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "cd /path/to/agent-long-memory && uv run main.py"
      }
    ]
  }
}
```

### フックが受け取る stdin ペイロード

`Stop` イベント発火時、`main.py` の stdin には以下の JSON が渡されます。

```json
{
  "timestamp": "2026-03-26T10:30:00.000Z",
  "cwd": "/path/to/workspace",
  "sessionId": "session-identifier",
  "hookEventName": "Stop",
  "transcript_path": "/path/to/transcript.json",
  "stop_hook_active": false
}
```

`transcript_path` のキー名は Claude Code と同じため、現在の `main.py` をそのまま使用できます。

### 利用可能なフックイベント

| イベント | タイミング |
|---|---|
| `SessionStart` | セッションの最初のプロンプト送信時 |
| `UserPromptSubmit` | プロンプト送信のたび |
| `PreToolUse` | ツール（ファイル編集・ターミナル等）実行前 |
| `PostToolUse` | ツール実行後 |
| `PreCompact` | コンテキスト圧縮前 |
| `SubagentStart` | サブエージェント起動時 |
| `SubagentStop` | サブエージェント終了時 |
| `Stop` | エージェントセッション終了時 |

### 注意事項

- `Stop` フックがセッション終了をブロックしたい場合（例：処理完了まで待機）、stdout に `{"hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": "..."}}` を出力します。ブロックするとエージェントが追加ターンを消費するため、通常は `exit 0` で終了させてください。
- `stop_hook_active` が `true` の場合は前の Stop フックの継続ターンなので、無限ループを避けるため処理をスキップしてください。

---

## 参考

- [Agent hooks in Visual Studio Code (Preview)](https://code.visualstudio.com/docs/copilot/customization/hooks)
