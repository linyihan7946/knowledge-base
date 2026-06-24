# Markdown 知识库向量化检索工具 (Knowledge Base)

这是一个基于 LangChain、ChromaDB 和阿里云百炼 (DashScope) 提供的 `text-embedding-v3` 模型构建的 Markdown 知识库本地化向量搜索引擎。该项目可将 `docs` 目录下的所有 Markdown 笔记文件按语义分块向量化入库，并提供高精度的语义搜索查询。

**主要特性：**
- **智能分块**：针对 Markdown 语法（`MarkdownTextSplitter`）进行语义切片（Chunk Size: 1500，Overlap: 200）。
- **高性能 Embedding**：集成阿里云百炼 `text-embedding-v3` API（OpenAI 兼容协议），在实现高精度语义理解的同时自动处理 `chunk_size` 限制与 Token 长度安全检查。
- **本地向量数据库**：采用 ChromaDB 构建无需安装服务端进程的轻量级本地向量库（默认存至 `./chroma_db`）。
- **跨平台兼容**：对 Windows 中文控制台编码进行完美适配，避免控制台乱码。

---

## 🚀 快速开始

### 1. 环境准备与依赖安装

请确保已安装 Python 3.8 或更高版本。

由于本项目暂无 `requirements.txt`，请手动安装以下核心依赖库：

```bash
pip install langchain langchain-openai langchain-community langchain-text-splitters chromadb unstructured python-dotenv
```

### 2. 配置环境变量

在项目根目录下创建一个 `.env` 文件，并配置你的阿里云百炼 API 密钥和网关地址：

```env
# .env 文件
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 3. 将笔记文件放入目录

将你所有的 Markdown 笔记文件放入根目录的 `docs/` 文件夹下。

---

## 🛠️ 使用指南

### 1. 向量化入库（全量构建/更新）

如果 `docs/` 目录下的 Markdown 文件有更新或新增，你需要运行 `ingest_md.py` 对它们进行全量向量化入库。

```bash
# 默认用法（读取 ./docs 目录，存入 ./chroma_db 目录）
python ingest_md.py

# 指定自定义目录
python ingest_md.py --source ./my_custom_docs --persist ./my_custom_db
```
*注：脚本内置了针对百炼 API 批量上传的限制保护，每次批量 Embedding 上限为 10 条块。*

### 2. 重建向量库

如果你希望强制清空现有的 ChromaDB 并完全重新从头构建知识库，可以使用 `rebuild_vectordb.py` 脚本：

```bash
python rebuild_vectordb.py
# 同样支持 --source 和 --persist 参数
```

### 3. 单条碎片知识录入

如果你不想新建 `.md` 文件，仅仅是随手记录一段短文本并想要入库，可以使用 `add_to_kb.py`：

```bash
python add_to_kb.py "今天在惠城鱼仔吃了好吃的卤水猪脚" -t "餐厅打卡" -c "随笔"
```

### 4. 语义查询

利用 `query_md.py` 进行终端命令行搜索，基于你提出的问题，查询最高相似度的 `k` 个文本块（默认返回前 3 个相关结果）：

```bash
# 基本查询
python query_md.py "推荐一些广州好吃的餐厅"

# 自定义返回数量与指定数据库路径
python query_md.py "林文捷的工作是什么" -k 5 -p ./chroma_db
```

### 5. LLM 问答（RAG 对话）

利用 `chat_with_kb.py` 进行基于知识库的 AI 问答。系统会先检索相关文档，然后让 LLM 基于检索结果生成自然语言回答：

```bash
# 基本问答
python chat_with_kb.py "我的笔记里关于 Python 学习有什么建议？"

# 自定义检索数量和模型
python chat_with_kb.py "如何保持健康？" -k 5 -m qwen-turbo

# 可选模型：qwen-turbo（更快更便宜）/ qwen-plus（质量更高）/ qwen-max（最强）
```

### 6. Wiki 知识库浏览界面

双击运行 `start_wiki.bat` 或在终端执行以下命令启动 Wiki 浏览界面：

```bash
# 首次运行需安装 MkDocs
pip install mkdocs mkdocs-material

# 同步 AI 整理后的 index.md、concepts/、entities/ 到 MkDocs 文档目录
python prepare_wiki_docs.py

# 启动 Wiki 服务
mkdocs serve -a 127.0.0.1:8000
```

然后在浏览器中打开 `http://127.0.0.1:8000` 即可浏览和搜索知识库。`start_wiki.bat` 会自动执行同步并打开浏览器。

### 7. 自动 Wiki 整理（AI 驱动）

利用 `auto_wiki_writer.py` 自动从原始笔记中提取概念和实体，生成结构化的 Wiki 页面：

```bash
# 全量整理（增量模式，只处理新增/修改的笔记）
python auto_wiki_writer.py

# 模拟运行（不实际写入文件）
python auto_wiki_writer.py --dry-run

# 只处理单个文件
python auto_wiki_writer.py --file "raw/mubu/AI/AI：ChatGPT.md"

# 强制重新处理所有文件
python auto_wiki_writer.py --force
```

**工作原理：**
1. 扫描 `raw/mubu/` 下的所有 `.md` 笔记
2. 计算 SHA256 检测文件是否修改（增量更新）
3. 调用 LLM 提取核心概念/实体
4. 按 `SCHEMA.md` 规范生成 `concepts/*.md` 和 `entities/*.md`
5. 自动更新 `index.md` 索引和 `log.md` 操作日志

**效果：** 随着笔记积累，AI 生成的 Wiki 会越来越完整，检索准确率也会越来越高。

---

## 📁 目录结构

```text
knowledge-base/
├── docs/                   # 存放需要被向量化的 Markdown 笔记原文件
├── raw/                    # 原始文档（只读，从幕布下载）
│   └── mubu/               # 幕布文档原始 Markdown 文件
├── concepts/               # AI 生成的概念页面（按 Wiki 规范整理）
├── entities/               # AI 生成的实体页面（按 Wiki 规范整理）
├── comparisons/            # AI 生成的比较页面
├── chroma_db/              # ChromaDB 向量数据库持久化保存目录（自动生成）
├── .env                    # 环境变量配置文件（需手动创建）
├── .wiki_state.json        # AI 整理状态文件（记录已处理的文件 SHA256）
├── index.md                # Wiki 索引页面（自动生成）
├── SCHEMA.md               # Wiki 规范文档
├── log.md                  # 操作日志
├── ingest_md.py            # 核心脚本：读取并向量化 docs 下所有 .md 文件
├── query_md.py             # 核心脚本：执行自然语言相似度查询
├── chat_with_kb.py         # LLM 问答脚本（RAG 对话）
├── auto_wiki_writer.py     # 新增：AI 自动 Wiki 整理脚本
├── add_to_kb.py            # 工具脚本：直接将单段纯文本添加进知识库
├── rebuild_vectordb.py     # 工具脚本：清理旧库并全量重新构建
├── mkdocs.yml              # MkDocs Wiki 界面配置
├── start_wiki.bat          # Wiki 服务启动脚本（Windows）
└── readme.md               # 本项目说明文档
```

---
## 💡 开发 / Skill 设计参考 (For OpenClaw)

对于后续编写 `OpenClaw` 智能体 Skill 配置，请参考以下行为逻辑：

- **触发意图 1（检索）**: 当用户表达"帮我查一下关于XXX的笔记"、"检索知识库"等意图时，可调用 `python query_md.py "<query>"`。注意要对返回的 `--- 结果 N ---` 等格式化内容进行阅读理解和二次总结后，再以人类自然语言回复给终端用户。
- **触发意图 2（构建更新）**: 当用户要求"更新知识库"、"向量化最新笔记"时，可调用 `python ingest_md.py`。
- **触发意图 3（清空重建）**: 当用户要求"清空知识库"、"重建向量库"时，可调用 `python rebuild_vectordb.py`。
- **触发意图 4（碎片记忆）**: 当用户要求"帮我记下来..."且为短文本片语时，可调用 `python add_to_kb.py "<content>" -t "<title>"`。
- **触发意图 5（LLM 问答）**: 当用户要求"帮我问问知识库"、"基于笔记回答"等意图时，可调用 `python chat_with_kb.py "<query>"`。系统会自动检索相关文档并让 LLM 生成回答。
- **触发意图 6（Wiki 浏览）**: 当用户要求"打开 Wiki"、"浏览知识库"时，可指导用户运行 `start_wiki.bat` 或 `mkdocs serve`。
