import argparse
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 加载.env环境变量
load_dotenv()

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

PERSIST_DIRECTORY = "./chroma_db"
AI_RAW_DIR = Path("raw/ai")


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


def slugify(title: str) -> str:
    """将标题转为适合文件名的 slug。"""
    slug = re.sub(r"[^\w\u4e00-\u9fff-]", "-", title.strip().lower())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or datetime.now().strftime("%Y%m%d_%H%M%S")


def write_ai_raw_note(content: str, title: str = None, category: str = None) -> Path:
    """把 AI 答案或手动补充内容写入 raw/ai，作为后续 Wiki 刷新的稳定源。"""
    if not title:
        title = datetime.now().strftime("%Y%m%d_%H%M%S")

    AI_RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(title)
    file_path = AI_RAW_DIR / f"{today}-{slug}.md"

    if file_path.exists():
        timestamp = datetime.now().strftime("%H%M%S")
        file_path = AI_RAW_DIR / f"{today}-{slug}-{timestamp}.md"

    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    metadata_lines = [
        "---",
        "source: codex-answer",
        f"ingested: {today}",
        f"sha256: {sha256}",
        f'title: "{title}"',
    ]
    if category:
        metadata_lines.append(f'category: "{category}"')
    metadata_lines.append("---")

    note = "\n".join(metadata_lines) + f"\n\n# {title}\n\n{content.strip()}\n"
    file_path.write_text(note, encoding="utf-8")
    return file_path


def add_to_vector_db(content: str, title: str = None, category: str = None):
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


def add_to_knowledge_base(
    content: str,
    title: str = None,
    category: str = None,
    also_vector: bool = False,
):
    file_path = write_ai_raw_note(content, title=title, category=category)
    print("已写入 raw/ai 源笔记！")
    print(f"文件: {file_path.as_posix()}")
    print("后续运行 auto_wiki_writer.py 时会从该源笔记生成/更新 Wiki 层。")

    if also_vector:
        add_to_vector_db(content, title=title, category=category)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="添加信息到知识库")
    parser.add_argument("content", help="要添加的内容")
    parser.add_argument("-t", "--title", help="标题（可选）")
    parser.add_argument("-c", "--category", help="分类（可选，如：习惯、备忘等）")
    parser.add_argument(
        "--also-vector",
        action="store_true",
        help="同时直接写入当前 ChromaDB 向量库（默认只写 raw/ai 源笔记）",
    )

    args = parser.parse_args()

    add_to_knowledge_base(
        content=args.content,
        title=args.title,
        category=args.category,
        also_vector=args.also_vector,
    )
