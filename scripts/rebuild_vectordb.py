import argparse
import shutil
from pathlib import Path

from ingest_md import ingest_markdown


ROOT = Path(__file__).resolve().parent.parent


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="删除并重建 ChromaDB 向量库")
    parser.add_argument("--source", "-s", default="./build/docs", help="Markdown 文档目录")
    parser.add_argument("--persist", "-p", default="./build/chroma_db", help="向量库目录")
    args = parser.parse_args()

    persist_path = resolve_path(args.persist)
    if persist_path.exists():
        print(f"删除旧向量库：{persist_path}")
        shutil.rmtree(persist_path)

    ingest_markdown(args.source, args.persist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
