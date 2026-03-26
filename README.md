# 加密货币量化分析 Telegram Bot

一个专业的加密货币量化分析Telegram机器人，从币安获取K线数据，使用DeepSeek AI进行量化分析。

## 功能特点

- 📊 获取多周期K线数据（15分钟、1小时、4小时、日线、周线、月线）
- 📈 自动生成K线图表
- 🤖 基于DeepSeek AI的专业量化分析
- 💼 提供完整的交易策略（入场点、止损、止盈、风险收益比）
- 🎯 多空概率分析和市场情绪判断

## 快速开始

### 1. 获取API密钥

#### Telegram Bot Token
1. 在Telegram中搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 创建新机器人
3. 按照提示设置机器人名称和用户名
4. 获取Bot Token

#### DeepSeek API Key
1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册并登录账号
3. 创建API Key

### 2. 部署

#### 方式一：直接运行

```bash
# 设置环境变量
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export DEEPSEEK_API_KEY="your_deepseek_api_key"

# 安装依赖
pip install -r requirements.txt

# 运行Bot
python bot.py
```

#### 方式二：使用Docker

```bash
# 构建镜像
docker build -t crypto-bot .

# 运行容器
docker run -d \
  -e TELEGRAM_BOT_TOKEN="your_telegram_bot_token" \
  -e DEEPSEEK_API_KEY="your_deepseek_api_key" \
  --name crypto-bot \
  crypto-bot
```

### 3. 使用Bot

在Telegram中搜索你的Bot用户名，开始对话：

- `/start` - 显示帮助信息
- `/analyze <交易对>` - 分析指定加密货币

示例：
```
/analyze BTCUSDT
/analyze ETHUSDT
/analyze SOLUSDT
```

## 分析输出示例

Bot会输出以下结构化分析：

1. **市场结构** - 趋势/震荡/突破判断
2. **关键价位** - 支撑位、阻力位、流动性区域
3. **市场情绪** - 利多/利空/中性及影响周期
4. **多空概率** - 百分比及逻辑说明
5. **交易策略** - 做多/做空的入场点、止损、止盈、风险收益比
6. **失效条件** - 判断错误的场景
7. **总结** - 交易偏向 + 信心评分

## 项目结构

```
crypto-bot/
├── bot.py              # 主程序
├── requirements.txt    # Python依赖
├── Dockerfile         # Docker配置
├── README.md          # 说明文档
└── .env.example       # 环境变量示例
```

## 技术栈

- Python 3.8+
- aiohttp - 异步HTTP客户端
- matplotlib - 图表生成
- pandas - 数据处理
- 币安API - K线数据
- DeepSeek API - AI分析

## 注意事项

1. 确保服务器可以访问Telegram和币安API
2. 建议使用海外服务器部署
3. 注意API调用频率限制
4. 交易有风险，分析结果仅供参考

## License

MIT License
