# -*- coding: utf-8 -*-
"""
AI Tennis 静态图片Web校准工具
功能：
1. 基于Web界面的静态图片校准（避免OpenCV GUI问题）
2. 生成HTML页面供浏览器使用
3. 鼠标点击标记校准点
4. 自动生成配置文件
5. 适用于RK3588等嵌入式平台
"""
import cv2
import numpy as np
import configparser
import signal
import sys
import logging
import base64
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebCalibrator:
    """基于Web界面的静态图片校准工具"""
    
    def __init__(self):
        self.current_frame = None
        self.calibration_points = {}
        
        # 创建输出目录
        Path("images").mkdir(exist_ok=True)
        Path("calibration_data").mkdir(exist_ok=True)
        Path("web_calibration").mkdir(exist_ok=True)
        
        # 校准步骤定义
        self.calibration_steps = [
            # 边界点校准
            {"key": "top_left_xy", "name": "顶部左角(TL)", "color": "#00FFFF", "description": "点击幕布左上角"},
            {"key": "top_right_xy", "name": "顶部右角(TR)", "color": "#00FFFF", "description": "点击幕布右上角"},
            {"key": "mid_left_xy", "name": "中线左点(ML)", "color": "#FFFF00", "description": "点击中线左侧边界"},
            {"key": "mid_center_xy", "name": "中线中心(MC)", "color": "#FFFF00", "description": "点击中线中心点"},
            {"key": "mid_right_xy", "name": "中线右点(MR)", "color": "#FFFF00", "description": "点击中线右侧边界"},
            {"key": "bottom_left_xy", "name": "底部左角(BL)", "color": "#00FFFF", "description": "点击幕布左下角"},
            {"key": "bottom_center_xy", "name": "底部中心(BC)", "color": "#00FFFF", "description": "点击幕布底部中心"},
            {"key": "bottom_right_xy", "name": "底部右角(BR)", "color": "#00FFFF", "description": "点击幕布右下角"},
            
            # 得分圆圈校准
            {"key": "circle_20_1_xy", "name": "20分圈1(灯1)", "color": "#0000FF", "description": "点击左上20分圈中心"},
            {"key": "circle_20_2_xy", "name": "20分圈2(灯2)", "color": "#0000FF", "description": "点击右上20分圈中心"},
            {"key": "circle_30_xy", "name": "30分圈(灯3)", "color": "#00FF00", "description": "点击30分圈中心"},
            {"key": "circle_50_1_xy", "name": "50分圈1(灯4)", "color": "#FF0000", "description": "点击左下50分圈中心"},
            {"key": "circle_50_2_xy", "name": "50分圈2(灯5)", "color": "#FF0000", "description": "点击右下50分圈中心"},
        ]
        
        # 默认圆圈半径
        self.circle_radii = {
            "circle_20": 55,
            "circle_30": 58,
            "circle_50": 53
        }
        
        logger.info("WebCalibrator initialized")

    def image_to_base64(self, image_path):
        """将图片转换为base64编码"""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图片编码失败: {e}")
            return None

    def create_html_page(self, img_base64, width, height, image_name):
        """创建HTML校准页面内容"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tennis 静态图片校准工具</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 20px; color: #333; }}
        .image-container {{ position: relative; display: inline-block; border: 2px solid #ddd; margin: 20px 0; }}
        .calibration-image {{ max-width: 100%; height: auto; cursor: crosshair; }}
        .point-marker {{ position: absolute; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; margin-left: -6px; margin-top: -6px; z-index: 10; }}
        .point-label {{ position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-left: 8px; margin-top: -10px; z-index: 11; }}
        .control-panel {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .current-step {{ font-size: 18px; font-weight: bold; color: #007bff; margin-bottom: 10px; }}
        .buttons {{ margin: 10px 0; }}
        .btn {{ padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }}
        .btn-primary {{ background: #007bff; color: white; }}
        .btn-secondary {{ background: #6c757d; color: white; }}
        .btn-success {{ background: #28a745; color: white; }}
        .btn-danger {{ background: #dc3545; color: white; }}
        .coordinates-list {{ margin-top: 20px; max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: white; }}
        .coordinate-item {{ padding: 5px; border-bottom: 1px solid #eee; font-family: monospace; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: #007bff; transition: width 0.3s ease; }}
        .image-info {{ margin: 10px 0; padding: 10px; background: #e7f3ff; border-radius: 5px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 AI Tennis 静态图片校准工具</h1>
            <p>使用鼠标点击图片标记校准点位置</p>
        </div>
        
        <div class="image-info">
            <strong>图片信息:</strong> {width} x {height} 像素<br>
            <strong>校准点数:</strong> 13个点 (8个边界点 + 5个得分圆圈)
        </div>
        
        <div class="control-panel">
            <div class="current-step" id="currentStep">步骤 1/13: 顶部左角(TL) - 点击幕布左上角</div>
            <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width: 0%"></div></div>
            <div class="buttons">
                <button class="btn btn-secondary" onclick="undoLast()">↶ 撤销上一步</button>
                <button class="btn btn-danger" onclick="resetAll()">🔄 重置所有</button>
                <button class="btn btn-primary" onclick="autoFill()">🤖 使用推荐坐标</button>
                <button class="btn btn-success" onclick="exportConfig()" id="exportBtn" disabled>💾 导出配置</button>
            </div>
        </div>
        
        <div class="image-container" id="imageContainer">
            <img src="data:image/jpeg;base64,{img_base64}" class="calibration-image" onclick="addPoint(event)" alt="校准图片">
        </div>
        
        <div class="coordinates-list">
            <h3>📍 已标记的坐标点:</h3>
            <div id="coordinatesList"></div>
        </div>
    </div>

    <script>
        const calibrationSteps = {json.dumps(self.calibration_steps)};
        const recommendedCoords = {{
            "top_left_xy": [480, 105], "top_right_xy": [1440, 105], "mid_left_xy": [495, 480],
            "mid_center_xy": [960, 480], "mid_right_xy": [1425, 480], "bottom_left_xy": [510, 870],
            "bottom_center_xy": [960, 870], "bottom_right_xy": [1410, 870], "circle_20_1_xy": [720, 270],
            "circle_20_2_xy": [1200, 270], "circle_30_xy": [960, 675], "circle_50_1_xy": [675, 675],
            "circle_50_2_xy": [1245, 675]
        }};
        
        let currentStepIndex = 0, calibrationPoints = {{}}, imageWidth = {width}, imageHeight = {height};
        
        function addPoint(event) {{
            if (currentStepIndex >= calibrationSteps.length) return alert('所有校准点已完成！');
            const rect = event.target.getBoundingClientRect();
            const scaleX = imageWidth / rect.width, scaleY = imageHeight / rect.height;
            const x = Math.round((event.clientX - rect.left) * scaleX);
            const y = Math.round((event.clientY - rect.top) * scaleY);
            const step = calibrationSteps[currentStepIndex];
            calibrationPoints[step.key] = [x, y];
            addVisualMarker(event.clientX - rect.left, event.clientY - rect.top, step);
            updateCoordinatesList(); currentStepIndex++; updateCurrentStep(); updateProgress();
            if (currentStepIndex >= calibrationSteps.length) {{
                document.getElementById('exportBtn').disabled = false;
                alert('🎉 所有校准点已完成！现在可以导出配置文件。');
            }}
        }}
        
        function addVisualMarker(x, y, step) {{
            const container = document.getElementById('imageContainer');
            const marker = document.createElement('div');
            marker.className = 'point-marker';
            marker.style.left = x + 'px'; marker.style.top = y + 'px'; marker.style.backgroundColor = step.color;
            marker.id = 'marker-' + step.key;
            const label = document.createElement('div');
            label.className = 'point-label'; label.style.left = x + 'px'; label.style.top = y + 'px';
            label.textContent = step.name; label.id = 'label-' + step.key;
            container.appendChild(marker); container.appendChild(label);
        }}
        
        function updateCurrentStep() {{
            const stepText = currentStepIndex < calibrationSteps.length ? 
                `步骤 ${{currentStepIndex + 1}}/13: ${{calibrationSteps[currentStepIndex].name}} - ${{calibrationSteps[currentStepIndex].description}}` : '✅ 所有校准点已完成';
            document.getElementById('currentStep').textContent = stepText;
        }}
        
        function updateProgress() {{
            const progress = (currentStepIndex / calibrationSteps.length) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }}
        
        function updateCoordinatesList() {{
            const listElement = document.getElementById('coordinatesList');
            listElement.innerHTML = '';
            for (let i = 0; i < calibrationSteps.length; i++) {{
                const step = calibrationSteps[i], div = document.createElement('div');
                div.className = 'coordinate-item';
                if (calibrationPoints[step.key]) {{
                    const [x, y] = calibrationPoints[step.key];
                    div.innerHTML = `✅ <strong>${{step.name}}</strong>: (${{x}}, ${{y}})`;
                    div.style.color = '#28a745';
                }} else {{
                    div.innerHTML = `⭕ <strong>${{step.name}}</strong>: 未标记`;
                    div.style.color = '#6c757d';
                }}
                listElement.appendChild(div);
            }}
        }}
        
        function undoLast() {{
            if (currentStepIndex > 0) {{
                currentStepIndex--; const step = calibrationSteps[currentStepIndex];
                delete calibrationPoints[step.key];
                const marker = document.getElementById('marker-' + step.key);
                const label = document.getElementById('label-' + step.key);
                if (marker) marker.remove(); if (label) label.remove();
                updateCurrentStep(); updateProgress(); updateCoordinatesList();
                document.getElementById('exportBtn').disabled = true;
            }}
        }}
        
        function resetAll() {{
            if (confirm('确定要重置所有标记点吗？')) {{
                currentStepIndex = 0; calibrationPoints = {{}};
                document.querySelectorAll('.point-marker, .point-label').forEach(marker => marker.remove());
                updateCurrentStep(); updateProgress(); updateCoordinatesList();
                document.getElementById('exportBtn').disabled = true;
            }}
        }}
        
        function autoFill() {{
            if (confirm('使用推荐坐标将覆盖现有标记，确定继续吗？')) {{
                resetAll(); const rect = document.querySelector('.calibration-image').getBoundingClientRect();
                const scaleX = rect.width / imageWidth, scaleY = rect.height / imageHeight;
                for (let i = 0; i < calibrationSteps.length; i++) {{
                    const step = calibrationSteps[i], coords = recommendedCoords[step.key];
                    if (coords) {{
                        calibrationPoints[step.key] = coords;
                        addVisualMarker(coords[0] * scaleX, coords[1] * scaleY, step);
                    }}
                }}
                currentStepIndex = calibrationSteps.length; updateCurrentStep(); updateProgress(); updateCoordinatesList();
                document.getElementById('exportBtn').disabled = false;
            }}
        }}
        
        function exportConfig() {{
            let iniContent = `# AI Tennis Web校准生成的配置文件\\n# 生成时间: ${{new Date().toLocaleString()}}\\n\\n`;
            iniContent += `[Settings]\\ncourt_name = HeHaa AI TENNIS\\ncourt_name_font_size = 3\\ncourt_number = 1\\ncourt_length = 8\\nserve_speed = 25\\ncourt_length_tuneup = 0\\nserve_time = 0\\nmin_girth = 250\\ncircularity = 0.85\\nlocating_time = 0\\nswing_time = 350\\nsave_image = true\\nrtsp_url = rtsp://admin:Mxchip5538@192.168.1.183:554/h264/ch1/main/av_stream\\n\\n`;
            iniContent += `[ScoreBoard]\\npoint_size = 5\\npoint_color = 0, 0, 255\\nline_width = 2\\nline_color = 0, 255, 0\\ncircle_20 = 82\\ncircle_30 = 87\\ncircle_50 = 79\\n`;
            for (const step of calibrationSteps) {{
                if (calibrationPoints[step.key]) {{
                    const [x, y] = calibrationPoints[step.key];
                    iniContent += `${{step.key}} = ${{x}}, ${{y}}\\n`;
                }}
            }}
            iniContent += `ball_color = 0, 204, 0\\ny_offset = 20\\nmultiple = 1\\n`;
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
            downloadFile(iniContent, `config_web_calibrated_${{timestamp}}.ini`, 'text/plain');
            alert('✅ 配置文件已导出！请将下载的config.ini文件放到项目目录');
        }}
        
        function downloadFile(content, filename, mimeType) {{
            const blob = new Blob([content], {{ type: mimeType }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = filename; document.body.appendChild(a); a.click();
            document.body.removeChild(a); URL.revokeObjectURL(url);
        }}
        
        updateCoordinatesList();
    </script>
</body>
</html>'''

    def generate_web_calibration_page(self, image_path):
        """生成Web校准页面"""
        try:
            # 读取图片并获取尺寸
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return None
            
            height, width = img.shape[:2]
            
            # 将图片转换为base64
            img_base64 = self.image_to_base64(image_path)
            if not img_base64:
                return None
            
            # 复制图片到web目录
            import shutil
            image_name = Path(image_path).name
            target_image = f'web_calibration/{image_name}'
            shutil.copy2(image_path, target_image)
            
            # 生成HTML内容
            html_content = self.create_html_page(img_base64, width, height, image_name)
            
            # 保存HTML文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_filename = f'web_calibration/calibration_{timestamp}.html'
            
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Web校准页面已生成: {html_filename}")
            return html_filename
            
        except Exception as e:
            logger.error(f"生成Web页面失败: {e}")
            return None

    def run_calibration(self, image_path):
        """运行Web校准界面"""
        logger.info("生成Web校准页面...")
        
        html_file = self.generate_web_calibration_page(image_path)
        
        if html_file:
            print(f"\n✅ Web校准页面已生成: {html_file}")
            print(f"\n🌐 请在浏览器中打开以下链接进行校准:")
            print(f"   file://{Path(html_file).absolute()}")
            print(f"\n📋 使用说明:")
            print(f"   1. 在浏览器中打开上面的链接")
            print(f"   2. 按照提示依次点击图片中的13个标记点")
            print(f"   3. 完成后点击'导出配置'按钮下载配置文件")
            print(f"   4. 将下载的config.ini文件放到项目目录")
            
            # 尝试自动打开浏览器
            try:
                webbrowser.open(f'file://{Path(html_file).absolute()}')
                print(f"\n🔄 正在尝试自动打开浏览器...")
            except:
                print(f"\n💡 如果浏览器没有自动打开，请手动复制上面的链接到浏览器中")
            
            return True
        else:
            logger.error("生成Web校准页面失败")
            return False


def print_startup_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║             AI Tennis 静态图片Web校准工具                   ║
    ║             Static Image Web Calibration Tool                ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  功能: 基于Web界面的静态图片校准（避免OpenCV GUI问题）        ║
    ║  版本: v2.0 (RK3588优化版)                                  ║
    ║  开发: MXCHIP                                                ║
    ║  日期: 2025-08-06                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    
    【适用场景】
    ✅ RK3588等嵌入式平台
    ✅ OpenCV GUI不兼容的环境
    ✅ 无SSH X11转发的远程连接
    ✅ 任何支持浏览器的环境
    
    【校准流程】
    1️⃣  选择图片文件
    2️⃣  生成Web校准页面
    3️⃣  在浏览器中点击标记点
    4️⃣  导出配置文件
    
    【Web界面操作】
    🖱️  左键点击: 标记校准点
    🔙  撤销按钮: 撤销上一步
    🔄  重置按钮: 重置所有标记
    🤖  推荐坐标: 使用默认坐标
    💾  导出配置: 下载配置文件
    
    """
    print(banner)


def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info('接收到退出信号 (Ctrl+C)')
    sys.exit(0)


def main():
    """主函数"""
    try:
        # 显示启动横幅
        print_startup_banner()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, signal_handler)
        
        # 创建校准器
        calibrator = WebCalibrator()
        
        # 选择图像文件
        print("请选择要校准的图片文件:")
        print("建议使用: images/calibration_source_20250806_091850.jpg (实际摄像头图像)")
        print("或使用: images/test_tennis_screen.jpg (测试图像)")
        
        # 默认图像选项
        default_images = [
            "images/calibration_source_20250806_091850.jpg",
            "images/test_tennis_screen.jpg"
        ]
        
        # 显示可用的默认图像
        available_images = []
        for img in default_images:
            if Path(img).exists():
                available_images.append(img)
        
        if available_images:
            print(f"\n可用的图像文件:")
            for i, img in enumerate(available_images, 1):
                print(f"  {i}. {img}")
            print(f"  0. 手动输入路径")
        
        while True:
            if available_images:
                choice = input(f"\n请选择图像 (1-{len(available_images)}) 或输入 0 手动输入: ").strip()
                
                if choice == "0":
                    image_path = input("请输入图片文件路径: ").strip()
                elif choice.isdigit() and 1 <= int(choice) <= len(available_images):
                    image_path = available_images[int(choice) - 1]
                else:
                    print("无效选择，请重新输入")
                    continue
            else:
                image_path = input("请输入图片文件路径: ").strip()
            
            if image_path and Path(image_path).exists():
                print(f"✅ 选择图像: {image_path}")
                break
            else:
                print("❌ 图片文件不存在，请重新输入")
        
        # 开始校准
        print("\n🌐 生成Web校准页面...")
        calibrator.run_calibration(image_path)
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        return 1
    finally:
        logger.info("程序已退出")
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)