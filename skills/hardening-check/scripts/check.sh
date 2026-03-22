#!/bin/bash
#
# OpenClaw 安全加固检查脚本
# 基于 CNCERT《OpenClaw 安全使用实践指南》
#

# set -e  # 禁用以防止中间命令失败导致脚本退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 计数器
PASS=0
WARN=0
FAIL=0
TOTAL=0

# 配置路径
OPENCLAW_DIR="${HOME}/.openclaw"
CONFIG_FILE="${OPENCLAW_DIR}/openclaw.json"

# 输出函数
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS++))
    ((TOTAL++))
}

print_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN++))
    ((TOTAL++))
}

print_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL++))
    ((TOTAL++))
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO${NC}: $1"
}

# 检查函数
check_gateway_bind() {
    print_header "1. Gateway 绑定地址检查"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_fail "配置文件不存在: $CONFIG_FILE"
        return
    fi
    
    local bind_addr=$(grep -o '"bind": *"[^"]*"' "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*: *"\([^"]*\)"/\1/')
    local bind_mode=$(grep -o '"mode": *"[^"]*"' "$CONFIG_FILE" 2>/dev/null | grep -i "gateway\|local" | head -1 | sed 's/.*: *"\([^"]*\)"/\1/')
    
    print_info "Gateway bind: $bind_addr"
    
    case "$bind_addr" in
        "loopback"|"127.0.0.1"|"localhost")
            print_pass "Gateway 仅绑定本地地址"
            ;;
        "0.0.0.0")
            print_fail "Gateway 绑定 0.0.0.0（暴露风险）"
            ;;
        *)
            print_warn "Gateway 绑定地址未知: $bind_addr"
            ;;
    esac
}

check_gateway_auth() {
    print_header "2. Gateway 认证检查"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_fail "配置文件不存在"
        return
    fi
    
    local auth_mode=$(grep -o '"mode": *"[^"]*"' "$CONFIG_FILE" 2>/dev/null | grep -A1 "auth" | tail -1 | sed 's/.*: *"\([^"]*\)"/\1/')
    local token=$(grep -o '"token": *"[^"]*"' "$CONFIG_FILE" 2>/dev/null | sed 's/.*: *"\([^"]*\)"/\1/')
    
    print_info "Auth mode: $auth_mode"
    
    if [ "$auth_mode" = "token" ] || [ "$auth_mode" = "password" ]; then
        if [ -n "$token" ] && [ ${#token} -ge 32 ]; then
            print_pass "Token 强度足够（${#token} 位）"
        else
            print_fail "Token 强度不足（应 >= 32 位）"
        fi
    else
        print_warn "Auth mode: $auth_mode（建议使用 token）"
    fi
}

check_ports() {
    print_header "3. 端口监听检查"
    
    # 检查 18789
    local port_18789=$(lsof -i :18789 2>/dev/null | grep LISTEN | head -1)
    if [ -n "$port_18789" ]; then
        local bound_addr=$(echo "$port_18789" | awk '{print $9}' | cut -d: -f1)
        print_info "18789 端口绑定: $bound_addr"
        if [ "$bound_addr" = "*" ] || [ "$bound_addr" = "0.0.0.0" ]; then
            print_fail "18789 端口暴露到所有网络接口"
        else
            print_pass "18789 仅本地监听"
        fi
    else
        print_info "18789 端口未监听（可能未运行）"
    fi
    
    # 检查 19890
    local port_19890=$(lsof -i :19890 2>/dev/null | grep LISTEN | head -1)
    if [ -n "$port_19890" ]; then
        local bound_addr=$(echo "$port_19890" | awk '{print $9}' | cut -d: -f1)
        print_info "19890 端口绑定: $bound_addr"
        if [ "$bound_addr" = "*" ] || [ "$bound_addr" = "0.0.0.0" ]; then
            print_fail "19890 端口暴露到所有网络接口"
        else
            print_pass "19890 仅本地监听"
        fi
    else
        print_info "19890 端口未监听"
    fi
}

check_public_access() {
    print_header "4. 公网访问测试"
    
    # 测试本地
    if curl -s --connect-timeout 5 http://127.0.0.1:18789/ > /dev/null 2>&1; then
        print_pass "本地访问正常（127.0.0.1:18789）"
    else
        print_warn "本地访问失败（服务可能未运行）"
    fi
    
    # 测试公网（如果配置了公网IP）
    local public_ip=""
    if command -v curl >/dev/null 2>&1; then
        public_ip=$(curl -s --connect-timeout 5 ifconfig.me 2>/dev/null || echo "")
    fi
    
    if [ -n "$public_ip" ]; then
        print_info "本机公网IP: $public_ip"
        if curl -s --connect-timeout 5 "http://${public_ip}:18789/" > /dev/null 2>&1; then
            print_fail "公网可访问 18789 端口（严重风险）"
        else
            print_pass "公网无法访问 18789"
        fi
    else
        print_info "无法获取公网IP，跳过公网测试"
    fi
}

check_process_user() {
    print_header "5. 进程用户检查"
    
    local openclaw_procs=$(ps aux 2>/dev/null | grep -i "[o]penclaw\|[g]ateway" | grep -v grep)
    if [ -n "$openclaw_procs" ]; then
        print_info "OpenClaw 进程:"
        echo "$openclaw_procs" | while read line; do
            echo "  $line"
        done
        
        local uid=$(echo "$openclaw_procs" | head -1 | awk '{print $2}')
        if [ "$uid" = "0" ] || [ "$uid" = "root" ]; then
            print_fail "以 root 权限运行（风险）"
        else
            print_pass "以普通用户运行"
        fi
    else
        print_info "未发现运行中的 OpenClaw 进程"
    fi
}

check_docker() {
    print_header "6. Docker 隔离检查"
    
    if ! command -v docker >/dev/null 2>&1; then
        print_info "Docker 未安装，跳过容器检查"
        return
    fi
    
    if ! docker ps >/dev/null 2>&1; then
        print_warn "Docker 守护进程不可访问"
        return
    fi
    
    local openclaw_container=$(docker ps --filter "name=openclaw" --format "{{.Names}}" 2>/dev/null)
    if [ -n "$openclaw_container" ]; then
        print_pass "OpenClaw 运行在 Docker 容器中: $openclaw_container"
        
        # 检查网络模式
        local net_mode=$(docker inspect "$openclaw_container" --format '{{.HostConfig.NetworkMode}}' 2>/dev/null)
        print_info "容器网络模式: $net_mode"
        
        if [ "$net_mode" = "bridge" ] || [ "$net_mode" = "host" ]; then
            print_warn "网络模式: $net_mode（建议使用默认bridge并限制端口映射）"
        fi
        
        # 检查端口映射
        local ports=$(docker port "$openclaw_container" 2>/dev/null)
        if [ -n "$ports" ]; then
            print_info "端口映射:"
            echo "$ports" | while read line; do
                echo "  $line"
            done
        fi
    else
        print_warn "OpenClaw 未在 Docker 中运行"
    fi
}

check_tailscale() {
    print_header "7. 网络隧道检查"
    
    if command -v tailscale >/dev/null 2>&1; then
        if pgrep -x tailscaled >/dev/null 2>&1; then
            print_fail "Tailscale 正在运行（可能暴露端口）"
        else
            print_pass "Tailscale 未运行"
        fi
    else
        print_info "Tailscale 未安装"
    fi
    
    if command -v wg >/dev/null 2>&1; then
        if pgrep -x wireguard >/dev/null 2>&1; then
            print_fail "WireGuard 正在运行"
        else
            print_pass "WireGuard 未运行"
        fi
    else
        print_info "WireGuard 未安装"
    fi
}

check_skills() {
    print_header "8. Skills 安全检查"
    
    local skills_dir="${HOME}/.openclaw/workspace/skills"
    if [ ! -d "$skills_dir" ]; then
        print_info "Skills 目录不存在"
        return
    fi
    
    local skill_count=$(find "$skills_dir" -maxdepth 1 -type d 2>/dev/null | wc -l)
    skill_count=$((skill_count - 1))  # 减去 skills 本身
    
    print_info "已安装 Skills 数量: $skill_count"
    
    if [ "$skill_count" -gt 0 ]; then
        print_info "Skills 列表:"
        find "$skills_dir" -maxdepth 1 -type d -name "*" ! -name "skills" 2>/dev/null | while read dir; do
            local name=$(basename "$dir")
            local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            echo "  - $name ($size)"
        done
        
        print_warn "安装第三方 Skills 有供应链风险，建议审查代码"
    fi
    
    # 检查可疑安装命令
    local suspicious_patterns=("curl.*sh|bash.*install|wget.*install|npm.*install.*-g|pip.*install.*--user")
    for pattern in "${suspicious_patterns[@]}"; do
        local found=$(grep -r "$pattern" "$skills_dir" 2>/dev/null || true)
        if [ -n "$found" ]; then
            print_fail "发现可疑安装命令: $pattern"
        fi
    done
}

check_workspace() {
    print_header "9. 工作区权限检查"
    
    local workspace_dir="${HOME}/.openclaw/workspace"
    if [ -d "$workspace_dir" ]; then
        local perms=$(stat -f "%Sp" "$workspace_dir" 2>/dev/null)
        local owner=$(stat -f "%Su" "$workspace_dir" 2>/dev/null)
        print_info "Workspace: $workspace_dir"
        print_info "权限: $perms, 所有者: $owner"
        
        if [ "$perms" = "drwxr-xr-x" ] || [ "$perms" = "drwxrwxrwx" ]; then
            print_warn "Workspace 权限过于宽松（其他用户可读）"
        else
            print_pass "Workspace 权限正常"
        fi
    else
        print_info "Workspace 目录不存在"
    fi
}

check_security_audit() {
    print_header "10. OpenClaw 安全审计"
    
    if command -v openclaw >/dev/null 2>&1; then
        print_info "运行 openclaw security audit..."
        if openclaw security audit >/dev/null 2>&1; then
            print_pass "安全审计通过"
        else
            print_warn "安全审计发现问题"
        fi
    else
        print_info "openclaw CLI 未安装，跳过"
    fi
}

print_summary() {
    print_header "检查结果汇总"
    echo -e "${GREEN}✅ 通过: $PASS${NC}"
    echo -e "${YELLOW}⚠️  警告: $WARN${NC}"
    echo -e "${RED}❌ 失败: $FAIL${NC}"
    echo -e "\n总计: $TOTAL 项检查"
    
    if [ "$FAIL" -gt 0 ]; then
        echo -e "\n${RED}存在关键风险项，建议立即修复${NC}"
        return 1
    elif [ "$WARN" -gt 0 ]; then
        echo -e "\n${YELLOW}存在警告项，建议关注${NC}"
        return 0
    else
        echo -e "\n${GREEN}所有检查通过！${NC}"
        return 0
    fi
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════╗"
    echo "║     OpenClaw 安全加固检查                       ║"
    echo "║     基于 CNCERT《安全使用实践指南》             ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    local mode="${1:-full}"
    
    case "$mode" in
        --config|config)
            check_gateway_bind
            check_gateway_auth
            ;;
        --network|network)
            check_ports
            check_public_access
            check_tailscale
            ;;
        --process|process)
            check_process_user
            ;;
        --docker|docker)
            check_docker
            ;;
        --skills|skills)
            check_skills
            ;;
        --full|full|"")
            check_gateway_bind
            check_gateway_auth
            check_ports
            check_public_access
            check_process_user
            check_docker
            check_tailscale
            check_skills
            check_workspace
            check_security_audit
            ;;
        *)
            echo "用法: $0 [--config|--network|--process|--docker|--skills|--full]"
            exit 1
            ;;
    esac
    
    print_summary
}

main "$@"
