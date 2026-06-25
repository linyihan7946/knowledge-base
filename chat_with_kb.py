"""
LLM 问答脚本 — 基于知识库的 RAG 对话
使用阿里云百炼 LLM + ChromaDB 语义检索
"""
import argparse
import os
import sys

# 移除 Hermes venv 路径，避免加载损坏的 numpy
sys.path = [p for p in sys.path if 'hermes-agent' not in p.lower()]

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage

# 加载.env环境变量
load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PERSIST_DIRECTORY = "./chroma_db"
SYSTEM_SOURCES = {"docs/log.md", "docs/index.md", "docs/SCHEMA.md"}


def normalize_source_path(source: str) -> str:
    return (source or "unknown").replace("\\", "/")


def infer_source_layer(source: str) -> str:
    normalized = normalize_source_path(source)
    if normalized in SYSTEM_SOURCES:
        return "system"
    if normalized.startswith(("docs/concepts/", "docs/entities/", "docs/comparisons/")):
        return "wiki"
    if normalized.startswith("docs/"):
        return "raw-note-mirror"
    return "unknown"


def describe_source_layer(layer: str) -> str:
    descriptions = {
        "wiki": "Wiki layer (concepts/entities/comparisons)",
        "raw-note-mirror": "Raw note mirror under docs",
        "system": "System/index/log docs",
        "unknown": "Unknown layer",
    }
    return descriptions.get(layer, layer)


def get_source_layer(doc) -> str:
    source = normalize_source_path(doc.metadata.get("source", "unknown"))
    inferred = infer_source_layer(source)
    if inferred != "unknown":
        return inferred
    return doc.metadata.get("source_layer") or "unknown"


def is_system_source(doc) -> bool:
    source = normalize_source_path(doc.metadata.get("source", "unknown"))
    return infer_source_layer(source) == "system"


def unique_non_system_docs(docs):
    seen_sources = set()
    unique_docs = []
    for doc in docs:
        if is_system_source(doc):
            continue

        source = normalize_source_path(doc.metadata.get("source", "unknown"))
        key = (source, doc.page_content[:120])
        if key in seen_sources:
            continue

        seen_sources.add(key)
        unique_docs.append(doc)
    return unique_docs


def prioritize_docs_for_query(query_text: str, docs):
    travel_terms = ("旅游", "旅行", "景点", "目的地")
    if any(term in query_text for term in travel_terms):
        return sorted(
            docs,
            key=lambda doc: (
                0
                if normalize_source_path(doc.metadata.get("source", "unknown")).startswith("docs/旅游/")
                else 1
            ),
        )
    return docs

# 系统提示词 — 定义 LLM 的角色和行为
SYSTEM_PROMPT = """你是一个个人知识库助手。请根据以下检索到的文档内容，回答用户的问题。

要求：
1. 仅基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，请明确告知用户
3. 回答要简洁、准确、有条理
4. 如果涉及多个来源，请标注来源
5. 使用中文回答

提供的文档内容：
{context}
"""


def get_embeddings():
    """获取阿里百炼 embedding 模型"""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    base_url = os.environ.get(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    return OpenAIEmbeddings(
        model="text-embedding-v3",
        api_key=api_key,
        base_url=base_url,
        chunk_size=10,
        check_embedding_ctx_length=False,
    )


def get_llm():
    """获取阿里百炼 LLM 模型"""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    base_url = os.environ.get(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    return ChatOpenAI(
        model="qwen-plus",  # 可使用 qwen-turbo（更快更便宜）或 qwen-plus（质量更高）
        api_key=api_key,
        base_url=base_url,
        temperature=0.3,  # 较低温度，保证回答准确性
    )


def chat_with_kb(query_text: str, persist_dir: str, top_k: int = 3, model: str = "qwen-plus"):
    """
    基于知识库的 LLM 问答
    
    Args:
        query_text: 用户问题
        persist_dir: 向量库路径
        top_k: 检索返回结果数量
        model: LLM 模型名称
    """
    print("=" * 60)
    print(f"🔍 查询: {query_text}")
    print("=" * 60)

    # 1. 加载 Embedding 模型
    print("\n📦 加载向量数据库...")
    embeddings = get_embeddings()
    vector_db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # 2. 执行相似度搜索
    print(f"🔎 检索相关文档（top {top_k}）...")
    candidate_results = []
    layered_filters = (
        ({"source_layer": "raw-note-mirror"}, max(top_k * 12, 50)),
        ({"source_layer": "wiki"}, max(top_k * 3, top_k)),
        (None, max(top_k * 3, top_k)),
    )
    for metadata_filter, search_k in layered_filters:
        try:
            if metadata_filter:
                candidate_results.extend(
                    vector_db.similarity_search(query_text, k=search_k, filter=metadata_filter)
                )
            else:
                candidate_results.extend(vector_db.similarity_search(query_text, k=search_k))
        except Exception:
            continue

    results = prioritize_docs_for_query(query_text, unique_non_system_docs(candidate_results))[:top_k]
    if not results:
        results = candidate_results[:top_k]

    if not results:
        print("\n❌ 未找到相关文档，请检查向量库是否已构建。")
        return

    # 3. 构建上下文
    context_parts = []
    for i, doc in enumerate(results):
        source = normalize_source_path(doc.metadata.get("source", "unknown"))
        source_layer = get_source_layer(doc)
        content = doc.page_content.strip()
        context_parts.append(
            f"[Source {i+1}: {source}; layer={describe_source_layer(source_layer)}]\n{content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    # 4. 打印检索结果（调试用）
    print(f"\n✅ 找到 {len(results)} 个相关文档块：")
    for i, doc in enumerate(results):
        source = normalize_source_path(doc.metadata.get("source", "unknown"))
        source_layer = get_source_layer(doc)
        content_preview = doc.page_content.strip()[:150] + "..."
        print(f"\n--- 检索结果 {i + 1} ---")
        print(f"来源: {source}")
        print(f"来源层: {describe_source_layer(source_layer)}")
        print(f"内容: {content_preview}")

    # 5. 调用 LLM 生成回答
    print(f"\n🤖 调用 LLM ({model}) 生成回答...")
    llm = get_llm()

    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query_text),
    ]

    response = llm.invoke(messages)
    answer = response.content

    # 6. 输出最终回答
    print("\n" + "=" * 60)
    print("💡 AI 回答：")
    print("=" * 60)
    print(answer)
    layers = sorted(
        {
            get_source_layer(doc)
            for doc in results
        }
    )
    print("\n数据来源层: " + ", ".join(describe_source_layer(layer) for layer in layers))
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="基于知识库的 LLM 问答工具")
    parser.add_argument("query", help="查询问题")
    parser.add_argument("-k", "--top_k", type=int, default=3, help="检索结果数量")
    parser.add_argument("-p", "--persist", default=PERSIST_DIRECTORY, help="向量库路径")
    parser.add_argument("-m", "--model", default="qwen-plus", help="LLM 模型（qwen-turbo/qwen-plus/qwen-max）")

    args = parser.parse_args()

    chat_with_kb(args.query, args.persist, args.top_k, args.model)
