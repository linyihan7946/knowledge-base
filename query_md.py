import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings


load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def api_key() -> str | None:
    return os.getenv("KB_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")


def base_url() -> str | None:
    return os.getenv("KB_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL") or os.getenv("OPENAI_BASE_URL")


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.getenv("KB_EMBEDDING_MODEL", "text-embedding-v3"),
        api_key=api_key(),
        base_url=base_url(),
        chunk_size=10,
        check_embedding_ctx_length=False,
    )


def query_vector_db(query_text: str, persist_dir: str, top_k: int = 3) -> None:
    persist_path = resolve_path(persist_dir)
    vector_db = Chroma(persist_directory=str(persist_path), embedding_function=get_embeddings())
    results = vector_db.similarity_search(query_text, k=top_k)

    print("=" * 60)
    print(f"查询：{query_text}")
    print("=" * 60)

    if not results:
        print("未找到相关内容。请先运行 python kb.py build-all。")
        return

    for index, doc in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        layer = doc.metadata.get("source_layer", "unknown")
        print(f"\n--- 结果 {index} ---")
        print(f"来源：{source}")
        print(f"层级：{layer}")
        print(doc.page_content.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="向量库语义检索")
    parser.add_argument("query", help="查询文本")
    parser.add_argument("-k", "--top_k", type=int, default=3, help="返回结果数量")
    parser.add_argument("-p", "--persist", default="./chroma_db", help="向量库目录")
    args = parser.parse_args()
    query_vector_db(args.query, args.persist, args.top_k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
