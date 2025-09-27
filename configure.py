# -*- coding: utf-8 -*-
"""
AI Tennis 识别区域配置工具
功能：
1. 实时显示RTSP视频流
2. 可视化显示所有得分区域和边界
3. 生成配置校准图片
4. 提供坐标标注和区域识别
"""
import cv2
import numpy as np
import signal
import sys
import logging
from datetime import datetime
from pathlib import Path
from config.config import ConfigLoader

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# 初始化GStreamer
Gst.init(None)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RTSPStreamProcessor:
    def __init__(self, config):
        self.config = config
        self.pipeline = None
        self.loop = GLib.MainLoop()
        self.cap = None
        self.running = True
        self.frame_count = 0
        
        # 创建图片保存目录
        Path("images").mkdir(exist_ok=True)
        
        logger.info("RTSPStreamProcessor initialized")

    def bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End of stream")
            self.restart_pipeline()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error received from element {message.src.get_name()}: {err.message}")
            print(f"Debugging information: {debug or 'none'}")
            self.restart_pipeline()
        return True

    def restart_pipeline(self):
        self.stop_pipeline()
        self.start_pipeline()

    def stop_pipeline(self):
        if self.pipeline is not None:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def start_pipeline(self):
        # 创建新的管道
        pipeline_str = f"rtspsrc location={self.config.rtsp_url} ! rtph264depay ! h264parse ! mppvideodec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink sync=false"
        self.pipeline = Gst.parse_launch(pipeline_str)

        # 添加对消息总线的监听
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.bus_call, self.loop)

        # 设置appsink回调函数来获取帧
        appsink = self.pipeline.get_by_name('sink')
        appsink.set_property("emit-signals", True)
        appsink.connect("new-sample", self.on_new_sample)

        # 设置管道状态为播放
        self.pipeline.set_state(Gst.State.PLAYING)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass

        # 清理资源
        self.stop_pipeline()

    def draw_boundary_lines(self, frame):
        """绘制幕布边界区域线"""
        # 定义梯形有效区域的四个顶点（顺时针）
        boundary_points = np.array([
            self.config.top_left_xy,      # 顶部左角
            self.config.top_right_xy,     # 顶部右角
            self.config.bottom_right_xy,  # 底部右角
            self.config.bottom_left_xy    # 底部左角
        ], dtype=np.int32)
        
        # 绘制边界多边形
        cv2.polylines(frame, [boundary_points], True, self.config.line_color, self.config.line_width)
        
        # 绘制中线分割线
        mid_line_points = np.array([
            self.config.mid_left_xy,
            self.config.mid_center_xy,
            self.config.mid_right_xy
        ], dtype=np.int32)
        cv2.polylines(frame, [mid_line_points], False, self.config.line_color, self.config.line_width)
        
        # 填充半透明区域以突出显示有效区域
        overlay = frame.copy()
        cv2.fillPoly(overlay, [boundary_points], (0, 255, 0, 30))  # 绿色半透明
        cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
        
        logger.debug("Boundary lines drawn")

    def draw_coordinate_annotations(self, frame):
        """绘制坐标标注"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (255, 255, 255)  # 白色文字
        thickness = 1
        
        # 标注边界点坐标
        annotations = [
            (self.config.top_left_xy, "TL", self.config.top_left_xy),
            (self.config.top_right_xy, "TR", self.config.top_right_xy),
            (self.config.mid_left_xy, "ML", self.config.mid_left_xy),
            (self.config.mid_center_xy, "MC", self.config.mid_center_xy),
            (self.config.mid_right_xy, "MR", self.config.mid_right_xy),
            (self.config.bottom_left_xy, "BL", self.config.bottom_left_xy),
            (self.config.bottom_center_xy, "BC", self.config.bottom_center_xy),
            (self.config.bottom_right_xy, "BR", self.config.bottom_right_xy),
        ]
        
        for pos, label, coord in annotations:
            # 绘制标签背景
            text = f"{label}:{coord}"
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            
            # 调整文字位置避免超出边界
            text_x = max(5, min(pos[0] - text_size[0]//2, frame.shape[1] - text_size[0] - 5))
            text_y = max(text_size[1] + 5, min(pos[1] - 10, frame.shape[0] - 5))
            
            # 绘制文字背景
            cv2.rectangle(frame, (text_x - 2, text_y - text_size[1] - 2), 
                         (text_x + text_size[0] + 2, text_y + 2), (0, 0, 0), -1)
            
            # 绘制文字
            cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness)
        
        logger.debug("Coordinate annotations drawn")

    def draw_score_regions(self, frame):
        """绘制得分区域和标注"""
        # 绘制所有得分圆圈
        score_circles = [
            (self.config.circle_20_1_xy, self.config.circle_20, "20分(灯1)", (255, 0, 0)),
            (self.config.circle_20_2_xy, self.config.circle_20, "20分(灯2)", (255, 0, 0)),
            (self.config.circle_30_xy, self.config.circle_30, "30分(灯3)", (0, 255, 0)),
            (self.config.circle_50_1_xy, self.config.circle_50, "50分(灯4)", (0, 0, 255)),
            (self.config.circle_50_2_xy, self.config.circle_50, "50分(灯5)", (0, 0, 255)),
        ]
        
        for center, radius, label, color in score_circles:
            # 绘制得分圆圈
            cv2.circle(frame, center, radius, color, 2)
            
            # 绘制十字靶心
            cross_size = 15
            cv2.line(frame, (center[0] - cross_size, center[1]), 
                    (center[0] + cross_size, center[1]), (0, 0, 255), 2)
            cv2.line(frame, (center[0], center[1] - cross_size), 
                    (center[0], center[1] + cross_size), (0, 0, 255), 2)
            
            # 标注得分和坐标信息
            text = f"{label} {center}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            
            # 调整文字位置
            text_x = center[0] - text_size[0]//2
            text_y = center[1] + radius + 20
            
            # 确保文字在画面内
            text_x = max(5, min(text_x, frame.shape[1] - text_size[0] - 5))
            text_y = max(text_size[1] + 5, min(text_y, frame.shape[0] - 5))
            
            # 绘制文字背景
            cv2.rectangle(frame, (text_x - 2, text_y - text_size[1] - 2), 
                         (text_x + text_size[0] + 2, text_y + 2), (0, 0, 0), -1)
            
            # 绘制标注文字
            cv2.putText(frame, text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        logger.debug("Score regions drawn")

    def draw_area_divisions(self, frame):
        """绘制区域划分和得分说明"""
        # 绘制上下区域分割线（加粗显示）
        cv2.line(frame, self.config.mid_left_xy, self.config.mid_right_xy, 
                (255, 255, 0), self.config.line_width + 2)
        
        # 在上半区域标注"5分区域"
        upper_center_x = (self.config.top_left_xy[0] + self.config.top_right_xy[0]) // 2
        upper_center_y = (self.config.top_left_xy[1] + self.config.mid_center_xy[1]) // 2
        
        cv2.putText(frame, "5分区域 (除特殊圆圈)", (upper_center_x - 80, upper_center_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # 在下半区域标注"10分区域"
        lower_center_x = (self.config.bottom_left_xy[0] + self.config.bottom_right_xy[0]) // 2
        lower_center_y = (self.config.mid_center_xy[1] + self.config.bottom_center_xy[1]) // 2
        
        cv2.putText(frame, "10分区域 (除特殊圆圈)", (lower_center_x - 90, lower_center_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        logger.debug("Area divisions drawn")

    def draw_system_info(self, frame):
        """绘制系统信息"""
        # 在左上角显示系统信息
        info_lines = [
            f"球馆: {self.config.court_name}",
            f"球道: {self.config.court_number}",
            f"帧数: {self.frame_count}",
            f"时间: {datetime.now().strftime('%H:%M:%S')}",
            "按 'q' 退出",
        ]
        
        y_offset = 30
        for i, line in enumerate(info_lines):
            y_pos = y_offset + i * 25
            
            # 绘制文字背景
            text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (10, y_pos - text_size[1] - 5), 
                         (10 + text_size[0] + 10, y_pos + 5), (0, 0, 0, 128), -1)
            
            # 绘制文字
            cv2.putText(frame, line, (15, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def on_new_sample(self, sink):
        """处理新的视频帧"""
        try:
            sample = sink.emit("pull-sample")
            if not sample:
                logger.error("No sample received")
                return Gst.FlowReturn.ERROR
                
            buf = sample.get_buffer()
            caps = sample.get_caps()
            
            # 增加帧计数
            self.frame_count += 1

            # 获取图像数据
            arr = np.ndarray(
                shape=(caps.get_structure(0).get_value('height'),
                       caps.get_structure(0).get_value('width'),
                       3),
                dtype=np.uint8,
                buffer=buf.extract_dup(0, buf.get_size()))

            # 确保使用BGR格式（OpenCV默认）
            frame = arr.copy()
            
            # 绘制所有标记点（边界顶点）
            self.draw_boundary_points(frame)
            
            # 绘制边界区域线
            self.draw_boundary_lines(frame)
            
            # 绘制坐标标注
            self.draw_coordinate_annotations(frame)
            
            # 绘制得分区域
            self.draw_score_regions(frame)
            
            # 绘制区域划分
            self.draw_area_divisions(frame)
            
            # 绘制系统信息
            self.draw_system_info(frame)
            
            # 保存配置图片（每30帧保存一次，减少IO）
            if self.frame_count % 30 == 0:
                current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"images/configure_{current_time}_frame{self.frame_count}.jpg"
                cv2.imwrite(filename, frame)
                logger.info(f"Configuration image saved: {filename}")

            # 检查退出条件
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("User requested exit")
                self.running = False
                self.loop.quit()
                
        except Exception as e:
            logger.error(f"Error in on_new_sample: {e}")
            return Gst.FlowReturn.ERROR
            
        return Gst.FlowReturn.OK

    def draw_boundary_points(self, frame):
        """绘制边界标记点"""
        boundary_points = [
            self.config.top_left_xy,
            self.config.top_right_xy,
            self.config.mid_left_xy,
            self.config.mid_center_xy,
            self.config.mid_right_xy,
            self.config.bottom_left_xy,
            self.config.bottom_center_xy,
            self.config.bottom_right_xy,
        ]
        
        for point in boundary_points:
            # 绘制较大的标记点
            cv2.circle(frame, point, self.config.point_size + 2, (255, 255, 255), -1)  # 白色外圈
            cv2.circle(frame, point, self.config.point_size, self.config.point_color, -1)  # 红色内圈

    def run(self):
        self.start_pipeline()

    def cleanup(self):
        self.running = False
        self.loop.quit()
        self.stop_pipeline()
        cv2.destroyAllWindows()

    def print_config(self):
        """打印详细的配置信息"""
        print("\n" + "="*60)
        print(f"           AI Tennis 配置信息")
        print("="*60)
        
        # 基础设置
        print(f"\n【基础设置】")
        print(f"  球馆名称: {self.config.court_name}")
        print(f"  球道编号: {self.config.court_number}")
        print(f"  球场长度: {self.config.court_length}米")
        print(f"  图像保存: {'开启' if self.config.save_image else '关闭'}")
        print(f"  RTSP地址: {self.config.rtsp_url}")
        
        # 识别参数
        print(f"\n【识别参数】")
        print(f"  轮廓周长阈值: {self.config.min_girth}")
        print(f"  圆形度阈值: {self.config.circularity}")
        print(f"  Y坐标补偿: {self.config.y_offset}")
        print(f"  球场长度调整: {self.config.court_length_tuneup}米")
        
        # 时间参数
        print(f"\n【时间参数】")
        print(f"  发球机球速: {self.config.serve_speed}米/秒")
        print(f"  挥拍时延: {self.config.swing_time}毫秒")
        print(f"  寻位时延: {self.config.locating_time}毫秒")
        print(f"  得分倍数: {self.config.multiple}")
        
        # 显示参数
        print(f"\n【显示参数】")
        print(f"  标记点大小: {self.config.point_size}")
        print(f"  标记点颜色: {self.config.point_color} (BGR)")
        print(f"  线条宽度: {self.config.line_width}")
        print(f"  线条颜色: {self.config.line_color} (BGR)")
        
        # 得分区域大小
        print(f"\n【得分区域大小】")
        print(f"  20分圈半径: {self.config.circle_20}")
        print(f"  30分圈半径: {self.config.circle_30}")
        print(f"  50分圈半径: {self.config.circle_50}")
        
        # 得分区域坐标
        print(f"\n【得分区域坐标】")
        print(f"  20分圈1(灯1): {self.config.circle_20_1_xy}")
        print(f"  20分圈2(灯2): {self.config.circle_20_2_xy}")
        print(f"  30分圈(灯3):  {self.config.circle_30_xy}")
        print(f"  50分圈1(灯4): {self.config.circle_50_1_xy}")
        print(f"  50分圈2(灯5): {self.config.circle_50_2_xy}")
        
        # 边界坐标
        print(f"\n【边界坐标】")
        print(f"  顶部左角(TL): {self.config.top_left_xy}")
        print(f"  顶部右角(TR): {self.config.top_right_xy}")
        print(f"  中线左点(ML): {self.config.mid_left_xy}")
        print(f"  中线中心(MC): {self.config.mid_center_xy}")
        print(f"  中线右点(MR): {self.config.mid_right_xy}")
        print(f"  底部左角(BL): {self.config.bottom_left_xy}")
        print(f"  底部中心(BC): {self.config.bottom_center_xy}")
        print(f"  底部右角(BR): {self.config.bottom_right_xy}")
        
        print("="*60)
        print("配置加载完成，开始处理视频流...")
        print("按 'q' 键退出程序")
        print("="*60 + "\n")

    def validate_config(self):
        """验证配置参数的有效性"""
        warnings = []
        errors = []
        
        # 验证基础参数
        if self.config.court_length <= 0:
            errors.append("球场长度必须大于0")
        
        if self.config.serve_speed <= 0:
            errors.append("发球机球速必须大于0")
            
        if not (0.5 <= self.config.circularity <= 1.0):
            errors.append("圆形度阈值必须在0.5-1.0之间")
        
        # 验证坐标是否合理
        coords = [
            ("20分圈1", self.config.circle_20_1_xy),
            ("20分圈2", self.config.circle_20_2_xy),
            ("30分圈", self.config.circle_30_xy),
            ("50分圈1", self.config.circle_50_1_xy),
            ("50分圈2", self.config.circle_50_2_xy),
        ]
        
        for name, coord in coords:
            x, y = coord
            if x < 0 or y < 0 or x > 2000 or y > 1500:
                warnings.append(f"{name}坐标 {coord} 可能超出画面范围")
        
        # 输出验证结果
        if errors:
            logger.error("配置验证发现错误:")
            for error in errors:
                logger.error(f"  - {error}")
        
        if warnings:
            logger.warning("配置验证发现警告:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        if not errors and not warnings:
            logger.info("配置验证通过")
        
        return len(errors) == 0

    def generate_config_summary(self):
        """生成配置摘要信息"""
        summary = {
            "court_info": {
                "name": self.config.court_name,
                "number": self.config.court_number,
                "length": self.config.court_length
            },
            "score_regions": {
                "20_point_1": {"center": self.config.circle_20_1_xy, "radius": self.config.circle_20, "light": 1},
                "20_point_2": {"center": self.config.circle_20_2_xy, "radius": self.config.circle_20, "light": 2},
                "30_point": {"center": self.config.circle_30_xy, "radius": self.config.circle_30, "light": 3},
                "50_point_1": {"center": self.config.circle_50_1_xy, "radius": self.config.circle_50, "light": 4},
                "50_point_2": {"center": self.config.circle_50_2_xy, "radius": self.config.circle_50, "light": 5},
            },
            "boundary_points": {
                "top_left": self.config.top_left_xy,
                "top_right": self.config.top_right_xy,
                "bottom_left": self.config.bottom_left_xy,
                "bottom_right": self.config.bottom_right_xy,
                "mid_left": self.config.mid_left_xy,
                "mid_center": self.config.mid_center_xy,
                "mid_right": self.config.mid_right_xy,
                "bottom_center": self.config.bottom_center_xy,
            }
        }
        return summary


def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info('接收到退出信号 (Ctrl+C)')
    if 'processor' in globals():
        processor.cleanup()
    sys.exit(0)


def main():
    """主函数"""
    try:
        # 显示启动横幅
        print_startup_banner()
        
        # 加载配置
        logger.info("正在加载配置文件...")
        config = ConfigLoader()
        
        # 创建处理器并验证配置
        processor = RTSPStreamProcessor(config)
        
        # 验证配置
        if not processor.validate_config():
            logger.error("配置验证失败，程序退出")
            return 1
        
        # 打印详细配置信息
        processor.print_config()
        
        # 设置信号处理
        signal.signal(signal.SIGINT, signal_handler)
        
        # 运行处理器
        logger.info("开始启动视频流处理...")
        processor.run()
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        return 1
    finally:
        if 'processor' in locals():
            processor.cleanup()
        logger.info("程序已退出")
    
    return 0


def print_startup_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    AI Tennis 配置工具                        ║
    ║                   Configuration Tool                         ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  功能: 实时显示RTSP视频流和识别区域配置                      ║
    ║  版本: v1.0                                                  ║
    ║  开发: MXCHIP                                                ║
    ║  日期: 2025-01-02                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    
    【功能说明】
    ✓ 实时显示RTSP视频流
    ✓ 可视化边界区域和得分圈
    ✓ 坐标标注和区域识别
    ✓ 生成配置校准图片
    ✓ 配置参数验证
    
    【操作说明】
    - 程序将自动连接RTSP视频流
    - 在视频上显示所有识别区域
    - 每30帧自动保存配置图片
    - 按 'q' 键退出程序
    
    """
    print(banner)


if __name__ == '__main__':
    # 设置全局变量供信号处理使用
    processor = None
    
    # 运行主函数
    exit_code = main()
    sys.exit(exit_code)
