from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def query_vector_db(query_text: str, persist_dir: str):
    # 1. 加载相同的 Embedding 模型
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 2. 加载现有数据库
    vector_db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # 3. 执行相似度搜索
    results = vector_db.similarity_search(query_text, k=3)

    print(f"\n针对 '{query_text}' 的查询结果：\n")
    for i, doc in enumerate(results):
        print(f"--- 结果 {i + 1} ---")
        print(f"来源: {doc.metadata.get('source')}")
        print(f"内容预览: {doc.page_content[:200]}...")
        print("-" * 20)


if __name__ == "__main__":
    PERSIST_DIRECTORY = "./chroma_db"
    query = input("请输入搜索关键词: ")
    query_vector_db(query, PERSIST_DIRECTORY)
