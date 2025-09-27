#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Tennis 环境设置脚本
自动检查和安装必要的依赖
"""
import sys
import subprocess
import platform
import os
from pathlib import Path

def print_banner():
    """显示设置横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                AI Tennis 环境设置工具                         ║
    ║                Environment Setup Tool                          ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  自动检查和安装项目依赖                                       ║
    ║  版本: v1.0                                                   ║
    ║  开发: MXCHIP                                                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    print("\n🔍 检查Python版本...")
    version = sys.version_info
    print(f"   Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ 错误: 需要Python 3.7或更高版本")
        return False
    
    print("✅ Python版本检查通过")
    return True

def check_module_availability():
    """检查模块可用性"""
    print("\n🔍 检查已安装的模块...")
    
    modules = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'requests': 'requests',
        'configparser': '内置模块'
    }
    
    available = {}
    missing = []
    
    for module, package in modules.items():
        try:
            __import__(module)
            print(f"✅ {module} - 已安装")
            available[module] = True
        except ImportError:
            print(f"❌ {module} - 未安装 (需要: {package})")
            available[module] = False
            if package != '内置模块':
                missing.append(package)
    
    return available, missing

def install_packages(packages):
    """安装缺失的包"""
    if not packages:
        print("\n✅ 所有必需的包都已安装")
        return True
    
    print(f"\n📦 需要安装的包: {', '.join(packages)}")
    
    # 检测操作系统
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("\n🍎 检测到macOS系统")
        return install_packages_macos(packages)
    elif system == "linux":  # Linux
        print("\n🐧 检测到Linux系统")
        return install_packages_linux(packages)
    else:
        print(f"\n❓ 未知操作系统: {system}")
        return install_packages_generic(packages)

def install_packages_macos(packages):
    """在macOS上安装包"""
    print("\n选择安装方式:")
    print("1. 使用pip3 (推荐)")
    print("2. 使用虚拟环境")
    print("3. 使用--break-system-packages标志")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        return install_with_pip3(packages)
    elif choice == "2":
        return install_with_venv(packages)
    elif choice == "3":
        return install_with_break_system_packages(packages)
    else:
        print("❌ 无效选择")
        return False

def install_packages_linux(packages):
    """在Linux上安装包"""
    print("\n选择安装方式:")
    print("1. 使用apt-get (Ubuntu/Debian)")
    print("2. 使用pip3")
    print("3. 使用虚拟环境")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == "1":
        return install_with_apt(packages)
    elif choice == "2":
        return install_with_pip3(packages)
    elif choice == "3":
        return install_with_venv(packages)
    else:
        print("❌ 无效选择")
        return False

def install_packages_generic(packages):
    """通用安装方法"""
    return install_with_pip3(packages)

def install_with_pip3(packages):
    """使用pip3安装"""
    print("\n📦 使用pip3安装包...")
    
    try:
        cmd = ["pip3", "install"] + packages
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ pip3安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ pip3安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def install_with_venv(packages):
    """使用虚拟环境安装"""
    print("\n🏠 创建虚拟环境...")
    
    venv_path = Path("aitennis_env")
    
    try:
        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("✅ 虚拟环境创建成功")
        
        # 确定激活脚本路径
        if platform.system().lower() == "windows":
            pip_path = venv_path / "Scripts" / "pip"
        else:
            pip_path = venv_path / "bin" / "pip"
        
        # 安装包
        cmd = [str(pip_path), "install"] + packages
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        print("✅ 虚拟环境安装成功")
        print(f"\n📋 使用虚拟环境的方法:")
        if platform.system().lower() == "windows":
            print(f"   {venv_path}\\Scripts\\activate")
        else:
            print(f"   source {venv_path}/bin/activate")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境安装失败: {e}")
        return False

def install_with_break_system_packages(packages):
    """使用--break-system-packages标志安装"""
    print("\n⚠️  使用--break-system-packages标志...")
    print("注意: 这可能会影响系统Python环境")
    
    confirm = input("确认继续? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ 取消安装")
        return False
    
    try:
        cmd = ["pip3", "install", "--break-system-packages"] + packages
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False

def install_with_apt(packages):
    """使用apt-get安装（Ubuntu/Debian）"""
    print("\n📦 使用apt-get安装系统包...")
    
    # OpenCV和numpy的系统包名
    apt_packages = []
    for package in packages:
        if package == "opencv-python":
            apt_packages.append("python3-opencv")
        elif package == "numpy":
            apt_packages.append("python3-numpy")
        elif package == "requests":
            apt_packages.append("python3-requests")
    
    if apt_packages:
        try:
            cmd = ["sudo", "apt-get", "install", "-y"] + apt_packages
            print(f"执行命令: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            print("✅ apt-get安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ apt-get安装失败: {e}")
            return False
    else:
        print("❌ 没有找到对应的系统包")
        return False

def create_test_image():
    """创建测试图像"""
    print("\n🖼️  创建测试图像...")
    
    try:
        import cv2
        import numpy as np
        
        # 创建images目录
        Path("images").mkdir(exist_ok=True)
        
        # 创建 1280x720 的测试图像
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # 绘制蓝色背景（模拟网球幕布）
        cv2.rectangle(img, (300, 50), (980, 600), (139, 69, 19), -1)
        
        # 绘制边界线（绿色）
        cv2.line(img, (320, 70), (960, 70), (0, 255, 0), 3)
        cv2.line(img, (340, 580), (940, 580), (0, 255, 0), 3)
        cv2.line(img, (320, 70), (340, 580), (0, 255, 0), 3)
        cv2.line(img, (960, 70), (940, 580), (0, 255, 0), 3)
        
        # 绘制中线
        cv2.line(img, (330, 320), (950, 320), (255, 255, 0), 3)
        
        # 绘制得分圆圈（白色圆圈）
        cv2.circle(img, (480, 180), 55, (255, 255, 255), 3)
        cv2.circle(img, (800, 180), 55, (255, 255, 255), 3)
        cv2.circle(img, (640, 450), 58, (255, 255, 255), 3)
        cv2.circle(img, (450, 450), 53, (255, 255, 255), 3)
        cv2.circle(img, (830, 450), 53, (255, 255, 255), 3)
        
        # 添加得分标注
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, "20", (470, 185), font, 1, (255, 255, 255), 2)
        cv2.putText(img, "20", (790, 185), font, 1, (255, 255, 255), 2)
        cv2.putText(img, "30", (630, 455), font, 1, (255, 255, 255), 2)
        cv2.putText(img, "50", (440, 455), font, 1, (255, 255, 255), 2)
        cv2.putText(img, "50", (820, 455), font, 1, (255, 255, 255), 2)
        
        # 保存图像
        cv2.imwrite("images/test_tennis_screen.jpg", img)
        print("✅ 测试图像创建成功: images/test_tennis_screen.jpg")
        return True
        
    except Exception as e:
        print(f"❌ 测试图像创建失败: {e}")
        return False

def print_next_steps():
    """显示下一步操作"""
    print("\n🎉 环境设置完成！")
    print("\n📋 下一步操作:")
    print("1. 使用简化版校准工具:")
    print("   python3 simple_calibrate.py")
    print("\n2. 使用完整版校准工具:")
    print("   python3 manual_calibrate.py")
    print("\n3. 查看配置:")
    print("   python3 configure.py")
    print("\n4. 阅读快速开始指南:")
    print("   cat QUICK_START.md")

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查模块可用性
    available, missing = check_module_availability()
    
    # 安装缺失的包
    if missing:
        if not install_packages(missing):
            print("\n❌ 包安装失败，请手动安装:")
            for package in missing:
                print(f"   pip3 install {package}")
            sys.exit(1)
    
    # 重新检查
    print("\n🔍 重新检查模块可用性...")
    available, still_missing = check_module_availability()
    
    if still_missing:
        print(f"\n❌ 仍有模块缺失: {still_missing}")
        print("请手动安装这些模块")
        sys.exit(1)
    
    # 创建测试图像
    if available.get('cv2', False):
        create_test_image()
    
    # 显示下一步操作
    print_next_steps()

if __name__ == "__main__":
    main()