import argparse
import sys
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 加载.env环境变量
load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PERSIST_DIRECTORY = "./chroma_db"


def get_embeddings():
    """获取阿里百炼embedding模型"""
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


def query_vector_db(query_text: str, persist_dir: str, top_k: int = 3):
    # 1. 加载 Embedding 模型
    embeddings = get_embeddings()

    # 2. 加载现有数据库
    vector_db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # 3. 执行相似度搜索
    results = vector_db.similarity_search(query_text, k=top_k)

    # 4. 输出结果
    print("=" * 60)
    print(f"查询: {query_text}")
    print("=" * 60)

    for i, doc in enumerate(results):
        source = doc.metadata.get("source", "未知")
        content = doc.page_content.strip()
        print(f"\n--- 结果 {i + 1} ---")
        print(f"来源: {source}")
        print(f"内容:\n{content}")
        print("-" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="向量数据库查询工具")
    parser.add_argument("query", help="查询文本")
    parser.add_argument("-k", "--top_k", type=int, default=3, help="返回结果数量")
    parser.add_argument("-p", "--persist", default=PERSIST_DIRECTORY, help="向量库路径")

    args = parser.parse_args()

    query_vector_db(args.query, args.persist, args.top_k)
