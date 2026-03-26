import json
from pathlib import Path
import logging
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma

from dotenv import load_dotenv

load_dotenv()

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

file_path = "output.txt"


def process_and_store_message(message: str, metadata: dict | None = None, persist_directory: str = "./chroma_db"):
    """
    メッセージをチャンキングしてOpenAIでベクトル化して保存する
    """

    doc = Document(page_content=message, metadata=metadata or {})
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", "。", "、", " ", ""]
    )
    chunks = text_splitter.split_documents([doc])
    embeddings = AzureOpenAIEmbeddings(azure_deployment="text-embedding-3-large")

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=persist_directory
    )

    return vectorstore


def search(query: str, k: int = 10, persist_directory: str = "./chroma_db") -> list[dict]:
    """
    クエリ文字列でChromaDBをコサイン類似度検索し、上位k件を返す。
    """
    embeddings = AzureOpenAIEmbeddings(azure_deployment="text-embedding-3-large")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [
        {"content": doc.page_content, "metadata": doc.metadata, "score": score}
        for doc, score in results
    ]


def extract_messages(transcript_content: str) -> list[dict]:
    """
    JSONL形式のトランスクリプトからuser/assistantのテキストメッセージを抽出する。
    戻り値: [{"role": "user"|"assistant", "text": "..."}]
    """
    messages = []
    for line in transcript_content.splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        message = entry.get("message")
        if not message:
            continue

        role = message.get("role")
        content = message.get("content")
        if role not in ("user", "assistant") or content is None:
            continue

        # content が文字列の場合（ユーザの直接入力）
        if isinstance(content, str):
            if content.strip():
                messages.append({"role": role, "text": content})
            continue

        # content が配列の場合（テキストブロックを抽出）
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    messages.append({"role": role, "text": block["text"]})

    return messages


def process(transcript_content: str):
    """
    トランスクリプトの内容（JSONL文字列）を受け取り、ログ記録とベクトル化を行う。
    main.py がホスト上でファイルを読み込み、内容をキュー経由で渡す。
    """
    # output.txt にトランスクリプト内容を書き出す
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(transcript_content)

    messages = extract_messages(transcript_content)

    # ログに記録
    for msg in messages:
        label = "User" if msg["role"] == "user" else "Assistant"
        logging.info(f"{label}: {msg['text']}")

    # メッセージごとにroleをメタデータとしてベクトル化して保存
    for msg in messages:
        process_and_store_message(msg["text"], metadata={"role": msg["role"]})
