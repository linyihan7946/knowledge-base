import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"
CONCEPTS_DIR = WIKI_DIR / "concepts"
ENTITIES_DIR = WIKI_DIR / "entities"
COMPARISONS_DIR = WIKI_DIR / "comparisons"
INDEX_FILE = WIKI_DIR / "index.md"
LOG_FILE = WIKI_DIR / "log.md"
STATE_FILE = WIKI_DIR / ".wiki_state.json"

DEFAULT_RAW_DIRS = ["raw/notes", "raw/ai"]
LLM_MODEL = os.getenv("KB_LLM_MODEL", os.getenv("WIKI_LLM_MODEL", "qwen-plus"))
MAX_INPUT_CHARS = int(os.getenv("WIKI_MAX_INPUT_CHARS", "12000"))
MAX_TOKENS = int(os.getenv("WIKI_MAX_TOKENS", "8000"))


def env_raw_dirs() -> list[Path]:
    value = os.getenv("WIKI_RAW_DIRS")
    raw_dirs = value.split(";") if value else DEFAULT_RAW_DIRS
    return [resolve_path(item) for item in raw_dirs if item.strip()]


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def relative_to_root(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def ensure_dirs(raw_dirs: list[Path]) -> None:
    for directory in [*raw_dirs, CONCEPTS_DIR, ENTITIES_DIR, COMPARISONS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("# 构建日志\n\n", encoding="utf-8")


def compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_state() -> dict[str, str]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8-sig"))
    return {}


def save_state(state: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def read_raw_file(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content.strip()


def iter_raw_files(raw_dirs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for raw_dir in raw_dirs:
        if raw_dir.exists():
            files.extend(raw_dir.rglob("*.md"))
    return sorted(set(files), key=lambda path: path.as_posix())


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]", "-", title.strip().lower())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or datetime.now().strftime("%Y%m%d-%H%M%S")


def api_key() -> str | None:
    return os.getenv("KB_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")


def base_url() -> str | None:
    return os.getenv("KB_BASE_URL") or os.getenv("DASHSCOPE_BASE_URL") or os.getenv("OPENAI_BASE_URL")


def extract_json(text: str) -> list[dict]:
    match = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            text = match.group(0)
    data = json.loads(text)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def call_llm_extract(content: str, source_file: str, dry_run: bool = False) -> list[dict]:
    if dry_run:
        return [
            {
                "type": "concept",
                "title": "示例概念",
                "slug": "example-concept",
                "tags": ["note"],
                "sources": [source_file],
                "content": "---\ntitle: 示例概念\ncreated: 2026-01-01\nupdated: 2026-01-01\ntype: concept\ntags: [note]\nsources: [\"raw/notes/example.md\"]\n---\n\n# 示例概念\n\n这是 dry-run 示例。",
            }
        ]

    today = datetime.now().strftime("%Y-%m-%d")
    system_prompt = f"""你是一个知识库整理助手。请从原始 Markdown 笔记中提取值得独立成页的概念、实体或比较页。

要求：
1. 返回 JSON 数组，不要返回 Markdown 代码块之外的解释。
2. 每个对象包含 type、title、slug、tags、sources、content。
3. type 只能是 concept、entity、comparison。
4. content 必须是完整 Markdown，并以 YAML frontmatter 开头。
5. sources 必须包含当前来源：{source_file}
6. 页面内容要可读、可追溯，并使用 [[wikilinks]] 连接相关主题。
7. 如果内容太短或没有整理价值，返回空数组 []。

frontmatter 示例：
---
title: 页面标题
created: {today}
updated: {today}
type: concept
tags: [note]
sources: ["{source_file}"]
---
"""
    user_prompt = f"""来源文件：{source_file}

原始笔记：

{content[:MAX_INPUT_CHARS]}
"""

    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=api_key(),
        base_url=base_url(),
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    return extract_json(str(response.content))


def page_dir(page_type: str) -> Path:
    if page_type == "entity":
        return ENTITIES_DIR
    if page_type == "comparison":
        return COMPARISONS_DIR
    return CONCEPTS_DIR


def normalize_page(page: dict, source_file: str) -> dict:
    page_type = page.get("type") if page.get("type") in {"concept", "entity", "comparison"} else "concept"
    title = str(page.get("title") or "Untitled")
    slug = str(page.get("slug") or slugify(title)).replace("/", "-").replace("\\", "-")
    content = str(page.get("content") or "").strip()
    if not content:
        today = datetime.now().strftime("%Y-%m-%d")
        tags = page.get("tags") or ["note"]
        content = (
            "---\n"
            f"title: {title}\n"
            f"created: {today}\n"
            f"updated: {today}\n"
            f"type: {page_type}\n"
            f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
            f"sources: [\"{source_file}\"]\n"
            "---\n\n"
            f"# {title}\n\n"
        )
    return {"type": page_type, "title": title, "slug": slug, "content": content}


def write_wiki_page(page: dict, source_file: str) -> Path:
    normalized = normalize_page(page, source_file)
    target = page_dir(normalized["type"]) / f"{normalized['slug']}.md"
    target.write_text(normalized["content"].rstrip() + "\n", encoding="utf-8")
    return target


def update_index() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Knowledge Base Wiki",
        "",
        f"最后更新：{today}",
        "",
        "## Concepts",
        "",
    ]
    for path in sorted(CONCEPTS_DIR.glob("*.md")):
        lines.append(f"- [[{path.stem}]]")
    lines.extend(["", "## Entities", ""])
    for path in sorted(ENTITIES_DIR.glob("*.md")):
        lines.append(f"- [[{path.stem}]]")
    lines.extend(["", "## Comparisons", ""])
    for path in sorted(COMPARISONS_DIR.glob("*.md")):
        lines.append(f"- [[{path.stem}]]")
    INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_log(message: str) -> None:
    if not LOG_FILE.exists():
        LOG_FILE.write_text("# 构建日志\n\n", encoding="utf-8")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(f"- [{timestamp}] {message}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="从原始 Markdown 笔记生成结构化 Wiki")
    parser.add_argument("--dry-run", action="store_true", help="预览处理结果，不写入文件")
    parser.add_argument("--file", help="只处理指定 Markdown 文件")
    parser.add_argument("--force", action="store_true", help="忽略状态文件，重新处理所有笔记")
    parser.add_argument("--raw-dir", action="append", help="额外指定原始笔记目录，可重复传入")
    args = parser.parse_args()

    raw_dirs = env_raw_dirs()
    if args.raw_dir:
        raw_dirs.extend(resolve_path(path) for path in args.raw_dir)
    ensure_dirs(raw_dirs)

    state = {} if args.force else load_state()
    raw_files = [resolve_path(args.file)] if args.file else iter_raw_files(raw_dirs)

    if not raw_files:
        print("未找到原始 Markdown 笔记。请把文件放入 raw/notes/，或用 kb.py add 写入 raw/ai/ 后重试。")
        return 0

    print(f"找到 {len(raw_files)} 个原始笔记。")
    processed_count = 0
    page_count = 0

    for raw_file in raw_files:
        if not raw_file.exists():
            print(f"跳过不存在的文件：{raw_file}")
            continue

        rel_path = relative_to_root(raw_file)
        current_sha = compute_sha256(raw_file)
        if not args.force and state.get(rel_path) == current_sha:
            continue

        content = read_raw_file(raw_file)
        if len(content) < 100:
            print(f"跳过短笔记：{rel_path}")
            if not args.dry_run:
                state[rel_path] = current_sha
                update_log(f"跳过短笔记：{rel_path}")
            continue

        print(f"处理：{rel_path}")
        try:
            pages = call_llm_extract(content, rel_path, dry_run=args.dry_run)
        except Exception as exc:
            print(f"处理失败：{rel_path}，原因：{exc}")
            continue

        if not pages:
            print(f"未提取到页面：{rel_path}")
            if not args.dry_run:
                state[rel_path] = current_sha
                update_log(f"未提取到页面：{rel_path}")
            continue

        print(f"提取 {len(pages)} 个页面。")
        if not args.dry_run:
            for page in pages:
                target = write_wiki_page(page, rel_path)
                print(f"  写入：{relative_to_root(target)}")
                page_count += 1
            state[rel_path] = current_sha
            update_log(f"整理笔记：{rel_path} -> {len(pages)} 个页面")
        processed_count += 1

    if not args.dry_run:
        save_state(state)
        update_index()

    print(f"完成：处理 {processed_count} 个文件，生成/更新 {page_count} 个页面。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
