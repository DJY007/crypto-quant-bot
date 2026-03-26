# VPS部署指南（推荐）

由于Render免费服务器可能存在网络限制，推荐使用海外VPS部署。

## 推荐VPS服务商

| 服务商 | 价格 | 特点 |
|--------|------|------|
| [Vultr](https://www.vultr.com/) | $5/月 | 按小时计费，随时删除 |
| [DigitalOcean](https://www.digitalocean.com/) | $4/月 | 简单易用 |
| [Linode](https://www.linode.com/) | $5/月 | 稳定可靠 |
| [AWS Lightsail](https://aws.amazon.com/lightsail/) | $3.5/月 | 亚马逊服务 |

## 快速部署步骤

### 1. 创建VPS实例
- 选择 **Ubuntu 22.04 LTS**
- 选择 **新加坡/日本/美国** 节点
- 最低配置即可（1核1GB内存）

### 2. 连接到服务器

```bash
ssh root@你的服务器IP
```

### 3. 一键部署脚本

在服务器上执行：

```bash
# 安装Docker
curl -fsSL https://get.docker.com | sh

# 创建项目目录
mkdir -p /opt/crypto-bot && cd /opt/crypto-bot

# 下载项目
curl -L https://github.com/DJY007/crypto-quant-bot/archive/refs/heads/main.zip -o bot.zip
apt-get update && apt-get install -y unzip
unzip bot.zip && mv crypto-quant-bot-main/* . && rm -rf crypto-quant-bot-main bot.zip

# 创建环境变量文件
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28
DEEPSEEK_API_KEY=sk-3473d35aa86c43f881720bec82e6b08c
BINANCE_API_KEY=Gg6Jdd5ZwsLA2uGw0InE8nQ3EiSbBDzezyniUlzfXYByjb9hdmZllsp4NeEfyF7Z
EOF

# 构建并运行
docker build -t crypto-bot .
docker run -d \
  --name crypto-bot \
  --restart unless-stopped \
  --env-file .env \
  crypto-bot

# 查看日志
docker logs -f crypto-bot
```

### 4. 管理Bot

```bash
# 查看日志
docker logs -f crypto-bot

# 重启Bot
docker restart crypto-bot

# 停止Bot
docker stop crypto-bot

# 更新Bot（拉取最新代码后）
docker stop crypto-bot
docker rm crypto-bot
docker build -t crypto-bot .
docker run -d --name crypto-bot --restart unless-stopped --env-file .env crypto-bot
```

## 使用Docker Compose（更简单）

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  crypto-bot:
    build: .
    container_name: crypto-quant-bot
    environment:
      - TELEGRAM_BOT_TOKEN=8728057887:AAFK3-xdwK8rv2zawy5pImp56LbomZZ8z28
      - DEEPSEEK_API_KEY=sk-3473d35aa86c43f881720bec82e6b08c
      - BINANCE_API_KEY=Gg6Jdd5ZwsLA2uGw0InE8nQ3EiSbBDzezyniUlzfXYByjb9hdmZllsp4NeEfyF7Z
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

然后运行：

```bash
docker-compose up -d
docker-compose logs -f
```

## 故障排查

### 查看详细日志

```bash
docker logs -f crypto-bot 2>&1 | tee bot.log
```

### 测试API连接

```bash
# 测试币安API
curl https://api.binance.com/api/v3/ping

# 测试DeepSeek API
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer sk-3473d35aa86c43f881720bec82e6b08c"
```

### 如果还是无法连接

可能是防火墙问题：

```bash
# 检查防火墙
ufw status

# 允许出站连接（通常默认允许）
ufw allow out 443/tcp
```

## 需要帮助？

如果在部署过程中遇到问题，请提供：
1. VPS服务商和节点位置
2. 错误日志（`docker logs crypto-bot`）
3. 具体的错误信息
