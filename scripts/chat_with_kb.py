import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
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


def api_key() -> str | None:
    return os.getenv("KB_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")


def base_url() -> str | None:
    return os.getenv("KB_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL") or os.getenv("OPENAI_BASE_URL")


def normalize_source(source: str) -> str:
    return (source or "unknown").replace("\\", "/")


def infer_source_layer(source: str) -> str:
    source = normalize_source(source)
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
    if source.startswith(("build/docs/", "docs/")):
        return "raw-note-mirror"
    return "unknown"


def get_source_layer(doc) -> str:
    source = normalize_source(doc.metadata.get("source", "unknown"))
    layer = infer_source_layer(source)
    return layer if layer != "unknown" else doc.metadata.get("source_layer", "unknown")


def describe_source_layer(layer: str) -> str:
    return {
        "wiki": "Wiki 层",
        "raw-note-mirror": "原始笔记镜像",
        "system": "系统文档",
        "unknown": "未知来源",
    }.get(layer, layer)


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.getenv("KB_EMBEDDING_MODEL", "text-embedding-v3"),
        api_key=api_key(),
        base_url=base_url(),
        chunk_size=10,
        check_embedding_ctx_length=False,
    )


def get_llm(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=api_key(),
        base_url=base_url(),
        temperature=0.3,
    )


def unique_non_system_docs(docs) -> list:
    seen = set()
    unique_docs = []
    for doc in docs:
        source = normalize_source(doc.metadata.get("source", "unknown"))
        if infer_source_layer(source) == "system":
            continue
        key = (source, doc.page_content[:120])
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)
    return unique_docs


SYSTEM_PROMPT = """你是一个知识库问答助手。请只根据下面提供的知识库内容回答问题。

要求：
1. 不要编造知识库中没有的信息。
2. 如果资料不足，请明确说明。
3. 回答要简洁、准确、有条理。
4. 涉及多个来源时，请在回答中标注来源。
5. 使用中文回答。

知识库内容：
{context}
"""


def retrieve_docs(query_text: str, persist_dir: str, top_k: int):
    vector_db = Chroma(persist_directory=str(resolve_path(persist_dir)), embedding_function=get_embeddings())
    candidates = []
    for metadata_filter, search_k in (
        ({"source_layer": "raw-note-mirror"}, max(top_k * 8, 20)),
        ({"source_layer": "wiki"}, max(top_k * 4, top_k)),
        (None, max(top_k * 4, top_k)),
    ):
        try:
            if metadata_filter:
                candidates.extend(vector_db.similarity_search(query_text, k=search_k, filter=metadata_filter))
            else:
                candidates.extend(vector_db.similarity_search(query_text, k=search_k))
        except Exception:
            continue
    return unique_non_system_docs(candidates)[:top_k]


def chat_with_kb(query_text: str, persist_dir: str, top_k: int = 3, model: str = "qwen-plus") -> None:
    print("=" * 60)
    print(f"问题：{query_text}")
    print("=" * 60)

    results = retrieve_docs(query_text, persist_dir, top_k)
    if not results:
        print("未找到相关文档。请先运行 python kb.py build-all。")
        return

    context_parts = []
    for index, doc in enumerate(results, start=1):
        source = normalize_source(doc.metadata.get("source", "unknown"))
        layer = describe_source_layer(get_source_layer(doc))
        context_parts.append(f"[Source {index}: {source}; layer={layer}]\n{doc.page_content.strip()}")

    context = "\n\n---\n\n".join(context_parts)
    llm = get_llm(model)
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
            HumanMessage(content=query_text),
        ]
    )

    print("\n回答：")
    print(str(response.content).strip())
    print("\n参考来源：")
    for index, doc in enumerate(results, start=1):
        source = normalize_source(doc.metadata.get("source", "unknown"))
        layer = describe_source_layer(get_source_layer(doc))
        print(f"{index}. {source} ({layer})")


def main() -> int:
    parser = argparse.ArgumentParser(description="基于知识库的 RAG 问答")
    parser.add_argument("query", help="问题")
    parser.add_argument("-k", "--top_k", type=int, default=3, help="检索结果数量")
    parser.add_argument("-p", "--persist", default="./build/chroma_db", help="向量库目录")
    parser.add_argument("-m", "--model", default=os.getenv("KB_LLM_MODEL", os.getenv("WIKI_LLM_MODEL", "qwen-plus")))
    args = parser.parse_args()
    chat_with_kb(args.query, args.persist, args.top_k, args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
