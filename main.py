import json
import sys
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


def process_and_store_message(message: str, persist_directory: str = "./chroma_db"):
    """
    メッセージをチャンキングしてOpenAIでベクトル化して保存する
    """

    doc = Document(page_content=message, metadata={})
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50, separators=["\n\n", "\n", "。", "、", " ", ""]
    )
    chunks = text_splitter.split_documents([doc])
    embeddings = AzureOpenAIEmbeddings(azure_deployment="text-embedding-3-large")

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory=persist_directory
    )

    return vectorstore


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
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in f:
                file.write(line)
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
                    logging.info(content)
                    for user_content in content:
                        if user_content["type"] == "text":
                            logging.info("User: " + user_content["text"])

                if role == "assistant":
                    for agent_content in content:
                        if agent_content["type"] == "text":
                            logging.info("Assistant: " + agent_content["text"])
    with open(file_path, 'r', encoding='utf-8') as ff:
        file_content = ff.read()
        process_and_store_message(file_content);

if __name__ == "__main__":
    main()
