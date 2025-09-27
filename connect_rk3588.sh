#!/bin/bash
# RK3588 AI Tennis 快速连接脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                RK3588 AI Tennis 连接工具                     ║${NC}"
echo -e "${BLUE}║                RK3588 Connection Tool                         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查网络连通性
echo -e "${BLUE}🔍 检查RK3588设备连通性...${NC}"
if ping -c 2 192.168.1.99 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ RK3588设备网络连通正常${NC}"
else
    echo -e "${RED}❌ RK3588设备网络不通，请检查：${NC}"
    echo -e "${YELLOW}   1. 设备是否开机${NC}"
    echo -e "${YELLOW}   2. 网络连接是否正常${NC}"
    echo -e "${YELLOW}   3. IP地址是否正确 (192.168.1.99)${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}请选择连接方式:${NC}"
echo -e "${YELLOW}1.${NC} 直接连接到RK3588"
echo -e "${YELLOW}2.${NC} 连接并进入AI Tennis工作目录"
echo -e "${YELLOW}3.${NC} 运行环境检查"
echo -e "${YELLOW}4.${NC} 运行简化版校准工具"
echo -e "${YELLOW}5.${NC} 运行完整版校准工具"
echo -e "${YELLOW}6.${NC} 查看项目文件列表"
echo -e "${YELLOW}7.${NC} 同步本地文件到RK3588"
echo -e "${YELLOW}8.${NC} 从RK3588下载文件到本地"
echo -e "${YELLOW}9.${NC} 显示Cursor Remote-SSH使用说明"
echo ""

read -p "请输入选择 (1-9): " choice

case $choice in
    1)
        echo -e "${GREEN}🔗 连接到RK3588...${NC}"
        ssh rk3588-aitennis
        ;;
    2)
        echo -e "${GREEN}🔗 连接到RK3588并进入工作目录...${NC}"
        ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && bash"
        ;;
    3)
        echo -e "${GREEN}🔍 运行环境检查...${NC}"
        ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 demo_info.py"
        ;;
    4)
        echo -e "${GREEN}🎯 运行简化版校准工具...${NC}"
        echo -e "${YELLOW}注意：需要图片文件进行校准${NC}"
        ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 simple_calibrate.py"
        ;;
    5)
        echo -e "${GREEN}🎮 运行完整版校准工具...${NC}"
        echo -e "${YELLOW}注意：支持RTSP视频流和图片文件${NC}"
        ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 manual_calibrate.py"
        ;;
    6)
        echo -e "${GREEN}📁 查看项目文件列表...${NC}"
        ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && ls -la"
        ;;
    7)
        echo -e "${GREEN}📤 同步本地文件到RK3588...${NC}"
        echo -e "${YELLOW}当前目录所有Python文件将被上传${NC}"
        read -p "确认继续? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            scp *.py rk3588-aitennis:/home/blueberry/aitennis/score/
            scp *.md rk3588-aitennis:/home/blueberry/aitennis/score/
            scp *.sh rk3588-aitennis:/home/blueberry/aitennis/score/
            echo -e "${GREEN}✅ 文件同步完成${NC}"
        else
            echo -e "${YELLOW}❌ 同步已取消${NC}"
        fi
        ;;
    8)
        echo -e "${GREEN}📥 从RK3588下载文件...${NC}"
        echo "选择要下载的内容:"
        echo "1. 配置文件 (config.ini)"
        echo "2. 校准数据 (calibration_data/)"
        echo "3. 校准图片 (images/)"
        echo "4. 日志文件 (*.log)"
        read -p "请输入选择 (1-4): " download_choice
        
        case $download_choice in
            1)
                scp rk3588-aitennis:/home/blueberry/aitennis/score/config*.ini ./
                ;;
            2)
                scp -r rk3588-aitennis:/home/blueberry/aitennis/score/calibration_data/ ./
                ;;
            3)
                scp -r rk3588-aitennis:/home/blueberry/aitennis/score/images/ ./
                ;;
            4)
                scp rk3588-aitennis:/home/blueberry/aitennis/score/*.log ./
                ;;
            *)
                echo -e "${RED}❌ 无效选择${NC}"
                ;;
        esac
        ;;
    9)
        echo -e "${GREEN}📖 Cursor Remote-SSH使用说明${NC}"
        echo ""
        echo -e "${YELLOW}1. 打开Cursor编辑器${NC}"
        echo -e "${YELLOW}2. 按 Cmd+Shift+P (macOS) 打开命令面板${NC}"
        echo -e "${YELLOW}3. 输入 'Remote-SSH: Connect to Host...'${NC}"
        echo -e "${YELLOW}4. 选择 'rk3588-aitennis'${NC}"
        echo -e "${YELLOW}5. 输入密码 'blueberry'${NC}"
        echo -e "${YELLOW}6. 打开工作目录: /home/blueberry/aitennis/score${NC}"
        echo ""
        echo -e "${BLUE}详细说明请查看: RK3588_SSH_SETUP.md${NC}"
        ;;
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac