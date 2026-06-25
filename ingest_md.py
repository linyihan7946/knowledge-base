import os
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
)
from langchain_text_splitters import MarkdownTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 加载.env环境变量
load_dotenv()


def get_embeddings():
    """获取阿里百炼embedding模型"""
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    base_url = os.environ.get(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    print("加载text-embedding-v3模型...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-v3",
        api_key=api_key,
        base_url=base_url,
        chunk_size=10,
        check_embedding_ctx_length=False,
    )
    print("成功加载text-embedding-v3模型！")
    return embeddings


def ingest_markdown(source_dir: str, persist_dir: str):
    # 1. 递归加载所有 .md 文件
    print(f"正在加载目录 {source_dir} 下的 Markdown 文件...")
    loader = DirectoryLoader(
        source_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    documents = loader.load()
    print(f"加载完成，共计 {len(documents)} 个文件。")

    # 2. 文本分段 (针对 Markdown 优化)
    print("正在对文档进行分段...")
    text_splitter = MarkdownTextSplitter(chunk_size=1500, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"分段完成，产生 {len(texts)} 个文本块。")

    # 3. 清理文本内容
    print("正在清理文本内容...")
    cleaned_texts = []
    for doc in texts:
        content = str(doc.page_content).strip()
        if content and len(content) > 10:
            cleaned_texts.append(content)
    print(f"有效文本块: {len(cleaned_texts)} 个。")

    # 4. 初始化 Embedding 模型
    print("正在初始化 Embedding 模型...")
    embeddings = get_embeddings()

    # 5. 直接使用from_texts创建向量库
    print("正在生成向量并存入数据库...")
    vector_db = Chroma.from_texts(
        texts=cleaned_texts, embedding=embeddings, persist_directory=persist_dir
    )
    print(f"处理完成！数据库已保存至: {persist_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Markdown 文件向量化入库工具")
    parser.add_argument("--source", "-s", default="./docs", help="Markdown 文件目录")
    parser.add_argument("--persist", "-p", default="./chroma_db", help="向量库保存目录")

    args = parser.parse_args()

    SOURCE_DIRECTORY = args.source
    PERSIST_DIRECTORY = args.persist

    # 确保目录存在
    if not os.path.exists(SOURCE_DIRECTORY):
        os.makedirs(SOURCE_DIRECTORY)
        print(f"请将你的 .md 文件放入 {SOURCE_DIRECTORY} 目录后再次运行。")
    else:
        ingest_markdown(SOURCE_DIRECTORY, PERSIST_DIRECTORY)
