# 免费云平台部署指南

由于网络环境限制，推荐部署到以下免费云平台：

---

## 方案一：Render（推荐 ⭐）

**优点**: 免费、稳定、无需信用卡

### 部署步骤

1. **Fork项目到GitHub**（或创建新仓库上传代码）

2. **访问 Render**
   - 打开 https://render.com/
   - 用GitHub账号登录

3. **创建Web Service**
   - 点击 "New +" → "Web Service"
   - 选择你的GitHub仓库
   - 配置如下：
     - **Name**: `crypto-quant-bot`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python bot.py`

4. **设置环境变量**
   - 点击 "Environment" 标签
   - 添加：
     - `TELEGRAM_BOT_TOKEN` = `8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28`
     - `DEEPSEEK_API_KEY` = `sk-688c91dac04d4ba4bfe27a48ca552310`

5. **部署**
   - 点击 "Create Web Service"
   - 等待部署完成（约2-3分钟）

---

## 方案二：Railway

**优点**: 免费额度充足，部署简单

### 部署步骤

1. **访问 Railway**
   - 打开 https://railway.app/
   - 用GitHub账号登录

2. **创建项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的仓库

3. **设置环境变量**
   - 进入项目 → Variables
   - 添加：
     - `TELEGRAM_BOT_TOKEN` = `8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28`
     - `DEEPSEEK_API_KEY` = `sk-688c91dac04d4ba4bfe27a48ca552310`

4. **部署**
   - 自动开始部署
   - 等待完成

---

## 方案三：Fly.io

**优点**: 全球节点，速度快

### 部署步骤

1. **安装 Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **登录**
```bash
fly auth login
```

3. **部署**
```bash
cd crypto-bot
fly launch
fly secrets set TELEGRAM_BOT_TOKEN="8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28"
fly secrets set DEEPSEEK_API_KEY="sk-688c91dac04d4ba4bfe27a48ca552310"
fly deploy
```

---

## 方案四：VPS服务器（最稳定）

如果你有海外VPS，可以直接部署：

```bash
# 1. 连接服务器
ssh root@your_server_ip

# 2. 安装Docker
curl -fsSL https://get.docker.com | sh

# 3. 创建项目目录
mkdir -p /opt/crypto-bot && cd /opt/crypto-bot

# 4. 上传项目文件（在本地执行）
scp -r crypto-bot/* root@your_server_ip:/opt/crypto-bot/

# 5. 在服务器上启动
cd /opt/crypto-bot
docker build -t crypto-bot .
docker run -d \
  --name crypto-bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28" \
  -e DEEPSEEK_API_KEY="sk-688c91dac04d4ba4bfe27a48ca552310" \
  crypto-bot
```

---

## 验证部署

部署完成后，在Telegram中搜索你的Bot：

**Bot用户名**: `@crypto_quant_8728057887_bot`

发送测试命令：
```
/analyze BTCUSDT
```

如果收到K线图和分析报告，说明部署成功！

---

## 推荐VPS服务商

| 服务商 | 价格 | 特点 |
|--------|------|------|
| [Vultr](https://www.vultr.com/) | $5/月起 | 按小时计费，随时删除 |
| [DigitalOcean](https://www.digitalocean.com/) | $4/月起 | 简单易用 |
| [Linode](https://www.linode.com/) | $5/月起 | 稳定可靠 |
| [AWS Lightsail](https://aws.amazon.com/lightsail/) | $3.5/月起 | 亚马逊服务 |

---

## 需要帮助？

如果在部署过程中遇到问题，请告诉我：
1. 你选择的部署方案
2. 遇到的具体错误信息
3. 当前进行到哪个步骤
