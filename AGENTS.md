# AGENTS.md

本文件是给 Codex、Claude Code、OpenCode、Hermes 等 AI agent 使用的项目操作说明。进入本仓库后，优先遵守这里的约定。

## 项目定位

这是一个轻量、可控、本地化的 Markdown Wiki + RAG 知识库模板。原始资料保存在 `raw/`，AI 编译出的知识图谱保存在 `wiki/`，构建产物保存在 `build/`。

核心链路：

```text
raw/notes/*.md + raw/ai/*.md
  -> scripts/auto_wiki_writer.py
  -> wiki/concepts/ wiki/entities/ wiki/comparisons/ wiki/index.md wiki/log.md
  -> scripts/prepare_wiki_docs.py
  -> build/docs/
  -> scripts/ingest_md.py
  -> build/chroma_db/
  -> scripts/query_md.py / scripts/chat_with_kb.py
```

统一入口是：

```bash
python kb.py
```

## 目录约定

- `raw/notes/`：原始 Markdown 笔记，通常来自幕布或外部资料转换。
- `raw/ai/`：`python kb.py add ...` 写入的补充笔记。
- `wiki/concepts/`：AI 生成的概念页。
- `wiki/entities/`：AI 生成的实体页。
- `wiki/comparisons/`：AI 生成的比较页。
- `wiki/index.md`：自动生成的 Wiki 索引。
- `wiki/log.md`：自动生成的操作日志。
- `wiki/.wiki_state.json`：自动生成的增量构建状态。
- `build/docs/`：MkDocs 使用的构建源目录，由 `scripts/prepare_wiki_docs.py` 生成。
- `build/site/`：MkDocs 静态站点输出。
- `build/chroma_db/`：ChromaDB 本地向量库。
- `build/models/`：本地模型缓存目录。当前默认流程主要使用 OpenAI-compatible / DashScope 云端 embedding，不一定依赖本地模型；如果机器上已有本地模型缓存，应放在这里而不是根目录。
- `scripts/`：底层实现脚本。普通用户优先使用 `kb.py`，不要直接记忆脚本顺序。

以下内容默认属于用户私有或生成物，不应提交到 Git：

- `.env`
- `raw/`
- `wiki/`
- `build/`

## build/ 与 wiki/ 的关系

`build/` 是构建产物目录，可以理解成“机器生成、随时可删、可重新生成”的缓存区。

`wiki/` 才是 AI 整理后的知识图谱源文件。`build/docs/` 是给 MkDocs 使用的浏览副本，由 `scripts/prepare_wiki_docs.py` 从 `wiki/` 复制和转换而来。

因此：

- 不要手动编辑 `build/docs/`，需要改 Wiki 内容时改 `wiki/` 或重新运行 `python kb.py build-wiki`。
- `build/docs/` 看起来和 `wiki/` 很像是正常现象，因为它是 MkDocs 可浏览版本。
- `build/docs/` 里会把 `[[wikilinks]]` 转换为普通 Markdown 链接。
- `build/docs/`、`build/site/`、`build/chroma_db/`、`build/models/` 都可以视为生成物或缓存，不应提交到 Git。
- 如果 `build/docs/` 混入大量 `raw/` 原始笔记，而不是 `wiki/` 页面副本，通常是旧结构迁移遗留，应清空 `build/docs/` 后运行 `python kb.py prepare-docs` 重建。

推荐心智模型：

```text
raw/      # 原始资料
wiki/     # AI 整理后的知识图谱源文件
build/    # 给 MkDocs、ChromaDB、本地模型缓存使用的生成物
```

## 常用命令

初始化目录和 `.env`：

```bash
python kb.py init
```

只刷新 Wiki 知识图谱层：

```bash
python kb.py build-wiki
```

完整刷新 Wiki、MkDocs 文档和向量库：

```bash
python kb.py build-all
```

同步 Wiki 到 MkDocs 文档目录：

```bash
python kb.py prepare-docs
```

只构建向量库：

```bash
python kb.py ingest
```

删除并重建向量库：

```bash
python kb.py rebuild
```

语义检索：

```bash
python kb.py query "搜索问题"
```

RAG 问答：

```bash
python kb.py chat "基于知识库回答问题"
```

追加一条原始补充笔记：

```bash
python kb.py add "笔记内容" -t "标题" -c "分类"
```

启动 Wiki：

```bash
python kb.py serve
```

## 配置约定

复制 `.env.example` 为 `.env`，优先使用这些变量：

```env
KB_API_KEY=your_api_key
KB_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
KB_LLM_MODEL=qwen3.6-plus
KB_EMBEDDING_MODEL=text-embedding-v3
WIKI_RAW_DIRS=raw/notes;raw/ai
```

兼容旧变量：

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `WIKI_LLM_MODEL`

不要把 `.env` 或任何真实 API key 写入提交、文档示例或日志。

## Hermes / 自动化调用

外部自动化、Hermes、Claude 权限 allowlist 和其他 agent 调用应优先使用 `kb.py`：

```bash
python kb.py build-wiki
python kb.py build-all
python kb.py ingest
python kb.py query "搜索问题"
python kb.py chat "问题"
```

如果必须直接调用底层脚本，请使用新路径：

```bash
python scripts/auto_wiki_writer.py
python scripts/prepare_wiki_docs.py
python scripts/ingest_md.py --source ./build/docs --persist ./build/chroma_db
python scripts/query_md.py "搜索问题" -p ./build/chroma_db
python scripts/chat_with_kb.py "问题" -p ./build/chroma_db
```

旧路径 `python ingest_md.py`、`python query_md.py` 等不再作为推荐调用方式。

## 修改代码时的规则

- 优先保持 `kb.py` 作为唯一用户入口；新增功能时先接入 `kb.py` 子命令。
- 保持 `scripts/*.py` 可单独运行，方便自动化调用。
- 默认原始目录必须兼容 `raw/notes` 和 `raw/ai`。
- 生成的知识图谱必须写入 `wiki/`。
- MkDocs 文档、静态站点和向量库必须写入 `build/`。
- 生成内容、私有笔记、向量库和站点构建产物不得纳入 Git 跟踪。
- 对 Windows 终端输出保持 UTF-8 兼容；脚本里需要时使用 `sys.stdout.reconfigure(encoding="utf-8")`。
- 不要在脚本中硬编码个人路径、个人 API key、个人知识库内容或固定用户姓名。

## 刷新知识图谱自动化

推荐自动化使用：

```bash
python kb.py build-all
```

如果自动化只需要刷新 Wiki 层，不需要更新向量库，使用：

```bash
python kb.py build-wiki
```

## Wiki 内容规范

Wiki 页面遵守 `SCHEMA.md`：

- 页面类型使用 `concept`、`entity`、`comparison`。
- 页面保留 YAML frontmatter。
- 页面来源写入 `sources`。
- 相关主题使用 `[[wikilinks]]`。
- 原始笔记只读，不要修改 `raw/` 下用户放入的文件。

## 验证建议

修改脚本后至少运行：

```bash
python -m py_compile kb.py scripts/auto_wiki_writer.py scripts/ingest_md.py scripts/query_md.py scripts/chat_with_kb.py scripts/add_to_kb.py scripts/prepare_wiki_docs.py scripts/rebuild_vectordb.py
python kb.py --help
python scripts/auto_wiki_writer.py --dry-run --file readme.md
python scripts/prepare_wiki_docs.py
git diff --check
```

不要在没有用户同意时运行会大规模调用模型 API、扫描私有原始笔记或重建大型向量库的命令。
