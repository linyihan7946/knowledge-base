import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import MarkdownTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def ingest_markdown(source_dir: str, persist_dir: str, offline: bool = True):
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
    # 离线模式：使用本地缓存的模型，避免网络请求
    model_kwargs = {"local_files_only": offline}
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs=model_kwargs
    )

    # 4. 向量化并入库 (ChromaDB)
    print("正在生成向量并存入数据库...")
    vector_db = Chroma.from_documents(
        documents=texts, embedding=embeddings, persist_directory=persist_dir
    )
    print(f"处理完成！数据库已保存至: {persist_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Markdown 文件向量化入库工具")
    parser.add_argument("--source", "-s", default="./docs", help="Markdown 文件目录")
    parser.add_argument("--persist", "-p", default="./chroma_db", help="向量库保存目录")
    parser.add_argument("--online", action="store_true", help="在线模式（允许网络请求下载模型）")

    args = parser.parse_args()

    SOURCE_DIRECTORY = args.source
    PERSIST_DIRECTORY = args.persist
    offline = not args.online

    # 确保目录存在
    if not os.path.exists(SOURCE_DIRECTORY):
        os.makedirs(SOURCE_DIRECTORY)
        print(f"请将你的 .md 文件放入 {SOURCE_DIRECTORY} 目录后再次运行。")
    else:
        ingest_markdown(SOURCE_DIRECTORY, PERSIST_DIRECTORY, offline=offline)
