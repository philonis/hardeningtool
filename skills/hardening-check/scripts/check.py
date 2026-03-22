#!/usr/bin/env python3
"""
OpenClaw 安全加固检查脚本
基于 CNCERT《OpenClaw 安全使用实践指南》
"""

import os
import sys
import json
import subprocess
import re
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple

# 颜色定义
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

@dataclass
class CheckResult:
    name: str
    status: str  # PASS, WARN, FAIL, INFO
    message: str

class Counter:
    def __init__(self):
        self.passed = 0
        self.warnings = 0
        self.failed = 0
        self.total = 0

    def add(self, status: str):
        self.total += 1
        if status == 'PASS':
            self.passed += 1
        elif status == 'WARN':
            self.warnings += 1
        elif status == 'FAIL':
            self.failed += 1

def run_cmd(cmd: str) -> Tuple[int, str, str]:
    """执行命令，返回 (returncode, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def print_header(text: str):
    print(f"\n{BLUE}=== {text} ==={NC}")

def print_result(result: CheckResult, counter: Counter):
    counter.add(result.status)
    icon = {'PASS': '✅', 'WARN': '⚠️', 'FAIL': '❌', 'INFO': 'ℹ️'}
    color = {'PASS': GREEN, 'WARN': YELLOW, 'FAIL': RED, 'INFO': BLUE}
    print(f"{color.get(result.status, '')}{icon.get(result.status, '?')} {result.status}{NC}: {result.message}")

def check_gateway_bind(counter: Counter) -> Optional[dict]:
    """检查 Gateway 绑定地址"""
    print_header("1. Gateway 绑定地址检查")
    
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        print_result(CheckResult("gateway_bind", "FAIL", f"配置文件不存在: {config_path}"), counter)
        return None
    
    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print_result(CheckResult("gateway_bind", "FAIL", "配置文件 JSON 格式错误"), counter)
        return None
    
    gateway = config.get("gateway", {})
    bind = gateway.get("bind", "")
    mode = gateway.get("mode", "")
    
    print_result(CheckResult("gateway_bind", "INFO", f"Gateway bind: {bind}, mode: {mode}"), counter)
    
    if bind in ("loopback", "127.0.0.1", "localhost"):
        print_result(CheckResult("gateway_bind", "PASS", "Gateway 仅绑定本地地址"), counter)
    elif bind == "0.0.0.0":
        print_result(CheckResult("gateway_bind", "FAIL", "Gateway 绑定 0.0.0.0（暴露风险）"), counter)
    else:
        print_result(CheckResult("gateway_bind", "WARN", f"Gateway 绑定地址未知: {bind}"), counter)
    
    return gateway

def check_gateway_auth(counter: Counter):
    """检查 Gateway 认证"""
    print_header("2. Gateway 认证检查")
    
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        print_result(CheckResult("gateway_auth", "FAIL", "配置文件不存在"), counter)
        return
    
    try:
        with open(config_path) as f:
            config = json.load(f)
    except:
        print_result(CheckResult("gateway_auth", "FAIL", "配置文件解析失败"), counter)
        return
    
    gateway = config.get("gateway", {})
    auth = gateway.get("auth", {})
    auth_mode = auth.get("mode", "")
    token = auth.get("token", "")
    
    print_result(CheckResult("gateway_auth", "INFO", f"Auth mode: {auth_mode or '未设置'}"), counter)
    
    if auth_mode in ("token", "password"):
        if len(token) >= 32:
            print_result(CheckResult("gateway_auth", "PASS", f"Token 强度足够（{len(token)} 位）"), counter)
        else:
            print_result(CheckResult("gateway_auth", "FAIL", f"Token 强度不足（应 >= 32 位，当前 {len(token)} 位）"), counter)
    else:
        print_result(CheckResult("gateway_auth", "WARN", f"Auth mode: {auth_mode or '未设置'}（建议使用 token）"), counter)

def check_ports(counter: Counter):
    """检查端口监听"""
    print_header("3. 端口监听检查")
    
    for port in [18789, 19890]:
        code, out, _ = run_cmd(f"lsof -i :{port} -sTCP:LISTEN 2>/dev/null | grep LISTEN | head -1")
        if out.strip():
            # 提取绑定地址
            match = re.search(r'\((\S+)\)', out)
            if match:
                bound = match.group(1)
                print_result(CheckResult("ports", "INFO", f"{port} 端口绑定: {bound}"), counter)
                if bound in ("*", "0.0.0.0", "::"):
                    print_result(CheckResult("ports", "FAIL", f"{port} 端口暴露到所有网络接口"), counter)
                else:
                    print_result(CheckResult("ports", "PASS", f"{port} 仅本地监听"), counter)
        else:
            print_result(CheckResult("ports", "INFO", f"{port} 端口未监听"), counter)

def check_public_access(counter: Counter):
    """公网访问测试"""
    print_header("4. 公网访问测试")
    
    # 测试本地
    code, _, _ = run_cmd("curl -s --connect-timeout 5 http://127.0.0.1:18789/ > /dev/null 2>&1")
    if code == 0:
        print_result(CheckResult("public_access", "PASS", "本地访问正常（127.0.0.1:18789）"), counter)
    else:
        print_result(CheckResult("public_access", "WARN", "本地访问失败（服务可能未运行）"), counter)
    
    # 获取公网IP
    code, public_ip, _ = run_cmd("curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo ''")
    public_ip = public_ip.strip()
    
    if public_ip and public_ip != "0.0.0.0":
        print_result(CheckResult("public_access", "INFO", f"本机公网IP: {public_ip}"), counter)
        code, _, _ = run_cmd(f"curl -s --connect-timeout 5 http://{public_ip}:18789/ > /dev/null 2>&1")
        if code == 0:
            print_result(CheckResult("public_access", "FAIL", "公网可访问 18789 端口（严重风险）"), counter)
        else:
            print_result(CheckResult("public_access", "PASS", "公网无法访问 18789"), counter)
    else:
        print_result(CheckResult("public_access", "INFO", "无法获取公网IP，跳过公网测试"), counter)

def check_process_user(counter: Counter):
    """进程用户检查"""
    print_header("5. 进程用户检查")
    
    code, out, _ = run_cmd("ps aux 2>/dev/null | grep -i '[o]penclaw\\|[g]ateway' | grep -v grep")
    if out.strip():
        lines = out.strip().split('\n')
        print_result(CheckResult("process_user", "INFO", f"OpenClaw 进程数: {len(lines)}"), counter)
        for line in lines[:3]:  # 只显示前3个
            parts = line.split()
            if len(parts) >= 3:
                uid = parts[0]
                pid = parts[1]
                cmd = parts[-1][:50]
                print_result(CheckResult("process_user", "INFO", f"  PID {pid}: {cmd}"), counter)
        
        uid = lines[0].split()[0]
        if uid == 'root':
            print_result(CheckResult("process_user", "FAIL", "以 root 权限运行（风险）"), counter)
        else:
            print_result(CheckResult("process_user", "PASS", f"以普通用户运行 ({uid})"), counter)
    else:
        print_result(CheckResult("process_user", "INFO", "未发现运行中的 OpenClaw 进程"), counter)

def check_docker(counter: Counter):
    """Docker 隔离检查"""
    print_header("6. Docker 隔离检查")
    
    code, _, _ = run_cmd("which docker 2>/dev/null")
    if code != 0:
        print_result(CheckResult("docker", "INFO", "Docker 未安装，跳过容器检查"), counter)
        return
    
    code, out, _ = run_cmd("docker ps 2>/dev/null")
    if code != 0:
        print_result(CheckResult("docker", "WARN", "Docker 守护进程不可访问"), counter)
        return
    
    code, out, _ = run_cmd("docker ps --filter 'name=openclaw' --format '{{.Names}}' 2>/dev/null")
    containers = [c for c in out.strip().split('\n') if c]
    
    if containers:
        for c in containers:
            print_result(CheckResult("docker", "PASS", f"OpenClaw 运行在 Docker 容器中: {c}"), counter)
            
            # 检查网络模式
            code, net_mode, _ = run_cmd(f"docker inspect {c} --format '{{{{.HostConfig.NetworkMode}}}}' 2>/dev/null")
            net_mode = net_mode.strip()
            print_result(CheckResult("docker", "INFO", f"容器网络模式: {net_mode}"), counter)
            
            if net_mode in ("bridge", "host"):
                print_result(CheckResult("docker", "WARN", f"网络模式: {net_mode}（建议使用默认bridge）"), counter)
    else:
        print_result(CheckResult("docker", "WARN", "OpenClaw 未在 Docker 中运行"), counter)

def check_tailscale(counter: Counter):
    """网络隧道检查"""
    print_header("7. 网络隧道检查")
    
    checks = [
        ("tailscale", "Tailscale"),
        ("wg", "WireGuard"),
    ]
    
    for cmd_name, name in checks:
        code, _, _ = run_cmd(f"which {cmd_name} 2>/dev/null")
        if code != 0:
            print_result(CheckResult("tunnel", "INFO", f"{name} 未安装"), counter)
            continue
        
        code, _, _ = run_cmd(f"pgrep -x {cmd_name}d 2>/dev/null")
        if code == 0:
            print_result(CheckResult("tunnel", "FAIL", f"{name} 正在运行（可能暴露端口）"), counter)
        else:
            print_result(CheckResult("tunnel", "PASS", f"{name} 未运行"), counter)

def check_skills(counter: Counter):
    """Skills 安全检查"""
    print_header("8. Skills 安全检查")
    
    skills_dir = Path.home() / ".openclaw" / "workspace" / "skills"
    if not skills_dir.exists():
        print_result(CheckResult("skills", "INFO", "Skills 目录不存在"), counter)
        return
    
    skills = [d for d in skills_dir.iterdir() if d.is_dir() and d.name != "skills"]
    
    print_result(CheckResult("skills", "INFO", f"已安装 Skills 数量: {len(skills)}"), counter)
    
    if skills:
        for skill in sorted(skills)[:10]:  # 显示前10个
            size = subprocess.run(
                f"du -sh {skill} 2>/dev/null | cut -f1",
                shell=True, capture_output=True, text=True
            ).stdout.strip()
            print_result(CheckResult("skills", "INFO", f"  - {skill.name} ({size or '?'})"), counter)
        
        if len(skills) > 10:
            print_result(CheckResult("skills", "INFO", f"  ... 还有 {len(skills) - 10} 个"), counter)
        
        print_result(CheckResult("skills", "WARN", "安装第三方 Skills 有供应链风险，建议审查代码"), counter)
        
        # 检查可疑模式
        suspicious = [
            (r"curl.*sh", "远程脚本下载"),
            (r"bash.*install", "shell安装命令"),
            (r"pip.*install.*--user", "用户级pip安装"),
        ]
        
        for skill in skills:
            for pattern, desc in suspicious:
                code, out, _ = run_cmd(f"grep -r '{pattern}' {skill} 2>/dev/null || true")
                if out.strip():
                    print_result(CheckResult("skills", "FAIL", f"发现可疑模式 [{desc}]: {skill.name}"), counter)

def check_workspace(counter: Counter):
    """工作区权限检查"""
    print_header("9. 工作区权限检查")
    
    workspace = Path.home() / ".openclaw" / "workspace"
    if not workspace.exists():
        print_result(CheckResult("workspace", "INFO", "Workspace 目录不存在"), counter)
        return
    
    try:
        stat = workspace.stat()
        import stat as st
        perms = st.filemode(stat.st_mode)
        octal = oct(stat.st_mode)[-3:]
        
        # 检查其他用户权限
        other_perms = octal[-1]
        if other_perms in ('4', '6', '7'):
            print_result(CheckResult("workspace", "WARN", f"Workspace 权限过于宽松: {perms} ({octal})"), counter)
        else:
            print_result(CheckResult("workspace", "PASS", f"Workspace 权限正常: {perms}"), counter)
        
        print_result(CheckResult("workspace", "INFO", f"路径: {workspace}"), counter)
    except Exception as e:
        print_result(CheckResult("workspace", "WARN", f"权限检查失败: {e}"), counter)

def check_security_audit(counter: Counter):
    """OpenClaw 安全审计"""
    print_header("10. OpenClaw 安全审计")
    
    code, _, _ = run_cmd("which openclaw 2>/dev/null")
    if code != 0:
        print_result(CheckResult("security_audit", "INFO", "openclaw CLI 未安装，跳过"), counter)
        return
    
    print_result(CheckResult("security_audit", "INFO", "运行 openclaw security audit..."), counter)
    
    code, out, err = run_cmd("openclaw security audit 2>&1")
    if code == 0:
        print_result(CheckResult("security_audit", "PASS", "安全审计通过"), counter)
    else:
        output = (out + err)[:200]
        print_result(CheckResult("security_audit", "WARN", f"安全审计发现问题: {output}"), counter)

def print_summary(counter: Counter):
    """打印汇总"""
    print_header("检查结果汇总")
    print(f"{GREEN}✅ 通过: {counter.passed}{NC}")
    print(f"{YELLOW}⚠️  警告: {counter.warnings}{NC}")
    print(f"{RED}❌ 失败: {counter.failed}{NC}")
    print(f"\n总计: {counter.total} 项检查")
    
    if counter.failed > 0:
        print(f"\n{RED}存在关键风险项，建议立即修复{NC}")
        return 1
    elif counter.warnings > 0:
        print(f"\n{YELLOW}存在警告项，建议关注{NC}")
        return 0
    else:
        print(f"\n{GREEN}所有检查通过！{NC}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='OpenClaw 安全加固检查')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--config', action='store_true', help='仅配置检查')
    parser.add_argument('--network', action='store_true', help='仅网络安全检查')
    args = parser.parse_args()
    
    print(f"{BLUE}")
    print("╔══════════════════════════════════════════════════╗")
    print("║     OpenClaw 安全加固检查                       ║")
    print("║     基于 CNCERT《安全使用实践指南》             ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"{NC}")
    
    counter = Counter()
    
    if args.config:
        check_gateway_bind(counter)
        check_gateway_auth(counter)
    elif args.network:
        check_ports(counter)
        check_public_access(counter)
        check_tailscale(counter)
    else:
        check_gateway_bind(counter)
        check_gateway_auth(counter)
        check_ports(counter)
        check_public_access(counter)
        check_process_user(counter)
        check_docker(counter)
        check_tailscale(counter)
        check_skills(counter)
        check_workspace(counter)
        check_security_audit(counter)
    
    return print_summary(counter)

if __name__ == "__main__":
    sys.exit(main())
