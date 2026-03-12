import os
import shutil
import argparse
from ingest_md import ingest_markdown

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="重新生成向量库")
    parser.add_argument("--source", "-s", default="./docs", help="Markdown 文件目录")
    parser.add_argument("--persist", "-p", default="./chroma_db", help="向量库保存目录")
    parser.add_argument("--online", action="store_true", help="在线模式（允许网络请求下载模型）")
    
    args = parser.parse_args()
    
    SOURCE_DIRECTORY = args.source
    PERSIST_DIRECTORY = args.persist
    offline = not args.online
    
    # 删除旧的向量库
    if os.path.exists(PERSIST_DIRECTORY):
        print(f"正在删除旧的向量库: {PERSIST_DIRECTORY}")
        shutil.rmtree(PERSIST_DIRECTORY)
        print("删除完成！")
    
    # 重新生成向量库
    ingest_markdown(SOURCE_DIRECTORY, PERSIST_DIRECTORY, offline=offline)