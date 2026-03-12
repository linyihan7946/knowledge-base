import argparse
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

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


def add_to_knowledge_base(content: str, title: str = None, category: str = None):
    if not title:
        title = datetime.now().strftime("%Y%m%d_%H%M%S")

    embeddings = get_embeddings()
    vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings
    )

    metadata = {"title": title}
    if category:
        metadata["category"] = category

    doc = Document(page_content=content, metadata=metadata)
    vector_db.add_documents([doc])

    print(f"已添加到向量库！")
    print(f"标题: {title}")
    if category:
        print(f"分类: {category}")
    print(f"内容: {content}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="添加信息到知识库")
    parser.add_argument("content", help="要添加的内容")
    parser.add_argument("-t", "--title", help="标题（可选）")
    parser.add_argument("-c", "--category", help="分类（可选，如：习惯、备忘等）")

    args = parser.parse_args()

    add_to_knowledge_base(
        content=args.content,
        title=args.title,
        category=args.category,
    )
