#!/usr/bin/env python3
"""
加密货币量化分析 Telegram Bot
功能：
1. 白名单访问控制
2. 从币安API获取K线数据
3. 生成K线图
4. 调用DeepSeek API进行量化分析
5. 交互式按钮菜单
"""

import os
import json
import time
import asyncio
import aiohttp
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional, Dict, List, Tuple, Set

# 配置
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")

# 币安API备用域名列表
BINANCE_API_BASES = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://api4.binance.com",
]

# OKX API作为备选
OKX_API_BASE = "https://www.okx.com"

DEEPSEEK_API_BASE = "https://api.deepseek.com"

# 管理员用户ID列表
# 1795326193 - 主管理员
ADMIN_USER_IDS: Set[int] = {1795326193}
ALLOWED_USER_IDS: Set[int] = set()

# 前20加密货币列表
TOP_20_CRYPTOS = [
    ("BTC", "比特币"),
    ("ETH", "以太坊"),
    ("BNB", "币安币"),
    ("SOL", "索拉纳"),
    ("XRP", "瑞波币"),
    ("DOGE", "狗狗币"),
    ("ADA", "艾达币"),
    ("AVAX", "雪崩"),
    ("DOT", "波卡"),
    ("LINK", "Chainlink"),
    ("MATIC", "Polygon"),
    ("LTC", "莱特币"),
    ("UNI", "Uniswap"),
    ("ATOM", "Cosmos"),
    ("ETC", "以太经典"),
    ("XLM", "恒星币"),
    ("FIL", "Filecoin"),
    ("ARB", "Arbitrum"),
    ("OP", "Optimism"),
    ("NEAR", "NEAR"),
]

# K线周期映射
TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
    "1M": "1M"
}

KLINE_LIMIT = 100


def load_whitelist():
    """从文件加载白名单"""
    global ALLOWED_USER_IDS, ADMIN_USER_IDS
    try:
        if os.path.exists('whitelist.json'):
            with open('whitelist.json', 'r') as f:
                data = json.load(f)
                # 加载普通用户
                file_allowed = set(int(x) for x in data.get('allowed', []))
                ALLOWED_USER_IDS = ALLOWED_USER_IDS.union(file_allowed)
                # 加载文件中的管理员，合并到已有的管理员
                file_admins = set(int(x) for x in data.get('admins', []))
                ADMIN_USER_IDS = ADMIN_USER_IDS.union(file_admins)
                print(f"✅ 已加载白名单: {len(ALLOWED_USER_IDS)} 个用户, {len(ADMIN_USER_IDS)} 个管理员")
    except Exception as e:
        print(f"⚠️ 加载白名单失败: {e}")


def save_whitelist():
    """保存白名单到文件"""
    global ALLOWED_USER_IDS, ADMIN_USER_IDS
    try:
        with open('whitelist.json', 'w') as f:
            json.dump({
                'allowed': list(ALLOWED_USER_IDS),
                'admins': list(ADMIN_USER_IDS)
            }, f)
    except Exception as e:
        print(f"⚠️ 保存白名单失败: {e}")


def is_allowed(user_id: int) -> bool:
    """检查用户是否在白名单中"""
    # 暂时允许所有人访问（测试阶段）
    # 如果要开启白名单，取消下面这行的注释
    # return user_id in ALLOWED_USER_IDS or user_id in ADMIN_USER_IDS
    return True


def is_admin(user_id: int) -> bool:
    """检查用户是否是管理员"""
    return user_id in ADMIN_USER_IDS


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
        """从币安获取K线数据（尝试多个备用域名）"""
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        # 添加API Key到请求头
        headers = {}
        if BINANCE_API_KEY:
            headers["X-MBX-APIKEY"] = BINANCE_API_KEY
        
        last_error = None
        for api_base in BINANCE_API_BASES:
            try:
                url = f"{api_base}/api/v3/klines"
                async with self.session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        last_error = f"{api_base}: HTTP {response.status} - {error_text[:100]}"
                        print(f"⚠️ {last_error}")
            except Exception as e:
                last_error = f"{api_base}: {str(e)[:50]}"
                print(f"⚠️ {last_error}")
                continue
        
        # 如果币安都失败了，尝试OKX
        print("⚠️ 币安API全部失败，尝试OKX...")
        try:
            return await self.get_klines_okx(symbol, interval, limit)
        except Exception as e:
            raise Exception(f"所有API都无法访问。币安: {last_error}, OKX: {str(e)[:100]}")
    
    async def get_klines_okx(self, symbol: str, interval: str, limit: int = KLINE_LIMIT) -> List[List]:
        """从OKX获取K线数据（币安备选）"""
        # OKX时间周期映射
        okx_intervals = {
            "15m": "15m",
            "1h": "1H",
            "4h": "4H",
            "1d": "1D",
            "1w": "1W",
            "1M": "1M"
        }
        
        okx_interval = okx_intervals.get(interval, "1H")
        symbol_okx = f"{symbol.upper()}-USDT"
        
        url = f"{OKX_API_BASE}/api/v5/market/candles"
        params = {
            "instId": symbol_okx,
            "bar": okx_interval,
            "limit": limit
        }
        
        async with self.session.get(url, params=params, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("code") == "0" and data.get("data"):
                    # OKX数据格式转换为币安格式
                    # OKX: [ts, o, h, l, c, vol, volCcy, volCcyQuote, confirm]
                    # 币安: [ts, o, h, l, c, vol, close_time, ...]
                    okx_klines = data["data"]
                    converted = []
                    for k in okx_klines:
                        ts = int(k[0])
                        o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
                        vol = float(k[5])
                        # 币安格式: [ts, open, high, low, close, volume, close_time, ...]
                        converted.append([ts, str(o), str(h), str(l), str(c), str(vol), ts + 60000, "0", "0", "0", "0", "0"])
                    return converted
                else:
                    raise Exception(f"OKX API返回错误: {data}")
            else:
                error_text = await response.text()
                raise Exception(f"OKX API错误: HTTP {response.status} - {error_text}")
    
    def create_kline_chart(self, klines: List[List], symbol: str, timeframe: str) -> BytesIO:
        """生成K线图"""
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
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        for idx, row in df.iterrows():
            color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
            height = abs(row['close'] - row['open'])
            bottom = min(row['close'], row['open'])
            ax1.bar(row['timestamp'], height, bottom=bottom, color=color, width=0.6)
            ax1.plot([row['timestamp'], row['timestamp']], 
                    [row['low'], row['high']], 
                    color=color, linewidth=0.5)
        
        ax1.set_title(f'{symbol} {timeframe} K线图', fontsize=14, fontweight='bold')
        ax1.set_ylabel('价格 (USDT)')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        colors = ['#26a69a' if df.iloc[i]['close'] >= df.iloc[i]['open'] else '#ef5350' 
                  for i in range(len(df))]
        ax2.bar(df['timestamp'], df['volume'], color=colors, alpha=0.7, width=0.6)
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    async def analyze_with_deepseek(self, klines_data: Dict, symbol: str) -> str:
        """调用DeepSeek API进行量化分析"""
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
            
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * 100
            
            summary.append(f"""【{timeframe}周期】
- 最新价格: {df['close'].iloc[-1]:.4f}
- 周期最高: {df['high'].max():.4f}
- 周期最低: {df['low'].min():.4f}
- 周期涨幅: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%
- 平均成交量: {df['volume'].mean():.2f}
- 波动率: {volatility:.2f}%
- SMA20: {sma_20:.4f if sma_20 else 'N/A'}
- SMA50: {sma_50:.4f if sma_50 else 'N/A'}""")
        
        return "\n".join(summary)
    
    async def send_message(self, chat_id: int, text: str, reply_markup: dict = None) -> dict:
        """发送文本消息到Telegram"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        async with self.session.post(url, json=payload) as response:
            result = await response.json()
            if not result.get('ok'):
                print(f"发送消息失败: {result}")
            return result
    
    async def edit_message(self, chat_id: int, message_id: int, text: str, reply_markup: dict = None) -> dict:
        """编辑消息"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        async with self.session.post(url, json=payload) as response:
            return await response.json()
    
    async def answer_callback(self, callback_query_id: str, text: str = None) -> None:
        """回答回调查询"""
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        
        async with self.session.post(url, json=payload):
            pass
    
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
            await self.send_message(chat_id, f"🔍 开始分析 {symbol.upper()}...")
            
            klines_data = {}
            success_count = 0
            
            for tf_name, tf_code in TIMEFRAMES.items():
                try:
                    klines = await self.get_klines(symbol, tf_code)
                    if klines and len(klines) > 0:
                        klines_data[tf_name] = klines
                        
                        chart = self.create_kline_chart(klines, symbol.upper(), tf_name)
                        await self.send_photo(chat_id, chart, f"{symbol.upper()} {tf_name} K线图")
                        success_count += 1
                        await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"获取{tf_name}数据失败: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # 检查是否成功获取了数据
            if success_count == 0:
                await self.send_message(
                    chat_id, 
                    "❌ 无法获取K线数据\n\n"
                    "可能原因：\n"
                    "• 币安API暂时不可用\n"
                    "• 交易对不存在\n"
                    "• 网络连接问题\n\n"
                    "请稍后重试或检查交易对名称。"
                )
                return
            
            if len(klines_data) == 0:
                await self.send_message(chat_id, "❌ 没有可用的K线数据进行分枅")
                return
            
            await self.send_message(chat_id, f"✅ 成功获取 {success_count} 个周期数据，正在调用AI进行量化分析...")
            
            try:
                analysis = await self.analyze_with_deepseek(klines_data, symbol.upper())
                await self.send_message(chat_id, f"📊 *量化分析报告*\n\n{analysis}")
            except Exception as e:
                print(f"DeepSeek分析失败: {e}")
                import traceback
                traceback.print_exc()
                await self.send_message(
                    chat_id, 
                    f"❌ AI分析失败: {str(e)}\n\n"
                    "可能原因：\n"
                    "• DeepSeek API暂时不可用\n"
                    "• API密钥无效或余额不足\n"
                    "• 请求超时"
                )
            
        except Exception as e:
            print(f"分析流程失败: {e}")
            import traceback
            traceback.print_exc()
            await self.send_message(chat_id, f"❌ 分析失败: {str(e)}")


def get_main_menu_keyboard() -> dict:
    """获取主菜单键盘"""
    return {
        "inline_keyboard": [
            [{"text": "📊 DeepSeek量化分析", "callback_data": "menu_analysis"}],
            [{"text": "❓ 使用帮助", "callback_data": "menu_help"}]
        ]
    }


def get_crypto_list_keyboard(page: int = 0) -> dict:
    """获取加密货币列表键盘"""
    items_per_page = 10
    start = page * items_per_page
    end = min(start + items_per_page, len(TOP_20_CRYPTOS))
    
    keyboard = []
    
    # 添加加密货币按钮（每行2个）
    for i in range(start, end, 2):
        row = []
        symbol, name = TOP_20_CRYPTOS[i]
        row.append({"text": f"{symbol}", "callback_data": f"analyze_{symbol}USDT"})
        if i + 1 < end:
            symbol2, name2 = TOP_20_CRYPTOS[i + 1]
            row.append({"text": f"{symbol2}", "callback_data": f"analyze_{symbol2}USDT"})
        keyboard.append(row)
    
    # 添加分页按钮
    nav_row = []
    if page > 0:
        nav_row.append({"text": "⬅️ 上一页", "callback_data": f"page_{page-1}"})
    if end < len(TOP_20_CRYPTOS):
        nav_row.append({"text": "➡️ 下一页", "callback_data": f"page_{page+1}"})
    if nav_row:
        keyboard.append(nav_row)
    
    # 添加返回按钮
    keyboard.append([{"text": "🔙 返回主菜单", "callback_data": "menu_main"}])
    
    return {"inline_keyboard": keyboard}


def get_admin_keyboard() -> dict:
    """获取管理员键盘"""
    return {
        "inline_keyboard": [
            [{"text": "➕ 添加用户", "callback_data": "admin_add_user"}],
            [{"text": "➖ 移除用户", "callback_data": "admin_remove_user"}],
            [{"text": "📋 查看白名单", "callback_data": "admin_list_users"}],
            [{"text": "🔙 返回主菜单", "callback_data": "menu_main"}]
        ]
    }


async def handle_start(bot: CryptoAnalyzerBot, chat_id: int, user_id: int) -> None:
    """处理/start命令"""
    if not is_allowed(user_id):
        await bot.send_message(
            chat_id,
            "⛔ *访问被拒绝*\n\n"
            "您没有权限使用此Bot。\n"
            f"您的用户ID: `{user_id}`\n\n"
            "请联系管理员获取访问权限。"
        )
        return
    
    welcome_text = (
        "👋 *欢迎使用加密货币量化分析Bot!*\n\n"
        "🤖 本Bot提供专业的AI量化分析服务\n"
        "📊 基于币安K线数据 + DeepSeek AI\n"
        "💼 提供完整的交易策略建议\n\n"
        "请选择功能："
    )
    
    await bot.send_message(chat_id, welcome_text, get_main_menu_keyboard())


async def handle_callback(bot: CryptoAnalyzerBot, callback_query: dict) -> None:
    """处理回调查询"""
    callback_data = callback_query.get('data', '')
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    user_id = callback_query['from']['id']
    
    # 检查权限
    if not is_allowed(user_id):
        await bot.answer_callback(callback_query['id'], "⛔ 您没有权限")
        return
    
    await bot.answer_callback(callback_query['id'])
    
    # 处理菜单导航
    if callback_data == "menu_main":
        welcome_text = (
            "👋 *欢迎使用加密货币量化分析Bot!*\n\n"
            "🤖 本Bot提供专业的AI量化分析服务\n"
            "📊 基于币安K线数据 + DeepSeek AI\n"
            "💼 提供完整的交易策略建议\n\n"
            "请选择功能："
        )
        await bot.edit_message(chat_id, message_id, welcome_text, get_main_menu_keyboard())
    
    elif callback_data == "menu_analysis":
        analysis_text = (
            "📊 *DeepSeek量化分析*\n\n"
            "请选择要分析的加密货币：\n\n"
            "💡 点击币种即可开始分析\n"
            "⏱️ 分析时间约10-20秒"
        )
        await bot.edit_message(chat_id, message_id, analysis_text, get_crypto_list_keyboard(0))
    
    elif callback_data == "menu_help":
        help_text = (
            "❓ *使用帮助*\n\n"
            "📊 *DeepSeek量化分析*\n"
            "点击后选择前20加密货币之一\n"
            "Bot将自动获取多周期K线数据\n"
            "并调用DeepSeek AI进行量化分析\n\n"
            "📈 *分析报告包含：*\n"
            "• 6个周期K线图（15m/1h/4h/1d/1w/1M）\n"
            "• 市场结构判断\n"
            "• 关键支撑位/阻力位\n"
            "• 多空概率分析\n"
            "• 可执行交易策略\n"
            "• 风险收益比计算\n\n"
            "⚠️ *风险提示*\n"
            "分析结果仅供参考，不构成投资建议"
        )
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 返回主菜单", "callback_data": "menu_main"}]
            ]
        }
        await bot.edit_message(chat_id, message_id, help_text, keyboard)
    
    # 处理分页
    elif callback_data.startswith("page_"):
        page = int(callback_data.split("_")[1])
        analysis_text = (
            "📊 *DeepSeek量化分析*\n\n"
            "请选择要分析的加密货币：\n\n"
            "💡 点击币种即可开始分析\n"
            "⏱️ 分析时间约10-20秒"
        )
        await bot.edit_message(chat_id, message_id, analysis_text, get_crypto_list_keyboard(page))
    
    # 处理分析请求
    elif callback_data.startswith("analyze_"):
        symbol = callback_data.replace("analyze_", "")
        await bot.edit_message(
            chat_id, message_id,
            f"🔍 开始分析 {symbol}...",
            {"inline_keyboard": [[{"text": "🔙 返回列表", "callback_data": "menu_analysis"}]]}
        )
        await bot.analyze_crypto(chat_id, symbol)
    
    # 处理管理员命令
    elif callback_data.startswith("admin_"):
        if not is_admin(user_id):
            await bot.send_message(chat_id, "⛔ 您不是管理员")
            return
        
        if callback_data == "admin_add_user":
            await bot.send_message(
                chat_id,
                "➕ *添加用户*\n\n"
                "请发送命令：\n"
                "`/adduser <用户ID>`\n\n"
                "用户可以通过发送 /myid 获取自己的ID"
            )
        elif callback_data == "admin_remove_user":
            await bot.send_message(
                chat_id,
                "➖ *移除用户*\n\n"
                "请发送命令：\n"
                "`/removeuser <用户ID>`"
            )
        elif callback_data == "admin_list_users":
            admin_list = "\n".join([f"• `{uid}` (管理员)" for uid in ADMIN_USER_IDS]) if ADMIN_USER_IDS else "无"
            user_list = "\n".join([f"• `{uid}`" for uid in ALLOWED_USER_IDS]) if ALLOWED_USER_IDS else "无"
            
            list_text = (
                "📋 *白名单用户*\n\n"
                "*管理员：*\n" + admin_list + "\n\n"
                "*普通用户：*\n" + user_list
            )
            await bot.send_message(chat_id, list_text)


async def handle_admin_commands(bot: CryptoAnalyzerBot, chat_id: int, user_id: int, text: str) -> bool:
    """处理管理员命令，返回是否已处理"""
    if not is_admin(user_id):
        return False
    
    # 添加用户
    if text.startswith("/adduser "):
        try:
            target_id = int(text.split()[1])
            ALLOWED_USER_IDS.add(target_id)
            save_whitelist()
            await bot.send_message(chat_id, f"✅ 已添加用户 `{target_id}` 到白名单")
            return True
        except:
            await bot.send_message(chat_id, "❌ 格式错误，请使用: `/adduser <用户ID>`")
            return True
    
    # 移除用户
    elif text.startswith("/removeuser "):
        try:
            target_id = int(text.split()[1])
            if target_id in ALLOWED_USER_IDS:
                ALLOWED_USER_IDS.discard(target_id)
                save_whitelist()
                await bot.send_message(chat_id, f"✅ 已移除用户 `{target_id}`")
            else:
                await bot.send_message(chat_id, "❌ 用户不在白名单中")
            return True
        except:
            await bot.send_message(chat_id, "❌ 格式错误，请使用: `/removeuser <用户ID>`")
            return True
    
    # 添加管理员
    elif text.startswith("/addadmin "):
        try:
            target_id = int(text.split()[1])
            ADMIN_USER_IDS.add(target_id)
            save_whitelist()
            await bot.send_message(chat_id, f"✅ 已添加 `{target_id}` 为管理员")
            return True
        except:
            await bot.send_message(chat_id, "❌ 格式错误，请使用: `/addadmin <用户ID>`")
            return True
    
    return False


def run_polling():
    """运行Bot轮询模式"""
    import asyncio
    
    # 加载白名单
    load_whitelist()
    
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
                                    
                                    # 处理回调查询
                                    if 'callback_query' in update:
                                        await handle_callback(bot, update['callback_query'])
                                    
                                    # 处理消息
                                    elif 'message' in update:
                                        message = update['message']
                                        chat_id = message['chat']['id']
                                        user_id = message['from']['id']
                                        text = message.get('text', '')
                                        
                                        # 获取用户ID命令
                                        if text == '/myid':
                                            await bot.send_message(
                                                chat_id,
                                                f"🆔 您的用户ID是：\n`{user_id}`\n\n"
                                                "请将此ID发送给管理员获取访问权限。"
                                            )
                                            continue
                                        
                                        # 处理管理员命令
                                        if await handle_admin_commands(bot, chat_id, user_id, text):
                                            continue
                                        
                                        # 处理/start命令
                                        if text.startswith('/start'):
                                            await handle_start(bot, chat_id, user_id)
                                        
                                        # 处理/analyze命令
                                        elif text.startswith('/analyze'):
                                            if not is_allowed(user_id):
                                                await bot.send_message(
                                                    chat_id,
                                                    "⛔ *访问被拒绝*\n\n"
                                                    "您没有权限使用此Bot。\n"
                                                    f"您的用户ID: `{user_id}`\n\n"
                                                    "请联系管理员获取访问权限。"
                                                )
                                                continue
                                            
                                            parts = text.split()
                                            if len(parts) < 2:
                                                await bot.send_message(
                                                    chat_id,
                                                    "❌ 请提供交易对\n例如: `/analyze BTCUSDT`"
                                                )
                                                continue
                                            
                                            symbol = parts[1]
                                            await bot.analyze_crypto(chat_id, symbol)
                                        
                                        # 管理员菜单
                                        elif text == '/admin':
                                            if not is_admin(user_id):
                                                await bot.send_message(chat_id, "⛔ 您不是管理员")
                                                continue
                                            
                                            await bot.send_message(
                                                chat_id,
                                                "🔧 *管理员面板*\n\n"
                                                "可用命令：\n"
                                                "• `/adduser <ID>` - 添加用户\n"
                                                "• `/removeuser <ID>` - 移除用户\n"
                                                "• `/addadmin <ID>` - 添加管理员\n"
                                                "• `/myid` - 查看自己的ID",
                                                get_admin_keyboard()
                                            )
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"轮询错误: {e}")
                    import traceback
                    traceback.print_exc()
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
    print(f"✅ 管理员数量: {len(ADMIN_USER_IDS)}")
    print(f"✅ 白名单用户: {len(ALLOWED_USER_IDS)}")
    print("📋 命令: /start - 主菜单, /myid - 查看ID, /admin - 管理员面板")
    run_polling()
