# 加密货币量化分析Bot - 部署指南

## 项目文件说明

```
crypto-bot/
├── bot.py              # 主程序 - Telegram Bot核心逻辑
├── requirements.txt    # Python依赖包列表
├── Dockerfile         # Docker镜像构建配置
├── docker-compose.yml # Docker Compose部署配置
├── start.sh           # 本地启动脚本
├── README.md          # 项目说明文档
├── DEPLOY.md          # 本部署指南
└── .env.example       # 环境变量模板
```

## 部署方式

### 方式一：本地直接运行（推荐测试使用）

#### 1. 安装Python依赖

```bash
cd crypto-bot
pip3 install -r requirements.txt
```

#### 2. 设置环境变量

```bash
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export DEEPSEEK_API_KEY="your_deepseek_api_key"
```

或者创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件填入你的API密钥
```

#### 3. 运行Bot

```bash
# 方式1: 使用启动脚本
./start.sh

# 方式2: 直接运行
python3 bot.py
```

### 方式二：Docker部署（推荐生产环境）

#### 1. 使用Docker Compose（推荐）

```bash
cd crypto-bot

# 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件填入你的API密钥

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 2. 使用Docker命令

```bash
cd crypto-bot

# 构建镜像
docker build -t crypto-quant-bot .

# 运行容器
docker run -d \
  --name crypto-bot \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  -e DEEPSEEK_API_KEY="your_key" \
  --restart unless-stopped \
  crypto-quant-bot

# 查看日志
docker logs -f crypto-bot
```

### 方式三：云服务器部署

#### 推荐平台
- AWS EC2 / Lightsail
- Google Cloud Platform
- Azure VM
- DigitalOcean
- Vultr
- 阿里云/腾讯云海外节点

#### 部署步骤

1. **创建服务器实例**
   - 推荐配置: 1核2GB内存
   - 推荐系统: Ubuntu 22.04 LTS
   - 确保服务器可以访问外网

2. **连接到服务器**

```bash
ssh root@your_server_ip
```

3. **安装Docker和Docker Compose**

```bash
# 更新系统
apt update && apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | sh

# 安装Docker Compose
apt install docker-compose-plugin -y

# 启动Docker服务
systemctl start docker
systemctl enable docker
```

4. **上传项目文件**

```bash
# 在本地打包项目
tar -czvf crypto-bot.tar.gz crypto-bot/

# 上传到服务器
scp crypto-bot.tar.gz root@your_server_ip:/root/

# 在服务器上解压
ssh root@your_server_ip "tar -xzvf /root/crypto-bot.tar.gz"
```

5. **配置环境变量并启动**

```bash
cd /root/crypto-bot

# 创建环境变量文件
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DEEPSEEK_API_KEY=your_deepseek_api_key
EOF

# 启动服务
docker-compose up -d

# 查看日志确认正常运行
docker-compose logs -f
```

## 获取API密钥

### Telegram Bot Token

1. 打开Telegram，搜索 [@BotFather](https://t.me/BotFather)
2. 发送 `/newbot` 命令
3. 按提示设置机器人名称（如：Crypto Quant Analyzer）
4. 设置用户名（必须以bot结尾，如：crypto_quant_bot）
5. 复制获得的Bot Token

### DeepSeek API Key

1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册账号并登录
3. 进入API Keys页面
4. 创建新的API Key
5. 复制并保存API Key（只显示一次）

## 使用Bot

### 基本命令

- `/start` - 显示帮助信息
- `/analyze <交易对>` - 分析指定加密货币

### 使用示例

```
/analyze BTCUSDT
/analyze ETHUSDT
/analyze SOLUSDT
/analyze BNBUSDT
```

### 分析输出

Bot会返回：
1. 各周期K线图（15m, 1h, 4h, 1d, 1w, 1M）
2. AI量化分析报告，包括：
   - 市场结构判断
   - 关键支撑位/阻力位
   - 市场情绪分析
   - 多空概率
   - 可执行交易策略
   - 失效条件
   - 交易偏向总结

## 常见问题

### Q: Bot无法连接Telegram？

A: 确保服务器可以访问Telegram API。在中国大陆服务器需要配置代理或使用海外服务器。

### Q: 币安API无法访问？

A: 币安API在某些地区可能被限制，建议使用海外服务器部署。

### Q: DeepSeek API调用失败？

A: 检查：
1. API Key是否正确
2. 账户余额是否充足
3. API调用频率是否超限

### Q: 如何查看日志？

A: 
```bash
# Docker部署
docker-compose logs -f

# 本地运行
python3 bot.py 2>&1 | tee bot.log
```

### Q: 如何更新Bot？

A:
```bash
# 拉取最新代码
git pull

# 重启服务
docker-compose down
docker-compose up -d --build
```

## 安全建议

1. **保护API密钥**
   - 不要将 `.env` 文件提交到Git
   - 使用强密码保护服务器
   - 定期轮换API密钥

2. **限制Bot访问**
   - 可以在代码中添加白名单功能
   - 限制每个用户的分析频率

3. **监控和日志**
   - 定期检查日志
   - 设置异常告警

## 技术支持

如有问题，请检查：
1. 环境变量是否正确设置
2. 网络连接是否正常
3. API密钥是否有效
4. 查看日志获取详细错误信息
