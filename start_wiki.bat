@echo off
REM 启动 Wiki 知识库浏览界面
REM 使用方法：双击运行 start_wiki.bat

echo ========================================
echo   个人知识库 Wiki 浏览界面
echo ========================================
echo.

REM 检查 MkDocs 是否安装
pip show mkdocs >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] MkDocs 未安装，正在安装...
    pip install mkdocs mkdocs-material
    echo.
)

echo [启动] 正在启动 Wiki 服务...
echo [同步] 正在准备 Wiki 页面...
python prepare_wiki_docs.py
if %errorlevel% neq 0 (
    echo [错误] Wiki 页面准备失败，请检查上面的错误信息。
    pause
    exit /b %errorlevel%
)

echo [地址] 请在浏览器中打开: http://127.0.0.1:8000
echo [提示] 按 Ctrl+C 停止服务
echo.

start "" http://127.0.0.1:8000
mkdocs serve -a 127.0.0.1:8000
