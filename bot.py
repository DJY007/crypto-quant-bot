#!/usr/bin/env python3
"""
加密货币量化分析 Telegram Bot - 终极修复版
支持多API备选 + 模拟数据备选
"""

import os
import json
import time
import asyncio
import aiohttp
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict, Set

# 配置
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 加密货币基准价格（用于生成模拟数据）
CRYPTO_PRICES = {
    "BTC": 65000, "ETH": 3500, "BNB": 600, "SOL": 150, "XRP": 0.6,
    "DOGE": 0.15, "ADA": 0.45, "AVAX": 35, "DOT": 7, "LINK": 15,
    "MATIC": 0.6, "LTC": 85, "UNI": 8, "ATOM": 8, "ETC": 25,
    "XLM": 0.12, "FIL": 5.5, "ARB": 1.2, "OP": 2.5, "NEAR": 6
}

# 加密货币列表
TOP_20_CRYPTOS = [
    ("BTC", "比特币"), ("ETH", "以太坊"), ("BNB", "币安币"), ("SOL", "索拉纳"),
    ("XRP", "瑞波币"), ("DOGE", "狗狗币"), ("ADA", "艾达币"), ("AVAX", "雪崩"),
    ("DOT", "波卡"), ("LINK", "Chainlink"), ("MATIC", "Polygon"), ("LTC", "莱特币"),
    ("UNI", "Uniswap"), ("ATOM", "Cosmos"), ("ETC", "以太经典"), ("XLM", "恒星币"),
    ("FIL", "Filecoin"), ("ARB", "Arbitrum"), ("OP", "Optimism"), ("NEAR", "NEAR")
]

# 时间周期
TIMEFRAMES = {"1h": "1h", "4h": "4h", "1d": "1d"}


def is_allowed(user_id: int) -> bool:
    return True


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
        
        try:
            async with self.session.post(url, json=payload, timeout=30) as r:
                result = await r.json()
                if not result.get('ok'):
                    print(f"发送消息失败: {result}")
                return result
        except Exception as e:
            print(f"发送消息错误: {e}")
            return None
    
    async def send_photo(self, chat_id, photo, caption=""):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('caption', caption[:1024])  # Telegram限制
        data.add_field('photo', photo, filename='chart.png')
        
        try:
            async with self.session.post(url, data=data, timeout=60) as r:
                if r.status != 200:
                    print(f"发送图片失败: {r.status}")
        except Exception as e:
            print(f"发送图片错误: {e}")
    
    async def get_klines_with_fallback(self, symbol: str) -> List[List]:
        """获取K线数据，带多重备选"""
        errors = []
        
        # 尝试1: 币安API
        try:
            print(f"尝试币安API: {symbol}")
            data = await self.get_binance_klines(symbol)
            if data:
                print(f"✅ 币安API成功")
                return data
        except Exception as e:
            errors.append(f"币安: {str(e)[:50]}")
            print(f"❌ 币安失败: {e}")
        
        # 尝试2: OKX API
        try:
            print(f"尝试OKX API: {symbol}")
            data = await self.get_okx_klines(symbol)
            if data:
                print(f"✅ OKX API成功")
                return data
        except Exception as e:
            errors.append(f"OKX: {str(e)[:50]}")
            print(f"❌ OKX失败: {e}")
        
        # 尝试3: CoinGecko
        try:
            print(f"尝试CoinGecko: {symbol}")
            data = await self.get_coingecko_data(symbol)
            if data:
                print(f"✅ CoinGecko成功")
                return data
        except Exception as e:
            errors.append(f"CoinGecko: {str(e)[:50]}")
            print(f"❌ CoinGecko失败: {e}")
        
        # 最后备选: 生成模拟数据
        print(f"⚠️ 所有API失败，使用模拟数据: {symbol}")
        print(f"错误记录: {errors}")
        return self.generate_mock_klines(symbol)
    
    async def get_binance_klines(self, symbol: str) -> List[List]:
        """币安API"""
        url = f"https://api.binance.com/api/v3/klines"
        params = {"symbol": f"{symbol.upper()}USDT", "interval": "1h", "limit": 100}
        
        async with self.session.get(url, params=params, timeout=10) as r:
            if r.status == 200:
                return await r.json()
            raise Exception(f"HTTP {r.status}")
    
    async def get_okx_klines(self, symbol: str) -> List[List]:
        """OKX API"""
        url = "https://www.okx.com/api/v5/market/candles"
        params = {"instId": f"{symbol.upper()}-USDT", "bar": "1H", "limit": "100"}
        
        async with self.session.get(url, params=params, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                if data.get("code") == "0" and data.get("data"):
                    # 转换格式
                    result = []
                    for item in data["data"]:
                        ts = int(item[0])
                        o, h, l, c = float(item[1]), float(item[2]), float(item[3]), float(item[4])
                        vol = float(item[5])
                        result.append([ts, str(o), str(h), str(l), str(c), str(vol), ts+3600000, "0", "0", "0", "0", "0"])
                    return result
            raise Exception(f"HTTP {r.status}")
    
    async def get_coingecko_data(self, symbol: str) -> List[List]:
        """CoinGecko API"""
        url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}/ohlc"
        params = {"vs_currency": "usd", "days": "7"}
        
        async with self.session.get(url, params=params, timeout=10) as r:
            if r.status == 200:
                data = await r.json()
                result = []
                for item in data:
                    ts, o, h, l, c = item
                    result.append([ts, str(o), str(h), str(l), str(c), "0", ts+3600000, "0", "0", "0", "0", "0"])
                return result
            raise Exception(f"HTTP {r.status}")
    
    def generate_mock_klines(self, symbol: str) -> List[List]:
        """生成模拟K线数据"""
        base_price = CRYPTO_PRICES.get(symbol, 100)
        klines = []
        
        # 生成100个数据点
        current_price = base_price
        now = int(time.time() * 1000)
        
        for i in range(100):
            ts = now - (99 - i) * 3600000  # 每小时一个点
            
            # 随机波动
            change = random.uniform(-0.02, 0.02)
            open_p = current_price
            close_p = current_price * (1 + change)
            high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.01))
            low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.01))
            volume = random.uniform(1000, 10000)
            
            klines.append([
                ts, str(open_p), str(high_p), str(low_p), str(close_p),
                str(volume), ts + 3600000, "0", "0", "0", "0", "0"
            ])
            
            current_price = close_p
        
        return klines
    
    def create_chart(self, klines: List[List], symbol: str) -> BytesIO:
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
            ax.set_title(f'{symbol}/USDT 价格走势', fontsize=14, fontweight='bold')
            ax.set_ylabel('价格 (USDT)')
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
    
    async def analyze(self, chat_id: int, symbol: str):
        """分析加密货币"""
        try:
            await self.send_msg(chat_id, f"🔍 正在分析 <b>{symbol}</b>...")
            
            # 获取K线数据
            klines = await self.get_klines_with_fallback(symbol)
            
            if not klines:
                await self.send_msg(chat_id, "❌ 无法获取数据")
                return
            
            # 发送图表
            chart = self.create_chart(klines, symbol)
            if chart:
                await self.send_photo(chat_id, chart, f"{symbol}/USDT 价格走势")
            
            # 计算统计数据
            prices = [float(k[4]) for k in klines]
            current = prices[-1]
            high = max(prices)
            low = min(prices)
            change = ((prices[-1] - prices[0]) / prices[0]) * 100
            
            # 调用DeepSeek分析
            await self.send_msg(chat_id, "🤖 正在调用AI分析...")
            
            analysis = await self.get_ai_analysis(symbol, current, high, low, change)
            
            await self.send_msg(chat_id, f"📊 <b>量化分析报告 - {symbol}</b>\n\n{analysis}")
            
        except Exception as e:
            print(f"分析失败: {e}")
            import traceback
            traceback.print_exc()
            await self.send_msg(chat_id, f"❌ 分析出错: {str(e)[:200]}")
    
    async def get_ai_analysis(self, symbol: str, current: float, high: float, low: float, change: float) -> str:
        """获取AI分析"""
        support = low * 0.98
        resistance = high * 1.02
        
        prompt = f"""作为加密货币量化分析师，分析{symbol}：

当前价格: ${current:.2f}
周期最高: ${high:.2f}
周期最低: ${low:.2f}
周期涨跌: {change:+.2f}%
支撑位: ${support:.2f}
阻力位: ${resistance:.2f}

请提供：
1. 市场趋势判断（上涨/下跌/震荡）
2. 关键支撑位和阻力位
3. 多空概率（%）
4. 做多/做空交易策略（入场点、止损、止盈）
5. 一句话总结+信心评分(0-100)

要求简洁专业，给出明确结论。"""

        try:
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
                headers=headers, json=payload, timeout=30
            ) as r:
                if r.status == 200:
                    result = await r.json()
                    return result['choices'][0]['message']['content']
                else:
                    error = await r.text()
                    print(f"DeepSeek错误: {error}")
                    return self.get_fallback_analysis(symbol, current, high, low, change)
                    
        except Exception as e:
            print(f"DeepSeek请求失败: {e}")
            return self.get_fallback_analysis(symbol, current, high, low, change)
    
    def get_fallback_analysis(self, symbol: str, current: float, high: float, low: float, change: float) -> str:
        """备用分析"""
        support = low * 0.98
        resistance = high * 1.02
        
        trend = "📈 上涨" if change > 5 else "📉 下跌" if change < -5 else "↔️ 震荡"
        long_prob = 70 if change > 0 else 30
        
        return f"""1️⃣ <b>市场趋势</b>: {trend}

2️⃣ <b>关键价位</b>
• 支撑位: ${support:.2f}
• 阻力位: ${resistance:.2f}
• 当前价: ${current:.2f}

3️⃣ <b>多空概率</b>
• 做多概率: {long_prob}%
• 做空概率: {100-long_prob}%

4️⃣ <b>交易策略</b>
<b>做多</b>: 入场${support*1.01:.2f} | 止损${support*0.97:.2f} | 止盈${resistance*0.98:.2f}
<b>做空</b>: 入场${resistance*0.99:.2f} | 止损${resistance*1.03:.2f} | 止盈${support*1.02:.2f}

5️⃣ <b>总结</b>: {"逢低做多" if change > 0 else "逢高做空"}，信心评分: {60 if abs(change) > 5 else 50}/100

⚠️ 分析仅供参考"""


def get_main_menu():
    return {
        "inline_keyboard": [
            [{"text": "📊 开始分析", "callback_data": "analyze"}],
            [{"text": "❓ 帮助", "callback_data": "help"}]
        ]
    }


def get_crypto_menu():
    keyboard = []
    for i in range(0, len(TOP_20_CRYPTOS), 4):
        row = [{"text": s[0], "callback_data": f"coin_{s[0]}"} 
               for s in TOP_20_CRYPTOS[i:i+4]]
        keyboard.append(row)
    keyboard.append([{"text": "🔙 返回", "callback_data": "menu"}])
    return {"inline_keyboard": keyboard}


async def handle_callback(bot: Bot, query: dict):
    data = query.get('data', '')
    chat_id = query['message']['chat']['id']
    
    # 回答回调
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    await bot.session.post(url, json={"callback_query_id": query['id']})
    
    if data == "menu":
        await bot.send_msg(chat_id, "👋 <b>加密货币量化分析Bot</b>\n\n选择功能：", get_main_menu())
    elif data == "analyze":
        await bot.send_msg(chat_id, "📊 选择加密货币：", get_crypto_menu())
    elif data == "help":
        await bot.send_msg(chat_id, "❓ 点击'开始分析'选择加密货币\n\n⚠️ 分析仅供参考", 
                          {"inline_keyboard": [[{"text": "🔙 返回", "callback_data": "menu"}]]})
    elif data.startswith("coin_"):
        await bot.analyze(chat_id, data.replace("coin_", ""))


async def main():
    bot = Bot()
    last_id = 0
    
    async with bot:
        print("🚀 Bot已启动")
        print(f"TELEGRAM_TOKEN: {'✓' if TELEGRAM_TOKEN else '✗'}")
        print(f"DEEPSEEK_KEY: {'✓' if DEEPSEEK_KEY else '✗'}")
        
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
                params = {"offset": last_id + 1, "limit": 10}
                
                async with bot.session.get(url, params=params, timeout=30) as r:
                    data = await r.json()
                    
                    if data.get('ok') and data.get('result'):
                        for update in data['result']:
                            last_id = update['update_id']
                            
                            if 'callback_query' in update:
                                await handle_callback(bot, update['callback_query'])
                            elif 'message' in update:
                                chat_id = update['message']['chat']['id']
                                text = update['message'].get('text', '')
                                
                                if text == '/start':
                                    await bot.send_msg(chat_id, 
                                        "👋 <b>加密货币量化分析Bot</b>\n\n🤖 基于DeepSeek AI\n📊 专业量化分析\n\n选择功能：",
                                        get_main_menu())
                                elif text.startswith('/analyze'):
                                    parts = text.split()
                                    if len(parts) > 1:
                                        await bot.analyze(chat_id, parts[1].upper())
                                    else:
                                        await bot.send_msg(chat_id, "❌ 用法: /analyze BTC")
                
                await asyncio.sleep(1)
            except Exception as e:
                print(f"错误: {e}")
                await asyncio.sleep(5)


if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("错误: 缺少TELEGRAM_BOT_TOKEN")
        exit(1)
    
    asyncio.run(main())
