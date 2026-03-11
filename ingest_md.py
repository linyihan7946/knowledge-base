import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import MarkdownTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def ingest_markdown(source_dir: str, persist_dir: str):
    # 1. 递归加载所有 .md 文件
    print(f"正在加载目录 {source_dir} 下的 Markdown 文件...")
    loader = DirectoryLoader(
        source_dir,
        glob="**/*.md",
        loader_cls=UnstructuredMarkdownLoader,
        show_progress=True,
    )
    documents = loader.load()
    print(f"加载完成，共计 {len(documents)} 个文件。")

    # 2. 文本分段 (针对 Markdown 优化)
    print("正在对文档进行分段...")
    text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print(f"分段完成，产生 {len(texts)} 个文本块。")

    # 3. 初始化 Embedding 模型 (使用本地开源模型)
    print("正在初始化 Embedding 模型 (sentence-transformers)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. 向量化并入库 (ChromaDB)
    print("正在生成向量并存入数据库...")
    vector_db = Chroma.from_documents(
        documents=texts, embedding=embeddings, persist_directory=persist_dir
    )

    # 5. 持久化存储
    vector_db.persist()
    print(f"处理完成！数据库已保存至: {persist_dir}")


if __name__ == "__main__":
    # 配置路径
    SOURCE_DIRECTORY = "./docs"  # 你的 MD 文件目录
    PERSIST_DIRECTORY = "./chroma_db"  # 向量库保存目录

    # 确保目录存在
    if not os.path.exists(SOURCE_DIRECTORY):
        os.makedirs(SOURCE_DIRECTORY)
        print(f"请将你的 .md 文件放入 {SOURCE_DIRECTORY} 目录后再次运行。")
    else:
        ingest_markdown(SOURCE_DIRECTORY, PERSIST_DIRECTORY)
