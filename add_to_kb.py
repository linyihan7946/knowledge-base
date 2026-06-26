import argparse
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
AI_RAW_DIR = ROOT / "raw" / "ai"
PERSIST_DIRECTORY = ROOT / "chroma_db"


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


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]", "-", title.strip().lower())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or datetime.now().strftime("%Y%m%d-%H%M%S")


def write_ai_raw_note(content: str, title: str | None = None, category: str | None = None) -> Path:
    title = title or datetime.now().strftime("%Y%m%d-%H%M%S")
    AI_RAW_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    file_path = AI_RAW_DIR / f"{today}-{slugify(title)}.md"
    if file_path.exists():
        file_path = AI_RAW_DIR / f"{today}-{slugify(title)}-{datetime.now().strftime('%H%M%S')}.md"

    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    frontmatter = [
        "---",
        "source: manual-note",
        f"ingested: {today}",
        f"sha256: {sha256}",
        f'title: "{title}"',
    ]
    if category:
        frontmatter.append(f'category: "{category}"')
    frontmatter.append("---")

    note = "\n".join(frontmatter) + f"\n\n# {title}\n\n{content.strip()}\n"
    file_path.write_text(note, encoding="utf-8")
    return file_path


def add_to_vector_db(content: str, title: str, category: str | None = None) -> None:
    metadata = {"title": title, "source": "manual-note", "source_layer": "raw-note-mirror"}
    if category:
        metadata["category"] = category
    vector_db = Chroma(persist_directory=str(PERSIST_DIRECTORY), embedding_function=get_embeddings())
    vector_db.add_documents([Document(page_content=content, metadata=metadata)])
    if hasattr(vector_db, "persist"):
        vector_db.persist()


def add_to_knowledge_base(content: str, title: str | None, category: str | None, also_vector: bool) -> None:
    title = title or datetime.now().strftime("%Y%m%d-%H%M%S")
    file_path = write_ai_raw_note(content, title=title, category=category)
    print(f"已写入原始补充笔记：{file_path.relative_to(ROOT).as_posix()}")
    print("下一次运行 python kb.py build-all 时，会进入 Wiki 和向量库。")

    if also_vector:
        add_to_vector_db(content, title=title, category=category)
        print("已同时写入当前向量库。")


def main() -> int:
    parser = argparse.ArgumentParser(description="追加一条原始笔记")
    parser.add_argument("content", help="要追加的内容")
    parser.add_argument("-t", "--title", help="标题")
    parser.add_argument("-c", "--category", help="分类")
    parser.add_argument("--also-vector", action="store_true", help="同时写入当前向量库")
    args = parser.parse_args()
    add_to_knowledge_base(args.content, args.title, args.category, args.also_vector)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
