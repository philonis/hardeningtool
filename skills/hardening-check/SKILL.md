---
name: hardening-check
description: OpenClaw 安全加固检查工具。检查 OpenClaw 配置是否满足 CNCERT 安全指南要求。当用户说"安全检查"、"加固检查"、"检查 OpenClaw"、"运行 hardening check"时触发。执行 hardening-check.sh 脚本进行自动化安全检查。
---

# OpenClaw 安全加固检查

## 快速开始

```bash
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh
```

## 检查项目

### 1. 基础配置检查
- Gateway 绑定地址（应为 loopback/127.0.0.1）
- Gateway Token 强度
- 飞书配对策略

### 2. 网络安全检查
- 18789/19890 端口绑定地址
- 公网访问测试（curl）
- Tailscale/WireGuard 状态

### 3. 进程权限检查
- 运行用户（应为非 root）
- 进程 uid 检查

### 4. Docker 隔离检查（如安装）
- Docker 是否安装
- OpenClaw 是否运行在容器中
- 容器网络模式

### 5. 文件系统检查
- workspace 权限
- 敏感文件访问控制

### 6. Skills 安全检查
- 已安装 Skills 列表
- 可疑 Skills 警告

## 执行方式

### 完整检查
```bash
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh --full
```

### 分类检查
```bash
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh --config   # 基础配置
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh --network  # 网络安全
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh --process  # 进程权限
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh --docker   # Docker隔离
bash ~/projects/hardeningtool/skills/hardening-check/scripts/check.sh --skills   # Skills安全
```

### 输出格式
- `--json`：JSON 格式输出
- `--report`：生成报告文件

## 返回值

| 返回值 | 含义 |
|-------|------|
| 0 | 所有检查通过 |
| 1 | 有关键风险项 |
| 2 | 检查执行失败 |

## 依赖

- `grep`, `cat`, `awk`（基础）
- `docker`（可选，用于容器检查）
- `curl`（可选，用于网络测试）
- `openclaw` CLI（用于 `security audit` 命令）

## 常见问题

**Q: 提示 "docker not found"**
A: Docker 未安装或不在 PATH 中，可跳过 Docker 检查

**Q: 公网访问测试失败**
A: 网络环境限制，不影响本地安全评估
