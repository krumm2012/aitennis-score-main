# -*- coding: utf-8 -*-
"""
AI Tennis 手动校准工具
功能：
1. 鼠标交互式标点校准
2. 实时预览幕布区域和得分圈
3. 生成新的配置文件
4. 支持从RTSP或图片文件校准
"""
import cv2
import numpy as np
import configparser
import signal
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
import json

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# 初始化GStreamer
Gst.init(None)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ManualCalibrator:
    """手动校准工具主类"""
    
    def __init__(self):
        self.window_name = "AI Tennis 手动校准工具"
        self.current_frame = None
        self.calibration_points = {}
        self.score_circles = {}
        self.current_step = 0
        self.is_calibrating = True
        
        # 创建输出目录
        Path("images").mkdir(exist_ok=True)
        Path("calibration_data").mkdir(exist_ok=True)
        
        # 校准步骤定义
        self.calibration_steps = [
            # 边界点校准
            {"key": "top_left_xy", "name": "顶部左角(TL)", "color": (0, 255, 255), "description": "点击幕布左上角"},
            {"key": "top_right_xy", "name": "顶部右角(TR)", "color": (0, 255, 255), "description": "点击幕布右上角"},
            {"key": "mid_left_xy", "name": "中线左点(ML)", "color": (255, 255, 0), "description": "点击中线左侧边界"},
            {"key": "mid_center_xy", "name": "中线中心(MC)", "color": (255, 255, 0), "description": "点击中线中心点"},
            {"key": "mid_right_xy", "name": "中线右点(MR)", "color": (255, 255, 0), "description": "点击中线右侧边界"},
            {"key": "bottom_left_xy", "name": "底部左角(BL)", "color": (0, 255, 255), "description": "点击幕布左下角"},
            {"key": "bottom_center_xy", "name": "底部中心(BC)", "color": (0, 255, 255), "description": "点击幕布底部中心"},
            {"key": "bottom_right_xy", "name": "底部右角(BR)", "color": (0, 255, 255), "description": "点击幕布右下角"},
            
            # 得分圆圈校准
            {"key": "circle_20_1_xy", "name": "20分圈1(灯1)", "color": (0, 0, 255), "description": "点击左上20分圈中心"},
            {"key": "circle_20_2_xy", "name": "20分圈2(灯2)", "color": (0, 0, 255), "description": "点击右上20分圈中心"},
            {"key": "circle_30_xy", "name": "30分圈(灯3)", "color": (0, 255, 0), "description": "点击30分圈中心"},
            {"key": "circle_50_1_xy", "name": "50分圈1(灯4)", "color": (255, 0, 0), "description": "点击左下50分圈中心"},
            {"key": "circle_50_2_xy", "name": "50分圈2(灯5)", "color": (255, 0, 0), "description": "点击右下50分圈中心"},
        ]
        
        # 默认圆圈半径
        self.circle_radii = {
            "circle_20": 55,
            "circle_30": 58,
            "circle_50": 53
        }
        
        logger.info("ManualCalibrator initialized")

    def mouse_callback(self, event, x, y, flags, param):
        """鼠标点击回调函数"""
        if event == cv2.EVENT_LBUTTONDOWN and self.is_calibrating:
            if self.current_step < len(self.calibration_steps):
                step_info = self.calibration_steps[self.current_step]
                key = step_info["key"]
                name = step_info["name"]
                
                # 记录坐标点
                if key.endswith("_xy"):
                    self.calibration_points[key] = (x, y)
                    logger.info(f"已标记 {name}: ({x}, {y})")
                    
                    # 自动前进到下一步
                    self.current_step += 1
                    
                    # 检查是否完成所有校准
                    if self.current_step >= len(self.calibration_steps):
                        self.is_calibrating = False
                        logger.info("所有校准点已完成！")
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右键点击：后退一步
            if self.current_step > 0:
                self.current_step -= 1
                step_info = self.calibration_steps[self.current_step]
                key = step_info["key"]
                
                # 删除当前点
                if key in self.calibration_points:
                    del self.calibration_points[key]
                
                self.is_calibrating = True
                logger.info(f"已撤销步骤 {self.current_step + 1}")

    def draw_calibration_overlay(self, frame):
        """绘制校准界面覆盖层"""
        overlay = frame.copy()
        
        # 绘制已标记的点
        for i, step_info in enumerate(self.calibration_steps):
            key = step_info["key"]
            name = step_info["name"]
            color = step_info["color"]
            
            if key in self.calibration_points:
                point = self.calibration_points[key]
                # 绘制已完成的点（绿色圆圈）
                cv2.circle(overlay, point, 8, (0, 255, 0), -1)
                cv2.circle(overlay, point, 12, (0, 255, 0), 2)
                
                # 标注名称
                cv2.putText(overlay, name, (point[0] + 15, point[1] - 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(overlay, f"{point}", (point[0] + 15, point[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # 绘制边界区域（如果有足够的点）
        if self.can_draw_boundary():
            self.draw_boundary_preview(overlay)
        
        # 绘制得分圆圈（如果有）
        self.draw_score_circles_preview(overlay)
        
        # 绘制当前步骤指示
        if self.is_calibrating and self.current_step < len(self.calibration_steps):
            current_step = self.calibration_steps[self.current_step]
            instruction = f"步骤 {self.current_step + 1}/{len(self.calibration_steps)}: {current_step['description']}"
            
            # 绘制指示框
            text_size = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(overlay, (10, 10), (text_size[0] + 20, 60), (0, 0, 0), -1)
            cv2.putText(overlay, instruction, (15, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 绘制操作说明
        help_text = [
            "操作说明:",
            "• 左键点击: 标记当前步骤的点",
            "• 右键点击: 撤销上一步",
            "• 'r': 重置所有标记",
            "• 's': 保存配置",
            "• 'q': 退出"
        ]
        
        y_start = frame.shape[0] - len(help_text) * 25 - 10
        for i, text in enumerate(help_text):
            y_pos = y_start + i * 25
            cv2.putText(overlay, text, (15, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 半透明混合
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        return frame

    def can_draw_boundary(self):
        """检查是否有足够的点来绘制边界"""
        required_points = ["top_left_xy", "top_right_xy", "bottom_left_xy", "bottom_right_xy"]
        return all(point in self.calibration_points for point in required_points)

    def draw_boundary_preview(self, frame):
        """绘制边界区域预览"""
        if not self.can_draw_boundary():
            return
        
        # 绘制边界多边形
        boundary_points = np.array([
            self.calibration_points["top_left_xy"],
            self.calibration_points["top_right_xy"], 
            self.calibration_points["bottom_right_xy"],
            self.calibration_points["bottom_left_xy"]
        ], dtype=np.int32)
        
        # 绘制边界线
        cv2.polylines(frame, [boundary_points], True, (0, 255, 0), 3)
        
        # 绘制中线（如果有中线点）
        if all(point in self.calibration_points for point in ["mid_left_xy", "mid_center_xy", "mid_right_xy"]):
            mid_points = np.array([
                self.calibration_points["mid_left_xy"],
                self.calibration_points["mid_center_xy"],
                self.calibration_points["mid_right_xy"]
            ], dtype=np.int32)
            cv2.polylines(frame, [mid_points], False, (255, 255, 0), 3)

    def draw_score_circles_preview(self, frame):
        """绘制得分圆圈预览"""
        circle_configs = [
            ("circle_20_1_xy", self.circle_radii["circle_20"], "20分(1)", (0, 0, 255)),
            ("circle_20_2_xy", self.circle_radii["circle_20"], "20分(2)", (0, 0, 255)),
            ("circle_30_xy", self.circle_radii["circle_30"], "30分(3)", (0, 255, 0)),
            ("circle_50_1_xy", self.circle_radii["circle_50"], "50分(4)", (255, 0, 0)),
            ("circle_50_2_xy", self.circle_radii["circle_50"], "50分(5)", (255, 0, 0)),
        ]
        
        for key, radius, label, color in circle_configs:
            if key in self.calibration_points:
                center = self.calibration_points[key]
                
                # 绘制得分圆圈
                cv2.circle(frame, center, radius, color, 2)
                
                # 绘制十字靶心
                cross_size = 10
                cv2.line(frame, (center[0] - cross_size, center[1]), 
                        (center[0] + cross_size, center[1]), color, 2)
                cv2.line(frame, (center[0], center[1] - cross_size), 
                        (center[0], center[1] + cross_size), color, 2)
                
                # 标注
                cv2.putText(frame, label, (center[0] - 20, center[1] + radius + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def load_from_rtsp(self, rtsp_url):
        """从RTSP流加载图像进行校准"""
        try:
            # 创建GStreamer管道
            pipeline_str = f"rtspsrc location={rtsp_url} ! rtph264depay ! h264parse ! mppvideodec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink sync=false"
            pipeline = Gst.parse_launch(pipeline_str)
            
            # 设置appsink
            appsink = pipeline.get_by_name('sink')
            appsink.set_property("emit-signals", True)
            
            # 启动管道
            pipeline.set_state(Gst.State.PLAYING)
            
            # 等待第一帧
            sample = appsink.emit("pull-sample")
            if sample:
                buf = sample.get_buffer()
                caps = sample.get_caps()
                
                # 获取图像数据
                arr = np.ndarray(
                    shape=(caps.get_structure(0).get_value('height'),
                           caps.get_structure(0).get_value('width'),
                           3),
                    dtype=np.uint8,
                    buffer=buf.extract_dup(0, buf.get_size()))
                
                self.current_frame = arr.copy()
                logger.info("成功从RTSP获取图像")
                
            # 停止管道
            pipeline.set_state(Gst.State.NULL)
            return True
            
        except Exception as e:
            logger.error(f"RTSP加载失败: {e}")
            return False

    def load_from_image(self, image_path):
        """从图片文件加载进行校准"""
        try:
            frame = cv2.imread(image_path)
            if frame is not None:
                self.current_frame = frame
                logger.info(f"成功加载图片: {image_path}")
                return True
            else:
                logger.error(f"无法加载图片: {image_path}")
                return False
        except Exception as e:
            logger.error(f"图片加载失败: {e}")
            return False

    def run_calibration(self):
        """运行校准界面"""
        if self.current_frame is None:
            logger.error("没有可用的图像进行校准")
            return False
        
        # 创建窗口
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 720)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        logger.info("开始手动校准，请按照指示点击各个标记点")
        
        while True:
            # 复制原始帧
            display_frame = self.current_frame.copy()
            
            # 绘制校准覆盖层
            display_frame = self.draw_calibration_overlay(display_frame)
            
            # 显示
            cv2.imshow(self.window_name, display_frame)
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                logger.info("用户退出校准")
                break
            elif key == ord('r'):
                # 重置所有标记
                self.calibration_points.clear()
                self.current_step = 0
                self.is_calibrating = True
                logger.info("已重置所有标记")
            elif key == ord('s'):
                # 保存配置
                if len(self.calibration_points) >= 8:  # 至少需要边界点
                    self.save_configuration()
                else:
                    logger.warning("校准点不足，无法保存配置")
            elif key == 27:  # ESC
                break
        
        cv2.destroyAllWindows()
        return True

    def save_configuration(self):
        """保存校准配置到文件"""
        try:
            # 生成时间戳
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 创建配置解析器
            config = configparser.ConfigParser()
            
            # [Settings] 部分 - 保持原有设置或使用默认值
            config.add_section('Settings')
            config.set('Settings', '# AI Tennis 手动校准生成的配置文件')
            config.set('Settings', f'# 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            config.set('Settings', 'court_name', 'HeHaa AI TENNIS')
            config.set('Settings', 'court_name_font_size', '3')
            config.set('Settings', 'court_number', '1')
            config.set('Settings', 'court_length', '8')
            config.set('Settings', 'serve_speed', '25')
            config.set('Settings', 'court_length_tuneup', '0')
            config.set('Settings', 'serve_time', '0')
            config.set('Settings', 'min_girth', '250')
            config.set('Settings', 'circularity', '0.85')
            config.set('Settings', 'locating_time', '0')
            config.set('Settings', 'swing_time', '350')
            config.set('Settings', 'save_image', 'true')
            config.set('Settings', 'rtsp_url', 'rtsp://admin:Mxchip5538@192.168.20.166:554/h264/ch1/main/av_stream')
            
            # [ScoreBoard] 部分
            config.add_section('ScoreBoard')
            config.set('ScoreBoard', '# 显示参数')
            config.set('ScoreBoard', 'point_size', '5')
            config.set('ScoreBoard', 'point_color', '0, 0, 255')
            config.set('ScoreBoard', 'line_width', '2')
            config.set('ScoreBoard', 'line_color', '0, 255, 0')
            
            # 得分圆圈半径
            config.set('ScoreBoard', '# 得分圆圈半径')
            config.set('ScoreBoard', 'circle_20', str(self.circle_radii["circle_20"]))
            config.set('ScoreBoard', 'circle_30', str(self.circle_radii["circle_30"]))
            config.set('ScoreBoard', 'circle_50', str(self.circle_radii["circle_50"]))
            
            # 校准坐标
            config.set('ScoreBoard', '# 校准坐标 - 手动标记生成')
            
            # 保存所有校准点
            for key, point in self.calibration_points.items():
                config.set('ScoreBoard', key, f'{point[0]}, {point[1]}')
            
            # 其他参数
            config.set('ScoreBoard', '# 其他参数')
            config.set('ScoreBoard', 'ball_color', '0, 204, 0')
            config.set('ScoreBoard', 'y_offset', '20')
            config.set('ScoreBoard', 'multiple', '1')
            
            # 保存配置文件
            config_filename = f'config_manual_calibrated_{timestamp}.ini'
            with open(config_filename, 'w', encoding='utf-8') as f:
                config.write(f)
            
            # 也保存为当前配置
            with open('config.ini', 'w', encoding='utf-8') as f:
                config.write(f)
            
            # 保存校准数据的JSON格式（便于后续处理）
            calibration_data = {
                'timestamp': timestamp,
                'calibration_points': self.calibration_points,
                'circle_radii': self.circle_radii,
                'image_size': self.current_frame.shape[:2] if self.current_frame is not None else None
            }
            
            json_filename = f'calibration_data/calibration_{timestamp}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(calibration_data, f, indent=2, ensure_ascii=False)
            
            # 保存校准图片
            if self.current_frame is not None:
                calibrated_image = self.current_frame.copy()
                self.draw_calibration_overlay(calibrated_image)
                
                image_filename = f'images/manual_calibration_{timestamp}.jpg'
                cv2.imwrite(image_filename, calibrated_image)
            
            logger.info(f"配置已保存:")
            logger.info(f"  配置文件: {config_filename}")
            logger.info(f"  当前配置: config.ini")
            logger.info(f"  校准数据: {json_filename}")
            logger.info(f"  校准图片: {image_filename}")
            
            # 显示校准摘要
            self.print_calibration_summary()
            
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def print_calibration_summary(self):
        """打印校准摘要"""
        print("\n" + "="*60)
        print("           手动校准完成摘要")
        print("="*60)
        
        print(f"\n【校准时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"【校准点数】: {len(self.calibration_points)}")
        
        if self.current_frame is not None:
            h, w = self.current_frame.shape[:2]
            print(f"【图像尺寸】: {w} x {h}")
        
        print(f"\n【边界坐标】")
        boundary_keys = ["top_left_xy", "top_right_xy", "mid_left_xy", "mid_center_xy", 
                        "mid_right_xy", "bottom_left_xy", "bottom_center_xy", "bottom_right_xy"]
        
        for key in boundary_keys:
            if key in self.calibration_points:
                point = self.calibration_points[key]
                name = next((step["name"] for step in self.calibration_steps if step["key"] == key), key)
                print(f"  {name}: {point}")
        
        print(f"\n【得分区域】")
        score_keys = ["circle_20_1_xy", "circle_20_2_xy", "circle_30_xy", "circle_50_1_xy", "circle_50_2_xy"]
        
        for key in score_keys:
            if key in self.calibration_points:
                point = self.calibration_points[key]
                name = next((step["name"] for step in self.calibration_steps if step["key"] == key), key)
                print(f"  {name}: {point}")
        
        print("="*60)
        print("配置文件已生成，可以开始使用系统进行识别测试")
        print("="*60 + "\n")


def print_startup_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 AI Tennis 手动校准工具                      ║
    ║                Manual Calibration Tool                       ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  功能: 鼠标交互式标点校准和配置文件生成                      ║
    ║  版本: v1.0                                                  ║
    ║  开发: MXCHIP                                                ║
    ║  日期: 2025-01-08                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    
    【校准流程】
    1️⃣  选择图像源（RTSP流或图片文件）
    2️⃣  按顺序点击各个标记点
    3️⃣  实时预览边界和得分区域
    4️⃣  保存生成新的配置文件
    
    【操作说明】
    🖱️  左键点击: 标记当前步骤的点
    🖱️  右键点击: 撤销上一步操作
    ⌨️  'r' 键: 重置所有标记
    ⌨️  's' 键: 保存当前配置
    ⌨️  'q' 键: 退出程序
    
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
        calibrator = ManualCalibrator()
        
        # 选择图像源
        print("请选择校准图像源:")
        print("1. RTSP视频流 (从摄像头获取当前画面)")
        print("2. 图片文件 (从本地图片文件)")
        
        while True:
            choice = input("请输入选择 (1 或 2): ").strip()
            
            if choice == '1':
                # RTSP模式
                rtsp_url = input("请输入RTSP地址 (直接回车使用默认): ").strip()
                if not rtsp_url:
                    rtsp_url = "rtsp://admin:Mxchip5538@192.168.20.166:554/h264/ch1/main/av_stream"
                
                print(f"正在连接RTSP: {rtsp_url}")
                if calibrator.load_from_rtsp(rtsp_url):
                    break
                else:
                    print("RTSP连接失败，请重新选择")
                    
            elif choice == '2':
                # 图片文件模式
                image_path = input("请输入图片文件路径: ").strip()
                if calibrator.load_from_image(image_path):
                    break
                else:
                    print("图片加载失败，请重新选择")
            else:
                print("无效选择，请输入 1 或 2")
        
        # 开始校准
        print("\n开始手动校准...")
        print("请按照屏幕指示依次点击各个标记点")
        
        calibrator.run_calibration()
        
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