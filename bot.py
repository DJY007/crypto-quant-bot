#!/usr/bin/env python3
"""
加密货币量化分析 Telegram Bot
功能：
1. 从币安API获取K线数据
2. 生成K线图
3. 调用DeepSeek API进行量化分析
4. 发送分析结果到Telegram
"""

import os
import json
import time
import asyncio
import aiohttp
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional, Dict, List, Tuple

# 配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BINANCE_API_BASE = "https://api.binance.com"
DEEPSEEK_API_BASE = "https://api.deepseek.com"

# K线周期映射
TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
    "1M": "1M"
}

# 获取K线数据的限制数量
KLINE_LIMIT = 100


class CryptoAnalyzerBot:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_klines(self, symbol: str, interval: str, limit: int = KLINE_LIMIT) -> List[List]:
        """从币安获取K线数据"""
        url = f"{BINANCE_API_BASE}/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"币安API错误: {error_text}")
    
    def create_kline_chart(self, klines: List[List], symbol: str, timeframe: str) -> BytesIO:
        """生成K线图"""
        # 解析K线数据
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # 绘制K线
        for idx, row in df.iterrows():
            color = 'green' if row['close'] >= row['open'] else 'red'
            
            # 实体
            height = abs(row['close'] - row['open'])
            bottom = min(row['close'], row['open'])
            ax1.bar(row['timestamp'], height, bottom=bottom, color=color, width=0.6, alpha=0.8)
            
            # 影线
            ax1.plot([row['timestamp'], row['timestamp']], 
                    [row['low'], row['high']], 
                    color=color, linewidth=0.5)
        
        # 设置标题和标签
        ax1.set_title(f'{symbol} {timeframe} K线图', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格 (USDT)')
        ax1.grid(True, alpha=0.3)
        
        # 格式化x轴
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 绘制成交量
        colors = ['green' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'red' 
                  for i in range(len(df))]
        ax2.bar(df['timestamp'], df['volume'], color=colors, alpha=0.7, width=0.6)
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 保存到内存
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    async def analyze_with_deepseek(self, klines_data: Dict, symbol: str) -> str:
        """调用DeepSeek API进行量化分析"""
        
        # 准备K线数据摘要
        price_data = self._prepare_price_data(klines_data)
        
        prompt = f"""你是一名专业的加密货币量化交易员，负责基于数据做交易决策。

我将提供K线数据，请你输出一份结构化交易分析，包括：

1）市场结构（趋势/震荡/突破）+ 当前阶段判断  
2）关键支撑位、阻力位、流动性区域（止损集中区）
3）结合技术分析判断市场情绪（利多/利空/中性）及影响周期（短/中期）
4）给出多空概率（%）并说明逻辑
5）提供一个可执行交易策略（做多和做空都要）：入场点、止损、止盈、风险收益比
6）列出失效条件（什么情况下判断错误）

最后用一句话总结当前交易偏向（做多/做空/观望）+ 信心评分（0-100）

要求：
- 偏量化和交易逻辑，不要泛泛分析
- 尽量具体到价格区间
- 像真实交易员一样给出明确结论

交易对: {symbol}

K线数据:
{price_data}
"""

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一名专业的加密货币量化交易员，擅长技术分析和量化交易策略。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        async with self.session.post(
            f"{DEEPSEEK_API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result['choices'][0]['message']['content']
            else:
                error_text = await response.text()
                raise Exception(f"DeepSeek API错误: {error_text}")
    
    def _prepare_price_data(self, klines_data: Dict) -> str:
        """准备价格数据摘要"""
        summary = []
        
        for timeframe, klines in klines_data.items():
            if not klines:
                continue
                
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 计算技术指标
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None
            
            # 计算波动率
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * 100
            
            summary.append(f"""
【{timeframe}周期】
- 最新价格: {df['close'].iloc[-1]:.4f}
- 周期最高: {df['high'].max():.4f}
- 周期最低: {df['low'].min():.4f}
- 周期涨幅: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%
- 平均成交量: {df['volume'].mean():.2f}
- 波动率: {volatility:.2f}%
- SMA20: {sma_20:.4f if sma_20 else 'N/A'}
- SMA50: {sma_50:.4f if sma_50 else 'N/A'}
""")
        
        return "\n".join(summary)
    
    async def send_message(self, chat_id: int, text: str) -> None:
        """发送文本消息到Telegram"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"发送消息失败: {error_text}")
    
    async def send_photo(self, chat_id: int, photo: BytesIO, caption: str = "") -> None:
        """发送图片到Telegram"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('caption', caption)
        data.add_field('photo', photo, filename='chart.png', content_type='image/png')
        
        async with self.session.post(url, data=data) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"发送图片失败: {error_text}")
    
    async def analyze_crypto(self, chat_id: int, symbol: str) -> None:
        """执行完整的加密货币分析流程"""
        try:
            # 发送开始分析消息
            await self.send_message(chat_id, f"🔍 开始分析 {symbol.upper()}...")
            
            # 获取各周期K线数据
            klines_data = {}
            charts = {}
            
            for tf_name, tf_code in TIMEFRAMES.items():
                try:
                    klines = await self.get_klines(symbol, tf_code)
                    klines_data[tf_name] = klines
                    
                    # 生成图表
                    chart = self.create_kline_chart(klines, symbol.upper(), tf_name)
                    charts[tf_name] = chart
                    
                    # 发送图表
                    await self.send_photo(chat_id, chart, f"{symbol.upper()} {tf_name} K线图")
                    
                    # 短暂延迟避免频率限制
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"获取{tf_name}数据失败: {e}")
                    continue
            
            # 调用DeepSeek进行分析
            await self.send_message(chat_id, "🤖 正在调用AI进行量化分析...")
            
            analysis = await self.analyze_with_deepseek(klines_data, symbol.upper())
            
            # 发送分析结果
            await self.send_message(chat_id, f"📊 *量化分析报告*\n\n{analysis}")
            
        except Exception as e:
            await self.send_message(chat_id, f"❌ 分析失败: {str(e)}")


class TelegramWebhookHandler:
    """处理Telegram Webhook请求"""
    
    def __init__(self):
        self.bot = CryptoAnalyzerBot()
    
    async def handle_update(self, update: Dict) -> None:
        """处理Telegram更新"""
        async with self.bot:
            if 'message' in update:
                message = update['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')
                
                # 处理命令
                if text.startswith('/start'):
                    await self.bot.send_message(
                        chat_id,
                        "👋 欢迎使用加密货币量化分析Bot!\n\n"
                        "可用命令:\n"
                        "/analyze <交易对> - 分析指定加密货币\n"
                        "例如: /analyze BTCUSDT\n\n"
                        "支持的时间周期: 15m, 1h, 4h, 1d, 1w, 1M"
                    )
                
                elif text.startswith('/analyze'):
                    parts = text.split()
                    if len(parts) < 2:
                        await self.bot.send_message(
                            chat_id,
                            "❌ 请提供交易对\n例如: /analyze BTCUSDT"
                        )
                        return
                    
                    symbol = parts[1]
                    await self.bot.analyze_crypto(chat_id, symbol)
                
                else:
                    await self.bot.send_message(
                        chat_id,
                        "❓ 未知命令\n使用 /analyze <交易对> 进行分析"
                    )


def run_polling():
    """运行Bot轮询模式"""
    import asyncio
    
    async def poll():
        bot = CryptoAnalyzerBot()
        last_update_id = 0
        
        async with bot:
            while True:
                try:
                    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
                    params = {"offset": last_update_id + 1, "limit": 10}
                    
                    async with bot.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('ok') and data.get('result'):
                                for update in data['result']:
                                    last_update_id = update['update_id']
                                    
                                    # 处理消息
                                    if 'message' in update:
                                        message = update['message']
                                        chat_id = message['chat']['id']
                                        text = message.get('text', '')
                                        
                                        # 处理命令
                                        if text.startswith('/start'):
                                            await bot.send_message(
                                                chat_id,
                                                "👋 欢迎使用加密货币量化分析Bot!\n\n"
                                                "可用命令:\n"
                                                "/analyze <交易对> - 分析指定加密货币\n"
                                                "例如: /analyze BTCUSDT\n\n"
                                                "支持的时间周期: 15m, 1h, 4h, 1d, 1w, 1M"
                                            )
                                        
                                        elif text.startswith('/analyze'):
                                            parts = text.split()
                                            if len(parts) < 2:
                                                await bot.send_message(
                                                    chat_id,
                                                    "❌ 请提供交易对\n例如: /analyze BTCUSDT"
                                                )
                                                continue
                                            
                                            symbol = parts[1]
                                            await bot.analyze_crypto(chat_id, symbol)
                                        
                                        else:
                                            await bot.send_message(
                                                chat_id,
                                                "❓ 未知命令\n使用 /analyze <交易对> 进行分析"
                                            )
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"轮询错误: {e}")
                    await asyncio.sleep(5)
    
    asyncio.run(poll())


if __name__ == "__main__":
    # 检查环境变量
    if not TELEGRAM_BOT_TOKEN:
        print("错误: 请设置 TELEGRAM_BOT_TOKEN 环境变量")
        exit(1)
    
    if not DEEPSEEK_API_KEY:
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        exit(1)
    
    print("🚀 启动加密货币量化分析Bot...")
    print("使用轮询模式运行")
    run_polling()
