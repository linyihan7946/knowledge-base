# Knowledge Base Wiki

一个开箱即用的个人/团队 Markdown 知识库模板。你只需要把原始笔记放进 `raw/notes`，运行一条构建命令，就可以得到：

- 结构化 Wiki 页面：概念、实体、比较页
- MkDocs 浏览站点
- ChromaDB 本地向量库
- 基于知识库的语义检索和 RAG 问答
- 随手追加笔记并进入下一轮 Wiki 构建

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
```

### 3. 初始化目录

```bash
python kb.py init
```

把 Markdown 原始笔记放到：

```text
raw/notes/
```

### 4. 一键构建

```bash
python kb.py build-all
```

这条命令会依次执行：

1. 从原始笔记生成 Wiki 层
2. 同步 MkDocs 文档目录
3. 构建本地向量库

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
  raw/notes/          # 外部用户放原始 Markdown 笔记
  raw/ai/             # kb.py add 写入的补充笔记
  concepts/           # AI 生成的概念页
  entities/           # AI 生成的实体页
  comparisons/        # AI 生成的比较页
  docs/               # MkDocs 构建源目录
  chroma_db/          # ChromaDB 本地向量库
  index.md            # 自动生成的 Wiki 索引
  log.md              # 自动生成的构建日志
  .wiki_state.json    # 自动生成的增量构建状态
```

这些目录和状态文件默认被 `.gitignore` 忽略，避免把个人笔记、向量库和生成内容提交到公开仓库。

## 支持的原始资料

当前开箱即用支持 Markdown：`*.md`。

如果你有 PDF、网页、视频、Excel、幕布导出等资料，建议先转换成 Markdown，再放入 `raw/notes`。转换后的 Markdown 越清晰，Wiki 层和问答效果越好。

## 构建流程

```text
raw/notes/*.md
  -> auto_wiki_writer.py
  -> concepts / entities / comparisons / index.md / log.md
  -> prepare_wiki_docs.py
  -> docs/
  -> ingest_md.py
  -> chroma_db/
  -> query_md.py / chat_with_kb.py
```

## 配置项

`.env` 支持：

```env
KB_API_KEY=your_api_key
KB_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
KB_LLM_MODEL=qwen-plus
KB_EMBEDDING_MODEL=text-embedding-v3
WIKI_RAW_DIRS=raw/notes;raw/ai;raw/mubu
```

兼容旧变量名：

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `WIKI_LLM_MODEL`

## 发布成通用模板时的建议

发布前保持以下文件不要提交：

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

这样外部用户 clone 后，运行 `python kb.py init` 就能得到自己的空知识库。
