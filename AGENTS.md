# AGENTS.md

本文件是给 Codex、Claude Code、OpenCode 等 AI 编程/知识库 agent 使用的项目操作说明。进入本仓库后，优先遵守这里的约定。

## 项目定位

这是一个开箱即用的 Markdown 知识库模板，用于把原始笔记整理成结构化 Wiki，并构建本地向量库用于检索和 RAG 问答。

核心链路：

```text
raw/notes/*.md
  -> auto_wiki_writer.py
  -> concepts/ entities/ comparisons/ index.md log.md
  -> prepare_wiki_docs.py
  -> docs/
  -> ingest_md.py
  -> chroma_db/
  -> query_md.py / chat_with_kb.py
```

统一入口是：

```bash
python kb.py
```

## 目录约定

- `raw/notes/`：外部用户放入的原始 Markdown 笔记。
- `raw/ai/`：`python kb.py add ...` 写入的补充笔记。
- `raw/mubu/`：兼容旧的幕布导出笔记目录。
- `concepts/`：AI 生成的概念页。
- `entities/`：AI 生成的实体页。
- `comparisons/`：AI 生成的比较页。
- `docs/`：MkDocs 使用的构建源目录，由 `prepare_wiki_docs.py` 生成。
- `chroma_db/`：ChromaDB 本地向量库。
- `index.md`：自动生成的 Wiki 索引。
- `log.md`：自动生成的操作日志。
- `.wiki_state.json`：自动生成的增量构建状态。

以下内容默认属于用户私有或生成物，不应提交到 Git：

- `.env`
- `raw/`
- `docs/`
- `site/`
- `concepts/`
- `entities/`
- `comparisons/`
- `chroma_db/`
- `index.md`
- `log.md`
- `.wiki_state.json`

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
KB_LLM_MODEL=qwen-plus
KB_EMBEDDING_MODEL=text-embedding-v3
WIKI_RAW_DIRS=raw/notes;raw/ai;raw/mubu
```

兼容旧变量：

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `WIKI_LLM_MODEL`

不要把 `.env` 或任何真实 API key 写入提交、文档示例或日志。

## 修改代码时的规则

- 优先保持 `kb.py` 作为唯一用户入口；新增功能时尽量先接入 `kb.py` 子命令。
- 不要让普通用户必须记住多个底层脚本的执行顺序。
- 保持 `auto_wiki_writer.py`、`prepare_wiki_docs.py`、`ingest_md.py` 可单独运行，方便自动化调用。
- 修改默认目录时必须兼容 `raw/notes`、`raw/ai`、`raw/mubu`。
- 修改模型配置时必须继续兼容 `KB_*` 变量。
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

旧自动化仍可直接调用：

```bash
python auto_wiki_writer.py
python prepare_wiki_docs.py
python ingest_md.py
```

但新功能应优先通过 `kb.py` 暴露。

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
python -m py_compile kb.py auto_wiki_writer.py ingest_md.py query_md.py chat_with_kb.py add_to_kb.py prepare_wiki_docs.py rebuild_vectordb.py
python kb.py --help
python auto_wiki_writer.py --dry-run --file readme.md
python prepare_wiki_docs.py
git diff --check
```

不要在没有用户同意时运行会大规模调用模型 API、扫描私有原始笔记或重建大型向量库的命令。

## 对外发布定位

本项目应定位为轻量、可控、本地化的 Markdown Wiki + RAG 知识库模板。

它不是完整的多 agent 研究平台。若要增强，可优先考虑：

- topic wiki 多主题隔离
- inbox 待整理区
- compile / lint / audit 阶段
- quick / standard / deep 查询模式
- 双链接输出：`[[wikilink]]` + 标准 Markdown 链接
- confidence 和更强来源追溯
