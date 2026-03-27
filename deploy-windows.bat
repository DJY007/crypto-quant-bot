@echo off
chcp 65001 >nul
echo ==========================================
echo   加密货币量化分析Bot - 一键部署脚本
echo ==========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.11
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/5] Python已安装 ✓

:: 创建项目目录
set BOT_DIR=%USERPROFILE%\crypto-bot
if not exist "%BOT_DIR%" mkdir "%BOT_DIR%"
cd /d "%BOT_DIR%"

echo [2/5] 创建目录: %BOT_DIR% ✓

:: 下载bot.py
echo [3/5] 下载Bot代码...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/DJY007/crypto-quant-bot/main/bot.py' -OutFile 'bot.py'"
if not exist "bot.py" (
    echo [错误] 下载失败，请检查网络连接
    pause
    exit /b 1
)
echo [3/5] 下载完成 ✓

:: 安装依赖
echo [4/5] 安装依赖包（可能需要几分钟）...
pip install aiohttp matplotlib pandas requests -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [4/5] 依赖安装完成 ✓

:: 设置环境变量并运行
echo [5/5] 启动Bot...
set TELEGRAM_BOT_TOKEN=8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28
set DEEPSEEK_API_KEY=sk-3473d35aa86c43f881720bec82e6b08c

echo.
echo ==========================================
echo   Bot正在启动...
echo   请不要关闭此窗口
echo ==========================================
echo.

python bot.py

pause
