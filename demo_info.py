#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Tennis 项目演示信息
显示项目功能和工具说明
"""

def print_project_banner():
    """显示项目横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                AI Tennis 智能网球计分系统                     ║
    ║                Intelligent Tennis Scoring System              ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║  🎾 基于OpenCV的网球击打幕布识别系统                          ║
    ║  🏗️  支持RK3588硬件加速和RTSP视频流                           ║
    ║  🎯 实时计分、球速计算和区域判断                              ║
    ║  🖱️  新增手动校准工具和配置管理                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def show_tools_overview():
    """显示工具概览"""
    print("\n📁 项目工具一览")
    print("=" * 50)
    
    tools = [
        {
            "name": "🔧 setup_environment.py",
            "description": "环境设置和依赖安装工具",
            "usage": "python3 setup_environment.py",
            "features": ["自动检查Python版本", "智能安装依赖", "创建测试图像"]
        },
        {
            "name": "🎯 simple_calibrate.py", 
            "description": "简化版手动校准工具（推荐）",
            "usage": "python3 simple_calibrate.py",
            "features": ["鼠标交互标点", "实时预览效果", "仅需OpenCV"]
        },
        {
            "name": "🎮 manual_calibrate.py",
            "description": "完整版手动校准工具",
            "usage": "python3 manual_calibrate.py", 
            "features": ["支持RTSP流", "完整功能", "生产环境推荐"]
        },
        {
            "name": "👁️ configure.py",
            "description": "配置查看和验证工具",
            "usage": "python3 configure.py",
            "features": ["实时显示配置", "坐标标注", "区域可视化"]
        },
        {
            "name": "🖼️ test_manual_calibrate.py",
            "description": "测试图像生成工具",
            "usage": "python3 test_manual_calibrate.py",
            "features": ["生成标准测试图", "推荐校准坐标", "快速验证"]
        },
        {
            "name": "🏃 score.py",
            "description": "主要识别和计分程序",
            "usage": "python3 score.py",
            "features": ["实时网球识别", "自动计分", "API数据提交"]
        }
    ]
    
    for tool in tools:
        print(f"\n{tool['name']}")
        print(f"   描述: {tool['description']}")
        print(f"   用法: {tool['usage']}")
        print(f"   特性: {' | '.join(tool['features'])}")

def show_calibration_workflow():
    """显示校准工作流程"""
    print("\n🔄 校准工作流程")
    print("=" * 50)
    
    workflow = [
        ("1️⃣", "环境设置", "运行 setup_environment.py 检查和安装依赖"),
        ("2️⃣", "生成测试图", "运行 test_manual_calibrate.py 创建标准测试图像"),
        ("3️⃣", "手动校准", "运行 simple_calibrate.py 进行交互式标点校准"),
        ("4️⃣", "验证配置", "运行 configure.py 查看校准结果"),
        ("5️⃣", "开始识别", "运行 score.py 开始网球识别和计分")
    ]
    
    for step, title, description in workflow:
        print(f"\n{step} {title}")
        print(f"   {description}")

def show_calibration_points():
    """显示校准点说明"""
    print("\n🎯 校准点说明 (共13个关键点)")
    print("=" * 50)
    
    boundary_points = [
        ("TL", "顶部左角", "幕布左上角边界点"),
        ("TR", "顶部右角", "幕布右上角边界点"), 
        ("ML", "中线左点", "中线与左边界交点"),
        ("MC", "中线中心", "中线中心点"),
        ("MR", "中线右点", "中线与右边界交点"),
        ("BL", "底部左角", "幕布左下角边界点"),
        ("BC", "底部中心", "底部边界中心点"),
        ("BR", "底部右角", "幕布右下角边界点")
    ]
    
    score_circles = [
        ("灯1", "20分圈1", "左上角20分圆圈中心"),
        ("灯2", "20分圈2", "右上角20分圆圈中心"),
        ("灯3", "30分圈", "中央30分圆圈中心"),
        ("灯4", "50分圈1", "左下角50分圆圈中心"),
        ("灯5", "50分圈2", "右下角50分圆圈中心")
    ]
    
    print("\n📍 边界点 (8个):")
    for code, name, desc in boundary_points:
        print(f"   {code}: {name} - {desc}")
    
    print("\n🎯 得分圆圈 (5个):")
    for light, name, desc in score_circles:
        print(f"   {light}: {name} - {desc}")

def show_test_coordinates():
    """显示测试图像推荐坐标"""
    print("\n📐 测试图像推荐坐标")
    print("=" * 50)
    print("(使用 test_manual_calibrate.py 生成的测试图像)")
    
    coords = [
        ("边界点", [
            ("顶部左角(TL)", "(320, 70)"),
            ("顶部右角(TR)", "(960, 70)"),
            ("中线左点(ML)", "(330, 320)"),
            ("中线中心(MC)", "(640, 320)"),
            ("中线右点(MR)", "(950, 320)"),
            ("底部左角(BL)", "(340, 580)"),
            ("底部中心(BC)", "(640, 580)"),
            ("底部右角(BR)", "(940, 580)")
        ]),
        ("得分圆圈", [
            ("20分圈1(灯1)", "(480, 180)"),
            ("20分圈2(灯2)", "(800, 180)"),
            ("30分圈(灯3)", "(640, 450)"),
            ("50分圈1(灯4)", "(450, 450)"),
            ("50分圈2(灯5)", "(830, 450)")
        ])
    ]
    
    for section, points in coords:
        print(f"\n📌 {section}:")
        for name, coord in points:
            print(f"   {name}: {coord}")

def show_output_files():
    """显示输出文件说明"""
    print("\n📄 校准输出文件")
    print("=" * 50)
    
    files = [
        ("config.ini", "当前系统配置文件", "主要配置，被系统直接使用"),
        ("config_*_calibrated_*.ini", "带时间戳的配置备份", "保留历史校准记录"),
        ("calibration_data/calibration_*.json", "JSON格式校准数据", "包含坐标和元数据"),
        ("images/*_calibration_*.jpg", "校准结果图片", "带标记的可视化校准图")
    ]
    
    for filename, description, usage in files:
        print(f"\n📁 {filename}")
        print(f"   描述: {description}")
        print(f"   用途: {usage}")

def show_next_steps():
    """显示下一步操作"""
    print("\n🚀 推荐操作步骤")
    print("=" * 50)
    
    steps = [
        "📖 阅读 QUICK_START.md 详细指南",
        "🔧 运行 python3 setup_environment.py 设置环境",
        "🖼️ 运行 python3 test_manual_calibrate.py 生成测试图",
        "🎯 运行 python3 simple_calibrate.py 开始校准",
        "👁️ 运行 python3 configure.py 验证配置",
        "📝 编辑 config.ini 进行参数微调",
        "🏃 运行 python3 score.py 开始识别测试"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")

def show_troubleshooting():
    """显示故障排除提示"""
    print("\n🔧 常见问题解决")
    print("=" * 50)
    
    issues = [
        ("ModuleNotFoundError: No module named 'cv2'", 
         "pip3 install opencv-python"),
        ("externally-managed-environment", 
         "python3 -m venv aitennis_env && source aitennis_env/bin/activate"),
        ("RTSP连接失败", 
         "使用 simple_calibrate.py 进行图片文件校准"),
        ("Permission denied", 
         "sudo pip3 install 或使用虚拟环境"),
        ("校准点不准确", 
         "重新运行校准工具，仔细点击目标中心")
    ]
    
    for problem, solution in issues:
        print(f"\n❌ 问题: {problem}")
        print(f"✅ 解决: {solution}")

def main():
    """主函数"""
    print_project_banner()
    show_tools_overview()
    show_calibration_workflow() 
    show_calibration_points()
    show_test_coordinates()
    show_output_files()
    show_next_steps()
    show_troubleshooting()
    
    print("\n" + "=" * 65)
    print("🎉 准备好开始您的AI Tennis校准之旅了吗？")
    print("首先运行: python3 setup_environment.py")
    print("详细指南: cat QUICK_START.md")
    print("=" * 65)

if __name__ == "__main__":
    main()