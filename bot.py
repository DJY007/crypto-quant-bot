#!/usr/bin/env python3
"""
加密货币量化分析 Telegram Bot - 简化版
"""

import os
import json
import asyncio
import aiohttp
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from io import BytesIO
from datetime import datetime

# 配置
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 管理员ID
ADMIN_IDS = {1795326193}
ALLOWED_IDS = set()

# 加密货币列表
CRYPTOS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", 
    "DOT", "LINK", "MATIC", "LTC", "UNI", "ATOM", "ETC", 
    "XLM", "FIL", "ARB", "OP", "NEAR"
]

# 时间周期
TIMEFRAMES = {
    "1h": "1h",
    "4h": "4h", 
    "1d": "1d"
}


def is_allowed(user_id):
    return True  # 允许所有人


class Bot:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def send_msg(self, chat_id, text, buttons=None):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if buttons:
            payload["reply_markup"] = json.dumps(buttons)
        
        async with self.session.post(url, json=payload) as r:
            result = await r.json()
            if not result.get('ok'):
                print(f"发送消息失败: {result}")
            return result
    
    async def edit_msg(self, chat_id, msg_id, text, buttons=None):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
        payload = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "HTML"}
        if buttons:
            payload["reply_markup"] = json.dumps(buttons)
        await self.session.post(url, json=payload)
    
    async def send_photo(self, chat_id, photo, caption=""):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('caption', caption)
        data.add_field('photo', photo, filename='chart.png')
        await self.session.post(url, data=data)
    
    async def get_klines(self, symbol, interval):
        """从CoinGecko获取价格数据（国内可访问）"""
        try:
            # 使用CoinGecko API（国内可访问）
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/ohlc"
            params = {
                "vs_currency": "usd",
                "days": "1" if interval == "1h" else "7" if interval == "4h" else "30"
            }
            
            async with self.session.get(url, params=params, timeout=15) as r:
                if r.status == 200:
                    data = await r.json()
                    # 转换为币安格式
                    klines = []
                    for item in data:
                        ts, o, h, l, c = item
                        klines.append([ts, str(o), str(h), str(l), str(c), "0", ts+3600000, "0", "0", "0", "0", "0"])
                    return klines
                else:
                    print(f"CoinGecko错误: {r.status}")
                    return None
        except Exception as e:
            print(f"获取K线失败: {e}")
            return None
    
    def create_chart(self, klines, symbol, timeframe):
        """创建K线图"""
        try:
            df = pd.DataFrame(klines, columns=[
                'ts', 'o', 'h', 'l', 'c', 'v', 'ct', 'qv', 'tr', 'tb', 'tq', 'ig'
            ])
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
            df['c'] = df['c'].astype(float)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['ts'], df['c'], linewidth=2, color='#2196F3')
            ax.fill_between(df['ts'], df['c'], alpha=0.3, color='#2196F3')
            ax.set_title(f'{symbol} {timeframe} 价格走势', fontsize=14)
            ax.set_ylabel('价格 (USD)')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            print(f"创建图表失败: {e}")
            return None
    
    async def analyze(self, chat_id, symbol):
        """分析加密货币"""
        await self.send_msg(chat_id, f"🔍 正在分析 <b>{symbol}</b>...")
        
        try:
            # 获取价格数据
            klines = await self.get_klines(symbol, "1d")
            if not klines:
                await self.send_msg(chat_id, "❌ 无法获取价格数据，请稍后重试")
                return
            
            # 发送图表
            chart = self.create_chart(klines, symbol, "1D")
            if chart:
                await self.send_photo(chat_id, chart, f"{symbol} 价格走势")
            
            # 准备分析数据
            prices = [float(k[4]) for k in klines]
            current_price = prices[-1]
            high_24h = max(prices[-24:]) if len(prices) >= 24 else max(prices)
            low_24h = min(prices[-24:]) if len(prices) >= 24 else min(prices)
            change_24h = ((prices[-1] - prices[-24]) / prices[-24] * 100) if len(prices) >= 24 else 0
            
            # 调用DeepSeek分析
            await self.send_msg(chat_id, "🤖 正在调用AI分析...")
            
            prompt = f"""作为加密货币量化分析师，分析{symbol}：

当前价格: ${current_price:.2f}
24H最高: ${high_24h:.2f}
24H最低: ${low_24h:.2f}
24H涨跌: {change_24h:.2f}%

请提供：
1. 市场趋势判断（上涨/下跌/震荡）
2. 关键支撑位和阻力位
3. 多空概率（%）
4. 简短交易策略建议
5. 一句话总结+信心评分(0-100)

要求简洁专业，给出明确结论。"""

            headers = {
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是专业加密货币量化分析师"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
            
            async with self.session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            ) as r:
                if r.status == 200:
                    result = await r.json()
                    analysis = result['choices'][0]['message']['content']
                    await self.send_msg(chat_id, f"📊 <b>量化分析报告</b>\n\n{analysis}")
                else:
                    error = await r.text()
                    print(f"DeepSeek错误: {error}")
                    await self.send_msg(chat_id, f"❌ AI分析失败，请稍后重试")
                    
        except Exception as e:
            print(f"分析失败: {e}")
            import traceback
            traceback.print_exc()
            await self.send_msg(chat_id, f"❌ 分析出错: {str(e)}")


def get_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 开始分析", "callback_data": "analyze"}],
            [{"text": "❓ 帮助", "callback_data": "help"}]
        ]
    }


def get_crypto_menu():
    keyboard = []
    for i in range(0, len(CRYPTOS), 4):
        row = []
        for j in range(i, min(i+4, len(CRYPTOS))):
            row.append({"text": CRYPTOS[j], "callback_data": f"coin_{CRYPTOS[j]}"})
        keyboard.append(row)
    keyboard.append([{"text": "🔙 返回", "callback_data": "menu"}])
    return {"inline_keyboard": keyboard}


async def handle_callback(bot, query):
    data = query.get('data', '')
    chat_id = query['message']['chat']['id']
    msg_id = query['message']['message_id']
    
    if data == "menu":
        await bot.edit_msg(chat_id, msg_id, 
            "👋 <b>加密货币量化分析Bot</b>\n\n选择功能：", 
            get_main_menu())
    
    elif data == "analyze":
        await bot.edit_msg(chat_id, msg_id,
            "📊 选择要分析的加密货币：",
            get_crypto_menu())
    
    elif data == "help":
        await bot.edit_msg(chat_id, msg_id,
            "❓ <b>使用帮助</b>\n\n"
            "1. 点击'开始分析'\n"
            "2. 选择加密货币\n"
            "3. 等待AI分析报告\n\n"
            "⚠️ 分析仅供参考，不构成投资建议",
            {"inline_keyboard": [[{"text": "🔙 返回", "callback_data": "menu"}]]})
    
    elif data.startswith("coin_"):
        symbol = data.replace("coin_", "")
        await bot.analyze(chat_id, symbol)


async def main():
    bot = Bot()
    last_id = 0
    
    async with bot:
        print("🚀 Bot已启动")
        
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
                params = {"offset": last_id + 1, "limit": 10}
                
                async with bot.session.get(url, params=params, timeout=30) as r:
                    data = await r.json()
                    
                    if data.get('ok') and data.get('result'):
                        for update in data['result']:
                            last_id = update['update_id']
                            
                            # 处理回调
                            if 'callback_query' in update:
                                await handle_callback(bot, update['callback_query'])
                            
                            # 处理消息
                            elif 'message' in update:
                                chat_id = update['message']['chat']['id']
                                text = update['message'].get('text', '')
                                
                                if text == '/start':
                                    await bot.send_msg(chat_id,
                                        "👋 <b>加密货币量化分析Bot</b>\n\n"
                                        "🤖 基于DeepSeek AI的专业分析\n"
                                        "📊 提供量化交易策略建议\n\n"
                                        "选择功能：",
                                        get_main_menu())
                                
                                elif text.startswith('/analyze'):
                                    parts = text.split()
                                    if len(parts) > 1:
                                        await bot.analyze(chat_id, parts[1].upper())
                                    else:
                                        await bot.send_msg(chat_id, 
                                            "❌ 请提供币种，例如: /analyze BTC")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"错误: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("错误: 缺少TELEGRAM_BOT_TOKEN")
        exit(1)
    if not DEEPSEEK_KEY:
        print("错误: 缺少DEEPSEEK_API_KEY")
        exit(1)
    
    asyncio.run(main())
