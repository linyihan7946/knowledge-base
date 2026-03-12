import os
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import MarkdownTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 设置HuggingFace镜像（国内用户）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


def get_embeddings(offline: bool = True):
    """获取embedding模型，优先尝试中文模型"""
    model_kwargs = {"local_files_only": offline}

    # 方案1：尝试使用多语言模型（支持中英文）
    try:
        print("尝试加载多语言模型...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs=model_kwargs,
        )
        print("成功加载多语言模型！")
        return embeddings
    except Exception as e:
        print(f"加载多语言模型失败: {e}")

    # 方案2：使用已缓存的英文模型
    try:
        print("使用已缓存的英文模型...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
        )
        print("成功加载英文模型（对中文支持较差）！")
        return embeddings
    except Exception as e:
        print(f"加载英文模型失败: {e}")
        raise


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
    # 中文字符较多，适当增大chunk_size
    text_splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"分段完成，产生 {len(texts)} 个文本块。")

    # 3. 初始化 Embedding 模型 (使用多语言模型)
    print("正在初始化 Embedding 模型...")
    embeddings = get_embeddings(offline=offline)

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
    parser.add_argument(
        "--online", action="store_true", help="在线模式（允许网络请求下载模型）"
    )

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
