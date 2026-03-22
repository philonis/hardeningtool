# OpenClaw 安全加固工具

> 基于 CNCERT《OpenClaw 安全使用实践指南》开发的安全检查工具

## 概述

OpenClaw（中文名"龙虾"）具备系统指令执行、文件读写、API 调用等高权限能力。默认配置与不当使用极易导致远程接管、数据泄露、恶意代码执行等严重安全风险。

本项目提供自动化安全检查工具，帮助用户发现并修复 OpenClaw 安全风险。

## 功能

- ✅ **基础配置检查** - Gateway 绑定地址、Token 强度、配对策略
- ✅ **网络安全检查** - 端口暴露、公网访问、网络隧道
- ✅ **进程权限检查** - 运行用户权限
- ✅ **Docker 隔离检查** - 容器化部署检查
- ✅ **Skills 安全检查** - 第三方 Skills 供应链风险
- ✅ **工作区权限检查** - 文件系统访问控制

## 快速开始

### 安装

```bash
git clone https://github.com/philonis/hardeningtool.git
cd hardeningtool
```

### 运行检查

```bash
# 完整检查
python3 skills/hardening-check/scripts/check.py

# 分类检查
python3 skills/hardening-check/scripts/check.py --config   # 基础配置
python3 skills/hardening-check/scripts/check.py --network  # 网络安全

# JSON 输出
python3 skills/hardening-check/scripts/check.py --json
```

## 检查项目

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | Gateway 绑定 | 应为 loopback/127.0.0.1 |
| 2 | Gateway 认证 | Token 应 >= 32 位 |
| 3 | 端口监听 | 18789/19890 不应暴露 |
| 4 | 公网访问 | 公网不应能访问 |
| 5 | 进程用户 | 不应以 root 运行 |
| 6 | Docker 隔离 | 推荐容器化运行 |
| 7 | 网络隧道 | 检查 Tailscale/WireGuard |
| 8 | Skills 安全 | 审查第三方 Skills |
| 9 | Workspace 权限 | 敏感文件访问控制 |
| 10 | 安全审计 | openclaw security audit |

## 参考资料

- [CNCERT《OpenClaw 安全使用实践指南》](https://mp.weixin.qq.com/s/L9AKvAFMB6kE2EcRSvTxZw)
- [OpenClaw 官方文档](https://docs.openclaw.ai)

## 免责声明

本工具仅供参考学习，请勿用于非法用途。使用本工具产生的任何后果由使用者自行承担。
