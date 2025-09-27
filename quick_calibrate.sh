#!/bin/bash
# AI Tennis 快速校准脚本
# 自动化执行环境设置和校准流程

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                AI Tennis 快速校准脚本                         ║"
echo "║                Quick Calibration Script                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Python3是否可用
check_python() {
    log_info "检查Python3环境..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
        log_success "Python3已安装: $PYTHON_VERSION"
        return 0
    else
        log_error "Python3未找到，请先安装Python3"
        return 1
    fi
}

# 运行环境设置
setup_environment() {
    log_info "开始环境设置..."
    
    if python3 setup_environment.py; then
        log_success "环境设置完成"
        return 0
    else
        log_error "环境设置失败"
        return 1
    fi
}

# 生成测试图像
generate_test_image() {
    log_info "生成测试图像..."
    
    if python3 test_manual_calibrate.py; then
        log_success "测试图像生成完成"
        return 0
    else
        log_warning "测试图像生成失败，可能是OpenCV未安装"
        return 1
    fi
}

# 运行简化版校准
run_simple_calibration() {
    log_info "启动简化版校准工具..."
    
    if [ -f "images/test_tennis_screen.jpg" ]; then
        log_info "找到测试图像，将自动使用"
        python3 simple_calibrate.py
    else
        log_warning "未找到测试图像，请手动选择图片文件"
        python3 simple_calibrate.py
    fi
}

# 验证配置
verify_configuration() {
    log_info "验证配置文件..."
    
    if [ -f "config.ini" ]; then
        log_success "配置文件存在"
        log_info "启动配置验证工具..."
        python3 configure.py
    else
        log_warning "配置文件不存在，请先完成校准"
    fi
}

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -s, --setup    仅运行环境设置"
    echo "  -t, --test     仅生成测试图像"
    echo "  -c, --calibrate 仅运行校准工具"
    echo "  -v, --verify   仅验证配置"
    echo "  -a, --all      运行完整流程 (默认)"
    echo ""
    echo "示例:"
    echo "  $0              # 运行完整校准流程"
    echo "  $0 --setup      # 仅设置环境"
    echo "  $0 --calibrate  # 仅运行校准"
}

# 显示完成信息
show_completion() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    校准流程完成                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    log_success "恭喜！AI Tennis校准流程已完成"
    echo ""
    echo "📋 下一步你可以："
    echo "1. 运行 python3 configure.py 验证配置"
    echo "2. 编辑 config.ini 进行参数微调"
    echo "3. 运行 python3 score.py 开始网球识别"
    echo "4. 查看生成的文件："
    echo "   - config.ini (当前配置)"
    echo "   - calibration_data/ (校准数据)" 
    echo "   - images/ (校准图片)"
    echo ""
}

# 主函数
main() {
    # 解析命令行参数
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--setup)
            check_python && setup_environment
            exit $?
            ;;
        -t|--test)
            check_python && generate_test_image
            exit $?
            ;;
        -c|--calibrate)
            check_python && run_simple_calibration
            exit $?
            ;;
        -v|--verify)
            check_python && verify_configuration
            exit $?
            ;;
        -a|--all|"")
            # 完整流程
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    # 运行完整校准流程
    log_info "开始AI Tennis快速校准流程..."
    echo ""
    
    # 步骤1: 检查Python环境
    if ! check_python; then
        exit 1
    fi
    echo ""
    
    # 步骤2: 环境设置
    if ! setup_environment; then
        log_error "环境设置失败，流程中断"
        exit 1
    fi
    echo ""
    
    # 步骤3: 生成测试图像
    generate_test_image
    echo ""
    
    # 步骤4: 运行校准
    log_info "准备运行校准工具..."
    echo "按回车键继续，或按Ctrl+C退出"
    read -r
    
    run_simple_calibration
    echo ""
    
    # 步骤5: 显示完成信息
    show_completion
}

# 执行主函数
main "$@"