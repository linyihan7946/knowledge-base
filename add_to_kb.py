import argparse
import sys
import os
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PERSIST_DIRECTORY = "./chroma_db"
KNOWLEDGE_DIR = "./docs/知识库"


def get_embeddings(offline: bool = True):
    model_kwargs = {"local_files_only": offline}
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name="./models/damo/nlp_gte_sentence-embedding_chinese-base",
            model_kwargs=model_kwargs,
        )
        return embeddings
    except Exception:
        pass
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs=model_kwargs,
    )


def add_to_knowledge_base(
    content: str, title: str = None, category: str = None, offline: bool = True
):
    if not title:
        title = datetime.now().strftime("%Y%m%d_%H%M%S")

    embeddings = get_embeddings(offline=offline)
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
    parser.add_argument("--online", action="store_true", help="在线模式")

    args = parser.parse_args()
    offline = not args.online

    add_to_knowledge_base(
        content=args.content, title=args.title, category=args.category, offline=offline
    )
