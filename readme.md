# Markdown 知识库向量化工具

将 docs 目录下的 Markdown 文件向量化入库，支持语义搜索查询。

## 功能

- 递归加载 docs 目录下所有 `.md` 文件
- 使用 ChromaDB 进行向量存储
- 支持 UTF-8 编码和 Windows 兼容
- 支持离线模式（使用本地缓存的模型）

## 使用方法

### 1. 向量化入库

```bash
# 基本用法（离线模式，使用 docs 目录）
python ingest_md.py

# 指定目录
python ingest_md.py --source ./my_docs --persist ./my_db

# 在线模式（允许下载模型）
python ingest_md.py --online
```

### 2. 查询知识库

```bash
# 单次查询
python query_md.py "你的问题"
python query_md.py "如何使用 threejs" -k 5

# 交互模式
python query_md.py -i

# 在线模式
python query_md.py "你的问题" --online
```

### 参数说明

**ingest_md.py**
- `--source, -s`: Markdown 文件目录（默认: ./docs）
- `--persist, -p`: 向量库保存目录（默认: ./chroma_db）
- `--online`: 在线模式（允许网络请求下载模型）

**query_md.py**
- `query`: 查询内容
- `-k, --top-k`: 返回结果数量（默认: 5）
- `-i, --interactive`: 交互模式
- `--online`: 在线模式

## 目录结构

```
.
├── docs/           # Markdown 文件目录
│   ├── AI/
│   ├── 工作/
│   └── ...
├── chroma_db/      # 向量数据库
├── ingest_md.py    # 入库脚本
└── query_md.py     # 查询脚本
```

## 依赖

- langchain
- langchain-huggingface
- langchain-community
- chromadb
- sentence-transformers
