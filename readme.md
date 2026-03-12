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

---

## 📁 目录结构

```text
knowledge-base/
├── docs/                   # 存放需要被向量化的 Markdown 笔记原文件
├── chroma_db/              # ChromaDB 向量数据库持久化保存目录（自动生成）
├── .env                    # 环境变量配置文件（需手动创建）
├── ingest_md.py            # 核心脚本：读取并向量化 docs 下所有 .md 文件
├── query_md.py             # 核心脚本：执行自然语言相似度查询
├── add_to_kb.py            # 工具脚本：直接将单段纯文本添加进知识库
├── rebuild_vectordb.py     # 工具脚本：清理旧库并全量重新构建
└── readme.md               # 本项目说明文档
```

---

## 💡 开发 / Skill 设计参考 (For OpenClaw)

对于后续编写 `OpenClaw` 智能体 Skill 配置，请参考以下行为逻辑：
- **触发意图 1（检索）**: 当用户表达“帮我查一下关于XXX的笔记”、“检索知识库”等意图时，可调用 `python query_md.py "<query>"`。注意要对返回的 `--- 结果 N ---` 等格式化内容进行阅读理解和二次总结后，再以人类自然语言回复给终端用户。
- **触发意图 2（构建更新）**: 当用户要求“更新知识库”、“向量化最新笔记”时，可调用 `python ingest_md.py`。
- **触发意图 3（清空重建）**: 当用户要求“清空知识库”、“重建向量库”时，可调用 `python rebuild_vectordb.py`。
- **触发意图 4（碎片记忆）**: 当用户要求“帮我记下来...”且为短文本片语时，可调用 `python add_to_kb.py "<content>" -t "<title>"`。