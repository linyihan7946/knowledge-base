# Knowledge Base Wiki

一个开箱即用的 Markdown 知识库模板。原始笔记放在 `raw/notes` 或 `raw/ai`，结构化知识图谱放在 `wiki/`，MkDocs 和向量库等构建产物放在 `build/`。

你可以用它完成：

- 从原始 Markdown 笔记生成 Wiki 知识图谱
- 用 MkDocs 浏览 Wiki
- 用 ChromaDB 构建本地向量库
- 基于知识库做语义检索和 RAG 问答
- 随手追加笔记，并进入下一轮知识图谱构建

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置模型

复制 `.env.example` 为 `.env`，填入你的 OpenAI-compatible API 信息：

```env
KB_API_KEY=your_api_key
KB_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
KB_LLM_MODEL=qwen-plus
KB_EMBEDDING_MODEL=text-embedding-v3
WIKI_RAW_DIRS=raw/notes;raw/ai
```

### 3. 初始化目录

```bash
python kb.py init
```

把 Markdown 原始笔记放到：

```text
raw/notes/
```

用命令追加的补充笔记会写入：

```text
raw/ai/
```

### 4. 一键构建

```bash
python kb.py build-all
```

这条命令会依次执行：

1. 从 `raw/notes`、`raw/ai` 生成 `wiki/` 知识图谱层
2. 同步到 `build/docs`
3. 构建本地向量库 `build/chroma_db`

### 5. 问答

```bash
python kb.py chat "我的笔记里关于 AI 编程有什么建议？"
```

### 6. 打开 Wiki

```bash
python kb.py serve
```

浏览器打开 `http://127.0.0.1:8000`。

Windows 也可以双击 `start_wiki.bat`。

## 常用命令

```bash
python kb.py init
python kb.py build-wiki
python kb.py prepare-docs
python kb.py ingest
python kb.py build-all
python kb.py query "搜索关键词"
python kb.py chat "基于知识库回答问题"
python kb.py add "一段新笔记" -t "标题" -c "分类"
python kb.py rebuild
python kb.py serve
```

## 目录说明

```text
knowledge-base/
  kb.py                 # 统一入口
  scripts/              # 底层脚本
  raw/
    notes/              # 原始 Markdown 笔记
    ai/                 # kb.py add 写入的补充笔记
  wiki/
    concepts/           # AI 生成的概念页
    entities/           # AI 生成的实体页
    comparisons/        # AI 生成的比较页
    index.md            # 自动生成的 Wiki 索引
    log.md              # 自动生成的构建日志
    .wiki_state.json    # 自动生成的增量构建状态
  build/
    docs/               # MkDocs 构建源目录
    site/               # MkDocs 静态站点输出
    chroma_db/          # ChromaDB 本地向量库
```

`raw/`、`wiki/`、`build/` 默认被 `.gitignore` 忽略，避免把个人笔记、生成知识图谱和向量库提交到公开仓库。

## 支持的原始资料

当前开箱即用支持 Markdown：`*.md`。

如果你有 PDF、网页、视频、Excel、幕布导出等资料，建议先转换成 Markdown，再放入 `raw/notes`。转换后的 Markdown 越清晰，Wiki 层和问答效果越好。

## 构建流程

```text
raw/notes/*.md + raw/ai/*.md
  -> scripts/auto_wiki_writer.py
  -> wiki/concepts / wiki/entities / wiki/comparisons / wiki/index.md / wiki/log.md
  -> scripts/prepare_wiki_docs.py
  -> build/docs/
  -> scripts/ingest_md.py
  -> build/chroma_db/
  -> scripts/query_md.py / scripts/chat_with_kb.py
```

## 配置项

`.env` 支持：

```env
KB_API_KEY=your_api_key
KB_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
KB_LLM_MODEL=qwen-plus
KB_EMBEDDING_MODEL=text-embedding-v3
WIKI_RAW_DIRS=raw/notes;raw/ai
```

兼容旧变量名：

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `WIKI_LLM_MODEL`

## 发布成通用模板时的建议

发布前保持以下目录和文件不提交：

- `.env`
- `raw/`
- `wiki/`
- `build/`

这样外部用户 clone 后，运行 `python kb.py init` 就能得到自己的空知识库。
