import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
SCRIPTS = ROOT / "scripts"
WIKI_DIR = ROOT / "wiki"
BUILD_DIR = ROOT / "build"
DEFAULT_DOCS = "./build/docs"
DEFAULT_VECTOR_DB = "./build/chroma_db"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def run(args: list[str]) -> int:
    print("> " + " ".join(args))
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    completed = subprocess.run(args, cwd=ROOT, env=env)
    return completed.returncode


def ensure_dirs() -> None:
    for path in [
        ROOT / "raw" / "notes",
        ROOT / "raw" / "ai",
        WIKI_DIR / "concepts",
        WIKI_DIR / "entities",
        WIKI_DIR / "comparisons",
        BUILD_DIR / "docs",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    for file_name, content in {
        "index.md": "# Knowledge Base Wiki\n\n运行 `python kb.py build-wiki` 生成索引。\n",
        "log.md": "# 构建日志\n\n",
    }.items():
        path = WIKI_DIR / file_name
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def init_project(_args: argparse.Namespace) -> int:
    ensure_dirs()
    env_file = ROOT / ".env"
    env_example = ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        print("已创建 .env，请填写 KB_API_KEY 后再构建。")
    print("初始化完成。把 Markdown 原始笔记放入 raw/notes/，或用 kb.py add 写入 raw/ai/，然后运行 python kb.py build-all。")
    return 0


def build_wiki(args: argparse.Namespace) -> int:
    cmd = [PYTHON, str(SCRIPTS / "auto_wiki_writer.py")]
    if args.force:
        cmd.append("--force")
    if args.dry_run:
        cmd.append("--dry-run")
    for raw_dir in args.raw_dir or []:
        cmd.extend(["--raw-dir", raw_dir])
    return run(cmd)


def prepare_docs(_args: argparse.Namespace) -> int:
    return run([PYTHON, str(SCRIPTS / "prepare_wiki_docs.py")])


def ingest(args: argparse.Namespace) -> int:
    return run([PYTHON, str(SCRIPTS / "ingest_md.py"), "--source", args.source, "--persist", args.persist])


def rebuild(args: argparse.Namespace) -> int:
    return run([PYTHON, str(SCRIPTS / "rebuild_vectordb.py"), "--source", args.source, "--persist", args.persist])


def build_all(args: argparse.Namespace) -> int:
    ensure_dirs()
    code = build_wiki(args)
    if code:
        return code
    if args.dry_run:
        print("dry-run 模式已结束，未继续同步 build/docs 或构建向量库。")
        return 0
    code = prepare_docs(args)
    if code:
        return code
    return ingest(args)


def query(args: argparse.Namespace) -> int:
    return run([PYTHON, str(SCRIPTS / "query_md.py"), args.query, "-k", str(args.top_k), "-p", args.persist])


def chat(args: argparse.Namespace) -> int:
    return run(
        [
            PYTHON,
            str(SCRIPTS / "chat_with_kb.py"),
            args.query,
            "-k",
            str(args.top_k),
            "-p",
            args.persist,
            "-m",
            args.model,
        ]
    )


def add(args: argparse.Namespace) -> int:
    cmd = [PYTHON, str(SCRIPTS / "add_to_kb.py"), args.content]
    if args.title:
        cmd.extend(["-t", args.title])
    if args.category:
        cmd.extend(["-c", args.category])
    if args.also_vector:
        cmd.append("--also-vector")
    return run(cmd)


def serve(args: argparse.Namespace) -> int:
    ensure_dirs()
    code = prepare_docs(args)
    if code:
        return code
    return run(["mkdocs", "serve", "-a", args.address])


def main() -> int:
    parser = argparse.ArgumentParser(description="Knowledge Base Wiki command line")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="初始化目录和 .env").set_defaults(func=init_project)

    p = subparsers.add_parser("build-wiki", help="从 raw/notes 和 raw/ai 生成 wiki/ 知识图谱层")
    p.add_argument("--force", action="store_true", help="忽略状态文件，重新处理所有笔记")
    p.add_argument("--dry-run", action="store_true", help="只预览，不写入文件")
    p.add_argument("--raw-dir", action="append", help="额外指定原始笔记目录，可重复传入")
    p.set_defaults(func=build_wiki)

    subparsers.add_parser("prepare-docs", help="同步 wiki/ 页面到 build/docs/").set_defaults(func=prepare_docs)

    p = subparsers.add_parser("ingest", help="构建向量库到 build/chroma_db/")
    p.add_argument("--source", "-s", default=DEFAULT_DOCS)
    p.add_argument("--persist", "-p", default=DEFAULT_VECTOR_DB)
    p.set_defaults(func=ingest)

    p = subparsers.add_parser("rebuild", help="删除并重建向量库")
    p.add_argument("--source", "-s", default=DEFAULT_DOCS)
    p.add_argument("--persist", "-p", default=DEFAULT_VECTOR_DB)
    p.set_defaults(func=rebuild)

    p = subparsers.add_parser("build-all", help="一键生成 wiki/、同步 build/docs 并构建向量库")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--raw-dir", action="append")
    p.add_argument("--source", "-s", default=DEFAULT_DOCS)
    p.add_argument("--persist", "-p", default=DEFAULT_VECTOR_DB)
    p.set_defaults(func=build_all)

    p = subparsers.add_parser("query", help="语义检索")
    p.add_argument("query")
    p.add_argument("-k", "--top-k", type=int, default=3)
    p.add_argument("-p", "--persist", default=DEFAULT_VECTOR_DB)
    p.set_defaults(func=query)

    p = subparsers.add_parser("chat", help="基于知识库问答")
    p.add_argument("query")
    p.add_argument("-k", "--top-k", type=int, default=3)
    p.add_argument("-p", "--persist", default=DEFAULT_VECTOR_DB)
    p.add_argument("-m", "--model", default=os.getenv("KB_LLM_MODEL", os.getenv("WIKI_LLM_MODEL", "qwen-plus")))
    p.set_defaults(func=chat)

    p = subparsers.add_parser("add", help="追加一条原始笔记到 raw/ai")
    p.add_argument("content")
    p.add_argument("-t", "--title")
    p.add_argument("-c", "--category")
    p.add_argument("--also-vector", action="store_true", help="同时写入当前向量库")
    p.set_defaults(func=add)

    p = subparsers.add_parser("serve", help="启动 MkDocs Wiki")
    p.add_argument("-a", "--address", default="127.0.0.1:8000")
    p.set_defaults(func=serve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
