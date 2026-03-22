# OpenClaw 个人安全加固 PRD

> 来源：国家互联网应急中心（CNCERT）、中国网络空间安全协会 联合发布
> 发布日期：2026年3月22日
> 原文链接：https://mp.weixin.qq.com/s/L9AKvAFMB6kE2EcRSvTxZw

---

## 1. 产品概述

### 1.1 背景

OpenClaw（中文名"龙虾"）具备系统指令执行、文件读写、API 调用等高权限能力。默认配置与不当使用极易导致：

- 远程接管
- 数据泄露
- 恶意代码执行

等严重安全风险。

### 1.2 目标用户

个人用户：将 OpenClaw 作为日常 AI 助手使用的开发者、技术爱好者。

### 1.3 核心价值

在充分利用 OpenClaw 强大能力的同时，最小化安全风险，保护个人数据与系统安全。

---

## 2. 安全风险分析

### 2.1 主要风险

| 风险类型 | 描述 | 严重程度 |
|---------|------|---------|
| 远程接管 | 攻击者通过未授权访问控制 OpenClaw | 🔴 高 |
| 数据泄露 | 敏感文件、密钥、聊天记录被窃取 | 🔴 高 |
| 恶意代码执行 | 通过 Agent 执行恶意命令 | 🔴 高 |
| 权限提升 | 普通用户权限升级为管理员权限 | 🟠 中 |

### 2.2 常见攻击面

1. **默认端口暴露**（18789/19890）
2. **弱密码或无认证**
3. **配对策略设置为 open**
4. **盲目安装第三方 Skills**
5. **在日常主力电脑上运行**

---

## 3. 安全加固清单（个人用户）

### 3.1 运行环境隔离 ⚠️ 优先级：最高

**问题**：日常办公电脑环境复杂，有大量个人数据和工作文件。

**建议**：
- [ ] 使用**专用设备**（闲置旧电脑）运行 OpenClaw
- [ ] 或使用 **Docker 容器** 隔离运行
- [ ] 或使用 **虚拟机**（VMware、Parallels、UTM）

**实施方案**：

```bash
# Docker 方案（推荐）
docker run -d \
  --name openclaw \
  -p 127.0.0.1:18789:18789 \
  -p 127.0.0.1:19890:19890 \
  -v ~/openclaw-data:/root/.openclaw \
  openclaw/openclaw:latest

# 关键点：
# 1. 端口仅绑定 127.0.0.1，不暴露到公网
# 2. 数据目录挂载到宿主机，便于备份
# 3. 不以 --privileged 运行
```

### 3.2 端口暴露控制 ⚠️ 优先级：最高

**问题**：18789（Gateway管理界面）和 19890 端口直接暴露可能被远程访问。

**建议**：
- [ ] **不将默认端口暴露到公网**
- [ ] **不将端口暴露到局域网**
- [ ] 仅绑定 `127.0.0.1` 或 `localhost`

**当前配置检查**：
```bash
# 检查 config.json 中的 bind 设置
cat ~/.openclaw/openclaw.json | grep bind
# 应为 "bind": "loopback" 或 "127.0.0.1"
```

**禁止行为**：
- ❌ 不使用 Tailscale、WireGuard 等隧道方案暴露端口
- ❌ 不设置端口转发到外网
- ❌ 不使用 ngrok、frp 等内网穿透工具

### 3.3 权限控制

**问题**：以管理员/root 权限运行 OpenClaw，攻击者可直接获得系统最高权限。

**建议**：
- [ ] **不以管理员或超级用户权限运行 OpenClaw**
- [ ] 使用普通用户账户运行
- [ ] 避免 `--sudo` 或 `sudo openclaw` 方式启动

**检查方法**：
```bash
# 检查当前运行进程的用户
ps aux | grep openclaw

# 检查是否以 root 运行
id
# 不应显示 uid=0
```

### 3.4 数据隔离

**问题**：OpenClaw 工作区可能包含敏感文件（密码、密钥、文档）。

**建议**：
- [ ] **不在 OpenClaw 工作区存储隐私数据**
- [ ] 敏感文件不放入 `~/.openclaw/workspace/`
- [ ] API密钥、密码、助记词等不存入对话或文件

**安全工作区设计**：
```
~/openclaw-workspace/     # 仅放公开、无敏感的文件
├── projects/            # 项目代码（无密钥）
├── docs/               # 公开文档
└── tmp/               # 临时文件（用完即删）

# 敏感文件存放（Agent 不可访问）
~/secure/
├── .env               # 密钥（不放入 workspace）
├── passwords.txt      # 密码本
└── private/          # 私密文档
```

### 3.5 版本更新

**问题**：旧版本可能存在已知漏洞。

**建议**：
- [ ] **及时更新 OpenClaw 到最新版本**
- [ ] 关注版本发布说明中的安全修复
- [ ] 重大安全更新后重新检查配置

**更新命令**：
```bash
# Homebrew
brew upgrade openclaw

# 检查版本
openclaw --version
```

### 3.6 配对与访问控制

**问题**：飞书/Discord 等渠道的配对策略设置不当。

**建议**：
- [ ] 检查各 channel 的 `connectionMode`
- [ ] 配对策略设置为 `pairing`（需验证码）或 `allowlist`（白名单）
- [ ] **绝对禁止** 设置为 `open`

**检查配置**：
```bash
cat ~/.openclaw/openclaw.json | grep -A5 "channels"
```

---

## 4. 安全配置自检清单

### 4.1 基础检查

| 检查项 | 命令/方法 | 预期结果 |
|--------|----------|---------|
| Gateway 绑定地址 | `grep bind ~/.openclaw/openclaw.json` | `loopback` 或 `127.0.0.1` |
| 端口可访问性 | `curl http://127.0.0.1:18789/` | 可访问 |
| 公网访问 | `curl http://公网IP:18789/` | **应拒绝** |
| 运行用户 | `ps aux \| grep openclaw` | 非 root 用户 |
| 版本状态 | `openclaw --version` | 最新版本 |

### 4.2 高级检查

```bash
# 运行安全审计（如果有）
openclaw security audit

# 深度探测
openclaw security audit --deep

# 自动修复
openclaw security audit --fix
```

---

## 5. 技能（Skills）安全

### 5.1 风险

第三方 Skills 可能包含恶意代码，如：
- 诱导执行 `npm install`、`pip install`
- 远程下载并执行脚本
- 窃取 API keys 或对话内容

### 5.2 建议

- [ ] **不盲目安装** ClawHub（技能商店）中的热门技能
- [ ] 安装前**阅读代码**，确认无恶意操作
- [ ] 使用 `clawhub inspect --files` 检查可疑指令
- [ ] **优先使用官方技能**

### 5.4 安全使用习惯

```
✅ 安全习惯：
- 安装技能前审查代码
- 敏感操作前二次确认
- 定期检查配置文件变更
- 监控异常日志

❌ 危险习惯：
- 执行"一键安装"命令
- 给 Agent 完全的系统权限
- 在对话中发送密码或密钥
- 忽略安全警告
```

---

## 6. 应急响应

### 6.1 发现被入侵的迹象

- 对话中出现未发送的消息
- 文件被意外修改或删除
- 系统性能异常下降
- 收到陌生的认证通知

### 6.2 应急步骤

1. **立即断开网络**（或停止 OpenClaw）
2. **检查日志**：`~/.openclaw/logs/`
3. **重置所有 Token 和密码**
4. **重新安装** OpenClaw
5. **恢复备份数据**（如有）
6. **报告安全事件**

---

## 7. 附录

### 7.1 相关资源

- OpenClaw 官方安全文档
- CNCERT 安全指南原文
- ClawHub 技能审查工具

### 7.2 版本历史

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| 1.0 | 2026-03-22 | 初始版本，基于 CNCERT 指南 |

---

## 8. 技术开发者安全加固

> 适用于使用 OpenClaw 进行开发的技术人员

### 8.1 基础配置加固

**配置文件强密码**：
```json
{
  "gateway": {
    "auth": {
      "mode": "token",
      "token": "使用 32+ 位随机字符串"
    }
  }
}
```

**配对策略**：
- ✅ 设置为 `pairing`（需验证码）
- ✅ 设置为 `allowlist`（白名单）
- ❌ 禁止设置为 `open`

### 8.2 网络暴露控制

- ❌ 不将 Web 管理界面（18789）暴露到公网或局域网
- ❌ 不使用 Tailscale、WireGuard 将端口映射到外网
- ❌ 不使用 ngrok、frp 等内网穿透
- ✅ 确保 `gateway.controlUi.allowInsecureAuth` 为 `false`

### 8.3 运行环境隔离

**方案一：Gateway 整体容器化**
```bash
docker run -d \
  --name openclaw \
  -p 127.0.0.1:18789:18789 \
  -v ~/openclaw-data:/root/.openclaw \
  openclaw/openclaw:latest
```

**方案二：工具执行沙箱隔离**
```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "scope": "agent",
        "workspaceAccess": "rw"
      }
    }
  }
}
```

### 8.4 工具白名单

```json
{
  "plugins": {
    "entries": {
      "shell": { "enabled": false },
      "browser": { "enabled": false }
    }
  }
}
```

### 8.5 文件系统只读挂载

```bash
# 敏感目录只读挂载
docker run -v /etc:/etc:ro -v /usr:/usr:ro ...
```

### 8.6 安全审计

```bash
# 常规检查
openclaw security audit

# 深度探测
openclaw security audit --deep

# 自动修复
openclaw security audit --fix
```

### 8.7 供应链安全

**Skills 安装前审查**：
```bash
clawhub inspect --files <skill-name>
```

**危险信号识别**：
- 诱导执行 `npm install`、`pip install`
- 远程脚本下载
- 发送 API keys 到外部

**禁止事项清单**：
```
❌ 禁止执行：rm -rf /（无确认）
❌ 禁止修改：认证/权限配置
❌ 禁止发送：token/私钥/助记词到外部
❌ 禁止执行：来路不明的"一键安装"命令
```

### 8.8 配置基线

安装完成后立即：
1. 建立配置文件哈希基线
2. 限制核心配置文件访问权限
3. 不将私钥交付给 Agent

---

*本文档根据国家互联网应急中心、中国网络空间安全协会联合发布的《OpenClaw 安全使用实践指南》整理。*
