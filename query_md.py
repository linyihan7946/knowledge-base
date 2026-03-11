import argparse
import sys
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 设置标准输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def query_vector_db(query_text: str, persist_dir: str, top_k: int = 3, offline: bool = True):
    # 1. 加载相同的 Embedding 模型 (离线模式)
    model_kwargs = {"local_files_only": offline}
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs=model_kwargs
    )

    # 2. 加载现有数据库
    vector_db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

    # 3. 执行相似度搜索
    results = vector_db.similarity_search(query_text, k=top_k)

    print(f"\n{'='*60}")
    print(f"查询: {query_text}")
    print(f"{'='*60}\n")

    for i, doc in enumerate(results):
        print(f"--- 结果 {i + 1} ---")
        print(f"来源: {doc.metadata.get('source', '未知')}")
        # 清理内容中的特殊 Unicode 字符
        content = doc.page_content.replace('\u200b', '').replace('\ufeff', '')
        print(f"内容:\n{content}")
        print("-" * 40 + "\n")

    return results


def interactive_query(persist_dir: str, offline: bool = True):
    """交互式查询模式"""
    print("=" * 60)
    print("Markdown 知识库查询系统")
    print("输入问题进行查询，输入 'quit' 或 'exit' 退出")
    print("=" * 60 + "\n")

    while True:
        try:
            query = input("请输入问题: ").strip()
            if query.lower() in ('quit', 'exit', 'q'):
                print("再见！")
                break
            if query:
                query_vector_db(query, persist_dir, top_k=5, offline=offline)
        except KeyboardInterrupt:
            print("\n再见！")
            break


if __name__ == "__main__":
    PERSIST_DIRECTORY = "./chroma_db"

    parser = argparse.ArgumentParser(description="Markdown 知识库查询工具")
    parser.add_argument("query", nargs="?", help="查询内容")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="返回结果数量")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("--online", action="store_true", help="在线模式（允许网络请求）")

    args = parser.parse_args()

    offline = not args.online

    if args.interactive:
        interactive_query(PERSIST_DIRECTORY, offline=offline)
    elif args.query:
        query_vector_db(args.query, PERSIST_DIRECTORY, top_k=args.top_k, offline=offline)
    else:
        # 默认交互模式
        interactive_query(PERSIST_DIRECTORY, offline=offline)
