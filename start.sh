#!/bin/bash

# 加密货币量化分析Bot启动脚本

echo "🚀 加密货币量化分析Bot"
echo "======================"

# 检查环境变量
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ 错误: 请设置 TELEGRAM_BOT_TOKEN 环境变量"
    echo "   从 @BotFather 获取: https://t.me/BotFather"
    exit 1
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ 错误: 请设置 DEEPSEEK_API_KEY 环境变量"
    echo "   从 DeepSeek平台获取: https://platform.deepseek.com/"
    exit 1
fi

echo "✅ 环境变量检查通过"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    exit 1
fi

echo "✅ Python版本: $(python3 --version)"
echo ""

# 检查依赖
echo "📦 检查依赖..."
pip3 install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成"
else
    echo "⚠️  依赖安装可能有问题，尝试继续..."
fi

echo ""
echo "🤖 启动Bot..."
echo "======================"
python3 bot.py
