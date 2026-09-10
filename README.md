# Lingxi Check-in

[![GitHub stars](https://img.shields.io/github/stars/qq987985/Lingxi-Check-in?style=flat-square)](https://github.com/qq987985/Lingxi-Check-in/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/qq987985/Lingxi-Check-in?style=flat-square)](https://github.com/qq987985/Lingxi-Check-in/network/members)
[![License: MIT](https://img.shields.io/github/license/qq987985/Lingxi-Check-in?style=flat-square)](LICENSE)
[![Build & Push](https://img.shields.io/github/actions/workflow/status/qq987985/Lingxi-Check-in/docker-publish.yml?branch=main&style=flat-square&label=build)](https://github.com/qq987985/Lingxi-Check-in/actions/workflows/docker-publish.yml)
[![GHCR Image](https://img.shields.io/badge/ghcr.io-lingxi--checkin-blue?style=flat-square&logo=docker&logoColor=white)](https://github.com/qq987985/Lingxi-Check-in/pkgs/container/lingxi-checkin)

金山灵犀自动签到工具。每天定时自动签到，通过 Bark 推送结果到 iPhone，带本地文件持久化记忆，防止容器重启后重复签到 / 重复通知。

## 功能特性

- ⏰ **多时间点签到**：支持自定义每日多个签到时间，任一成功即记入当日成功
- 🧠 **状态持久化**：签到成功日期写入 `data/last_success.txt`，容器重建后不会重复签到、重复推送
- 🔍 **三级结果判定**：明确失败 / 明确成功 / 未知结果（通知人工确认，下轮自动重试）
- 🔔 **Bark 推送**：签到成功、Cookie 失效、网络异常均实时推送到手机
- ✅ **配置自检**：环境变量未配置或仍为占位符时主动告警，时间格式非法自动剔除
- 🐳 **Docker 一键部署**：推送代码到 main 分支即自动构建镜像并推送至 GHCR

## 快速开始

### 1. 获取签到接口 URL 和 Cookie

1. 用电脑浏览器（推荐 Chrome）登录金山灵犀，打开签到页面
2. 按 `F12` 打开开发者工具，切换到 **Network（网络）** 面板
3. 在页面上手动点击一次「签到」
4. 在 Network 面板中找到签到请求（通常为 POST 请求），右键 → **Copy** → **Copy as cURL**
5. 从复制的 cURL 命令中提取：
   - **请求 URL** → 填入 `CHECKIN_URL`
   - **请求头中的 Cookie** → 填入 `LINGXI_COOKIE`

> ⚠️ Cookie 有有效期，失效后会收到「Cookie 可能已失效」的 Bark 推送，按上述步骤重新抓取替换即可。

### 2. 配置环境变量

编辑 `docker-compose.yml` 中的 `environment` 部分：

| 变量 | 必填 | 说明 | 示例 |
|---|---|---|---|
| `CHECKIN_URL` | ✅ | 抓取到的签到接口地址 | `https://xxx.com/api/checkin` |
| `LINGXI_COOKIE` | ✅ | 登录后的完整 Cookie 字符串 | `sessionid=abc123; ...` |
| `CHECKIN_TIMES` | 否 | 每日签到时间，逗号分隔，格式 `HH:MM` | `08:30,16:30`（默认值） |
| `BARK_URL` | 否 | Bark 推送链接（含 Key），不配置则不推送 | `https://api.day.app/你的Key` |
| `TZ` | 否 | 时区 | `Asia/Shanghai`（默认值） |

**docker-compose.yml 模板**（新服务器部署时直接复制，填入三项真实配置即可）：

```yaml
services:
  lingxi-checkin:
    image: ghcr.1ms.run/qq987985/lingxi-checkin:latest
    container_name: lingxi-checkin
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
      - CHECKIN_TIMES=08:30,16:30
      - CHECKIN_URL=请在这里填入抓取到的真实签到接口URL
      - LINGXI_COOKIE=请在这里填入你的真实Cookie
      - BARK_URL=请在这里填入你的Bark推送链接(包含Key)
    volumes:
      # 持久化签到状态文件，防止容器重建后重复签到/重复通知
      - ./data:/app/data
```

### 3. 启动

```bash
# 首次部署先拉取镜像（compose 也会自动拉，手动拉一次可提前确认网络畅通）
docker pull ghcr.1ms.run/qq987985/lingxi-checkin:latest

docker compose up -d
```

查看运行日志：

```bash
docker logs -f lingxi-checkin
```

启动后会立即执行一次签到，之后按设定时间每日执行。

## 签到结果判定逻辑

| 响应特征 | 判定 | 行为 |
|---|---|---|
| 包含「未登录」「失败」或 `"error"` 非 0 | ❌ 失败 | 推送「Cookie 可能已失效」，**不写**成功状态 |
| 包含「成功」「已签到」「已签过」或 `"success":true` / `"error":0` | ✅ 成功 | 推送结果，写入当日成功状态 |
| 以上都不匹配 | ❓ 未知 | 推送「请人工确认」，**不写**成功状态，下个时间点重试 |
| 网络异常 | ⚠️ 异常 | 推送异常信息，下个时间点重试 |

> 「已签过」（当日重复签到）也计为成功，避免重复通知打扰。

## 常用命令

```bash
# 重启（修改配置后）
docker compose up -d --force-recreate

# 停止
docker compose down

# 手动清除当日成功记录（下次到点会重新签到）
rm data/last_success.txt
```

## 镜像说明

- 镜像地址：`ghcr.1ms.run/qq987985/lingxi-checkin:latest`（GHCR 国内镜像加速）
- 推送 `main` / `master` 分支触发 GitHub Actions 自动构建发布，见 [docker-publish.yml](.github/workflows/docker-publish.yml)

## 注意事项

- `docker-compose.yml` 中的 URL、Cookie、Bark Key 属于敏感信息，推送到公开仓库前请确认已替换回占位符
- `data/` 目录下的签到记录已被 `.gitignore` 排除，不会提交

## 开源协议

本项目基于 [MIT License](LICENSE) 开源，可自由使用、修改和分发。本工具仅供学习交流，请遵守目标网站的使用条款。
