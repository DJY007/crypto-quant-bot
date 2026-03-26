# 快速开始指南

## 5分钟部署你的加密货币量化分析Bot

### 步骤1: 获取API密钥 (2分钟)

#### Telegram Bot Token
1. Telegram搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot`
3. 设置名称和用户名
4. **保存Token**

#### DeepSeek API Key
1. 访问 [DeepSeek平台](https://platform.deepseek.com/)
2. 注册登录
3. 创建API Key
4. **保存Key**

---

### 步骤2: 部署Bot (3分钟)

#### 方式A: Docker部署（推荐）

```bash
# 1. 进入项目目录
cd crypto-bot

# 2. 设置环境变量
export TELEGRAM_BOT_TOKEN="你的Telegram Token"
export DEEPSEEK_API_KEY="你的DeepSeek Key"

# 3. 启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

#### 方式B: 直接运行

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 设置环境变量
export TELEGRAM_BOT_TOKEN="你的Telegram Token"
export DEEPSEEK_API_KEY="你的DeepSeek Key"

# 3. 运行
python3 bot.py
```

---

### 步骤3: 使用Bot

在Telegram中搜索你的Bot，发送：

```
/analyze BTCUSDT
```

等待10-20秒，即可收到完整的量化分析报告！

---

## 支持的命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/start` | 显示帮助 | `/start` |
| `/analyze` | 分析加密货币 | `/analyze ETHUSDT` |

## 支持的交易对

所有币安现货市场的交易对，例如：
- BTCUSDT, ETHUSDT, SOLUSDT
- BNBUSDT, ADAUSDT, DOTUSDT
- 等等...

## 分析包含内容

✅ 6个周期K线图 (15m, 1h, 4h, 1d, 1w, 1M)  
✅ 市场结构判断  
✅ 关键支撑位/阻力位  
✅ 多空概率分析  
✅ 可执行交易策略  
✅ 风险收益比计算  
✅ 失效条件提示  
✅ 交易偏向总结  

---

## 遇到问题？

1. **检查环境变量**: `echo $TELEGRAM_BOT_TOKEN`
2. **查看日志**: `docker-compose logs -f`
3. **网络连接**: 确保能访问Telegram和币安
4. **详细文档**: 查看 [DEPLOY.md](DEPLOY.md)

---

**⚠️ 风险提示**: 交易有风险，分析结果仅供参考，不构成投资建议。
