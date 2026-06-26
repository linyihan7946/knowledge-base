import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownTextSplitter


load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DOCS_PREFIXES = ("build/docs/", "docs/")
SYSTEM_SOURCES = {
    "build/docs/log.md",
    "build/docs/index.md",
    "build/docs/SCHEMA.md",
    "docs/log.md",
    "docs/index.md",
    "docs/SCHEMA.md",
}


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def relative_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def api_key() -> str | None:
    return os.getenv("KB_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")


def base_url() -> str | None:
    return os.getenv("KB_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL") or os.getenv("OPENAI_BASE_URL")


def embedding_model() -> str:
    return os.getenv("KB_EMBEDDING_MODEL", "text-embedding-v3")


def classify_source_layer(source: str) -> str:
    if source in SYSTEM_SOURCES:
        return "system"
    if source.startswith(
        (
            "build/docs/concepts/",
            "build/docs/entities/",
            "build/docs/comparisons/",
            "docs/concepts/",
            "docs/entities/",
            "docs/comparisons/",
        )
    ):
        return "wiki"
    if source.startswith(DOCS_PREFIXES):
        return "raw-note-mirror"
    return "unknown"


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=embedding_model(),
        api_key=api_key(),
        base_url=base_url(),
        chunk_size=10,
        check_embedding_ctx_length=False,
    )


def load_markdown_documents(source_dir: Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(source_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        source = relative_to_root(path)
        documents.append(
            Document(
                page_content=text,
                metadata={"source": source, "source_layer": classify_source_layer(source)},
            )
        )
    return documents


def ingest_markdown(source_dir: str, persist_dir: str) -> None:
    source_path = resolve_path(source_dir)
    persist_path = resolve_path(persist_dir)
    source_path.mkdir(parents=True, exist_ok=True)

    print(f"加载 Markdown 目录：{relative_to_root(source_path)}")
    documents = load_markdown_documents(source_path)
    if not documents:
        print("未找到可入库的 Markdown 文件。")
        return

    splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
    if not chunks:
        print("Markdown 文件为空，未生成向量块。")
        return

    print(f"文件数：{len(documents)}，文本块：{len(chunks)}")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=str(persist_path),
    )
    if hasattr(vector_db, "persist"):
        vector_db.persist()
    print(f"向量库已保存：{relative_to_root(persist_path)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Markdown 向量化入库")
    parser.add_argument("--source", "-s", default="./build/docs", help="Markdown 文档目录")
    parser.add_argument("--persist", "-p", default="./build/chroma_db", help="ChromaDB 保存目录")
    args = parser.parse_args()
    ingest_markdown(args.source, args.persist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
