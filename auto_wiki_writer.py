"""
自动 Wiki 整理脚本 — 从原始笔记自动生成/更新结构化 Wiki 页面
遵循 SCHEMA.md 规范，支持增量更新
"""
import argparse
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 加载环境变量
load_dotenv()

# 配置
RAW_DIRS = [Path("raw/mubu"), Path("raw/ai")]
CONCEPTS_DIR = Path("concepts")
ENTITIES_DIR = Path("entities")
COMPARISONS_DIR = Path("comparisons")
INDEX_FILE = Path("index.md")
LOG_FILE = Path("log.md")
STATE_FILE = Path(".wiki_state.json")
LLM_MODEL = os.getenv("WIKI_LLM_MODEL", "qwen-plus")
MAX_TOKENS = 8000

# 确保目录存在
for d in [*RAW_DIRS, CONCEPTS_DIR, ENTITIES_DIR, COMPARISONS_DIR]:
    d.mkdir(exist_ok=True)


def compute_sha256(file_path: Path) -> str:
    """计算文件 SHA256"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def load_state() -> dict:
    """加载已处理的文件状态"""
    if STATE_FILE.exists():
        import json
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """保存文件状态"""
    import json
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def read_raw_file(file_path: Path) -> str:
    """读取原始笔记内容"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 移除原始 frontmatter（如果有的话）
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    return content


def raw_relative_path(file_path: Path) -> str:
    """返回用于状态记录和 sources 的仓库相对路径。"""
    file_path = Path(file_path)
    for raw_dir in RAW_DIRS:
        try:
            return (raw_dir / file_path.relative_to(raw_dir)).as_posix()
        except ValueError:
            continue

    try:
        return file_path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return file_path.as_posix()


def iter_raw_files() -> list[Path]:
    """扫描所有原始来源目录。"""
    raw_files: list[Path] = []
    for raw_dir in RAW_DIRS:
        if raw_dir.exists():
            raw_files.extend(raw_dir.rglob("*.md"))
    return sorted(raw_files, key=lambda path: path.as_posix())


def slugify(title: str) -> str:
    """将标题转为文件名格式（小写、连字符、无空格）"""
    # 保留中文，替换空格和特殊字符
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '-', title.strip().lower())
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def extract_frontmatter(content: str) -> tuple:
    """提取 YAML frontmatter，返回 (metadata_dict, body)"""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta_str = parts[1].strip()
            body = parts[2].strip()
            # 简单解析（不依赖 pyyaml）
            meta = {}
            for line in meta_str.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip()
            return meta, body
    return {}, content


def call_llm_extract(content: str, source_file: str = "", dry_run: bool = False) -> list:
    """调用 LLM 提取概念和实体"""
    if dry_run:
        print("[DRY RUN] 跳过 LLM 调用，模拟提取结果")
        return [{"type": "concept", "title": "示例概念", "content": "# 示例概念\n\n这是测试内容", "tags": ["note"]}]

    today = datetime.now().strftime("%Y-%m-%d")
    system_prompt = f"""你是一个知识库整理助手。请分析用户的原始笔记，提取出值得独立成页的概念（concept）和实体（entity）。

要求：
1. 每个提取出的页面必须包含：type（concept/entity）、title、slug（文件名）、content（完整 Markdown 内容）、tags（标签列表）、sources（来源文件路径列表）
2. content 必须以 YAML frontmatter 开头，格式如下：
   ```yaml
   ---
   title: 页面标题
   created: {today}
   updated: {today}
   type: concept  # 或 entity
   tags: [标签1, 标签2]
   sources: ["{source_file}"]
   ---
   ```
3. 遵循 Wiki 规范：使用 [[wikilinks]] 链接相关页面，每个页面至少 2 个出站链接
4. 如果笔记内容太短或只是临时记录，不要提取
5. 返回 JSON 数组，每个元素是一个页面对象

标签必须从以下体系中选择：
ai, model, architecture, training, inference, fine-tuning, deep-learning, machine-learning, neural-network, computer-vision, nlp, speech, rag, knowledge-graph, agent, image-generation, video-generation, text-to-image, llm, transformer, diffusion, programming, python, javascript, typescript, rust, c++, c#, frontend, backend, fullstack, web, threejs, webgl, webgpu, database, sql, mysql, git, docker, linux, ide, tool, framework, library, work, project, design-system, cad, bim, pointcloud, 3d, rendering, optimization, performance, architecture, team, meeting, weekly-report, health, fitness, diet, sleep, mental-health, life, food, travel, shopping, car, house, electronics, family, education, parenting, video, editing, animation, design, social-media, douyin, bilibili, ai-tool, productivity, comparison, timeline, reference, howto, note

注意：如果笔记内容涉及多个主题，请分别提取为多个页面。"""

    user_prompt = f"""请分析以下原始笔记，提取概念和实体页面：

--- 原始笔记开始 ---
{content[:8000]}  # 限制长度避免超出 token
--- 原始笔记结束 ---

返回 JSON 数组格式。"""

    import json
    max_retries = 3
    for attempt in range(max_retries):
        try:
            llm = ChatOpenAI(
                model=LLM_MODEL,
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                temperature=0.3,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            response = llm.invoke(messages)
            text = response.content

            # 提取 JSON（处理可能的 markdown 代码块包裹）
            json_match = re.search(r'```json\s*\n(.*?)\n\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    text = json_match.group(0)

            pages = json.loads(text)
            return pages if isinstance(pages, list) else [pages]
        except json.JSONDecodeError as e:
            print(f"⚠️ 第 {attempt + 1} 次尝试 JSON 解析失败: {e}")
            if attempt == max_retries - 1:
                print("⚠️ 达到最大重试次数，放弃提取")
                return []
            continue
        except Exception as e:
            print(f"⚠️ LLM 提取失败: {e}")
            return []


def write_wiki_page(page: dict, base_dir: Path = None):
    """写入 Wiki 页面"""
    page_type = page.get("type", "concept")
    title = page.get("title", "untitled")
    content = page.get("content", "")
    slug = page.get("slug", slugify(title))

    # 清理 slug 中的非法字符和路径分隔符
    slug = slug.replace("/", "-").replace("\\", "-")
    if base_dir is None:
        base_dir = CONCEPTS_DIR if page_type == "concept" else ENTITIES_DIR

    file_path = base_dir / f"{slug}.md"

    # 如果文件已存在，追加更新日志而不是覆盖
    if file_path.exists():
        print(f"  📝 更新现有页面: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            existing = f.read()
        # 更新 frontmatter 中的 updated 日期
        today = datetime.now().strftime("%Y-%m-%d")
        existing = re.sub(r'updated: \d{4}-\d{2}-\d{2}', f'updated: {today}', existing)
        # 追加新内容（如果内容不同）
        if content.strip() != existing.strip():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
    else:
        print(f"  ✨ 新建页面: {file_path}")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return file_path


def update_index():
    """更新 index.md 索引"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# 个人知识库索引",
        f"最后更新：{today}",
        "",
        "## 概念页面 (Concepts)",
        "",
    ]

    for f in sorted(CONCEPTS_DIR.glob("*.md")):
        title = f.stem.replace("-", " ").title()
        lines.append(f"- [[{f.stem}]] - {title}")

    lines.append("")
    lines.append("## 实体页面 (Entities)")
    lines.append("")

    for f in sorted(ENTITIES_DIR.glob("*.md")):
        title = f.stem.replace("-", " ").title()
        lines.append(f"- [[{f.stem}]] - {title}")

    lines.append("")
    lines.append("## 比较页面 (Comparisons)")
    lines.append("")

    for f in sorted(COMPARISONS_DIR.glob("*.md")):
        title = f.stem.replace("-", " ").title()
        lines.append(f"- [[{f.stem}]] - {title}")

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"📑 已更新索引: {INDEX_FILE}")


def update_log(message: str):
    """追加操作日志"""
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"- [{today}] {message}\n")


def main():
    parser = argparse.ArgumentParser(description="自动 Wiki 整理工具")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际写入文件")
    parser.add_argument("--file", type=str, help="只处理指定文件")
    parser.add_argument("--force", action="store_true", help="强制重新处理所有文件")
    args = parser.parse_args()

    print("=" * 60)
    print("🤖 自动 Wiki 整理工具")
    print("=" * 60)

    # 加载状态
    state = load_state()
    if args.force:
        state = {}
        print("⚡ 强制模式：清空状态，重新处理所有文件")

    # 获取所有原始文件
    if args.file:
        raw_files = [Path(args.file)]
    else:
        raw_files = iter_raw_files()

    if not raw_files:
        print("❌ 未找到任何原始笔记文件")
        return

    raw_dirs_display = ", ".join(raw_dir.as_posix() for raw_dir in RAW_DIRS)
    print(f"📂 在 {raw_dirs_display} 找到 {len(raw_files)} 个原始笔记文件")

    processed_count = 0
    new_pages_count = 0

    for raw_file in raw_files:
        rel_path = raw_relative_path(raw_file)
        current_sha = compute_sha256(raw_file)

        # 检查是否已处理且未修改
        if not args.force and rel_path in state and state[rel_path] == current_sha:
            continue

        print(f"\n📄 处理: {rel_path}")
        content = read_raw_file(raw_file)

        if len(content.strip()) < 100:
            print("  ⏭️ 内容过短，跳过")
            continue

        # 调用 LLM 提取
        pages = call_llm_extract(content, source_file=rel_path, dry_run=args.dry_run)

        if not pages:
            print("  ⏭️ 未提取到有效页面")
            continue

        print(f"  ✅ 提取到 {len(pages)} 个页面")

        for page in pages:
            if not args.dry_run:
                write_wiki_page(page)
                new_pages_count += 1

        # 更新状态
        if not args.dry_run:
            state[rel_path] = current_sha
            update_log(f"整理笔记: {rel_path} → {len(pages)} 个页面")

        processed_count += 1

    # 保存状态
    if not args.dry_run:
        save_state(state)
        update_index()

    print("\n" + "=" * 60)
    print(f"✅ 完成！处理 {processed_count} 个文件，生成/更新 {new_pages_count} 个页面")
    if args.dry_run:
        print("💡 这是模拟运行，未实际写入文件。去掉 --dry-run 参数执行实际整理。")
    print("=" * 60)


if __name__ == "__main__":
    main()
