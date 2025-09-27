# -*- coding: utf-8 -*-
import time
import math
import threading
import signal
import sys
import zmq
import cv2
import numpy as np
import requests
import logging
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config.config import ConfigLoader
from impact_detector import ImpactDetector
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# 初始化GStreamer
Gst.init(None)


class TennisStreamProcessor:
    game_id = None  # 当前游戏ID
    game_type = None  # 游戏类型
    game_playing = False  # 是否在游戏中
    frame_count = 0  # 当前帧编号
    ball_number = 0  # 当前球的编号
    light = 0
    serve_time = 0
    interval = 0
    recognized = False  # 是否已识别

    frame_queue = []
    # 定义绿色范围
    LOWER_GREEN = np.array([35, 43, 46])
    UPPER_GREEN = np.array([77, 255, 255])

    def __init__(self, configure, logger):
        self.config = configure
        self.logger = logger
        self.zmqcontext = zmq.Context()
        self.zmqclient = None
        self.pipeline = None
        self.loop = GLib.MainLoop()
        self.cap = None
        self.running = True
        
        # 初始化撞击检测器
        self.impact_detector = ImpactDetector(configure)
        
        # 撞击检测相关状态
        self.last_ball_position = None
        self.ball_detected_frames = 0
        self.impact_detection_enabled = True

    # 消息处理线程
    def zmq_message_handler(self):
        while True:
            message = self.zmqclient.recv_string()
            if message.startswith('begin'):
                self.game_id = int(message.split(' ')[1])
                self.game_type = int(message.split(' ')[2])

                self.game_playing = False
                if self.game_type in [1, 2]:
                    self.game_playing = True

                self.logger.info(f"Game begin: {self.game_id} {self.game_type}")

            if message.startswith('end'):
                if self.game_type in [1, 2]:
                    if not self.recognized:
                        self.call_score_api(0, "", False, 0, self.game_type, 0)

                # self.game_id = int(message.split(' ')[1])

                self.game_playing = False
                self.logger.info(f"Game end: {self.game_id}")

            if message.startswith('ball'):
                if self.game_type in [1, 2]:
                    if not self.recognized:
                        self.call_score_api(0, "", False, 0, self.game_type, 0)

                self.game_id = int(message.split(' ')[1])
                self.ball_number = int(message.split(' ')[2])
                self.light = int(message.split(' ')[3])
                self.serve_time = message.split(' ')[4]
                self.interval = int(message.split(' ')[5])

                self.recognized = False
                # 重置撞击检测器状态，准备检测新球
                self.impact_detector.reset()
                self.last_ball_position = None
                self.ball_detected_frames = 0
                
                self.logger.info(f"Received ball: {self.game_id} {self.ball_number} {self.light} {self.serve_time} {self.interval}")

    def bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.logger.info("End of stream")
            self.restart_pipeline()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.logger.error(f"Error received from element {message.src.get_name()}: {err.message}")
            self.logger.error(f"Debugging information: {debug or 'none'}")
            self.restart_pipeline()
        return True

    def restart_pipeline(self):
        self.stop_pipeline()
        self.start_pipeline()

    def stop_pipeline(self):
        if self.pipeline is not None:
            # self.pipeline.send_event(Gst.Event.new_eos)
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.running = False

    def start_pipeline(self):
        # 初始化ZeroMQ
        self.zmqclient = self.zmqcontext.socket(zmq.SUB)
        self.zmqclient.connect("tcp://localhost:5678")
        self.zmqclient.setsockopt_string(zmq.SUBSCRIBE, 'ball')
        self.zmqclient.setsockopt_string(zmq.SUBSCRIBE, 'begin')
        self.zmqclient.setsockopt_string(zmq.SUBSCRIBE, 'end')

        # 启动消息处理线程
        zmq_thread = threading.Thread(target=self.zmq_message_handler)
        zmq_thread.daemon = True
        zmq_thread.start()

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

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if not sample:
            self.logger.error("No sample received")
            return Gst.FlowReturn.ERROR

        buf = sample.get_buffer()
        caps = sample.get_caps()
        # self.logger.debug(f"Received sample with caps: {caps.to_string()}")

        # 获取图像数据
        try:
            _, map_info = buf.map(Gst.MapFlags.READ)
            img_array = np.ndarray(
                shape=(caps.get_structure(0).get_value('height'),
                       caps.get_structure(0).get_value('width'),
                       3),
                buffer=map_info.data,
                dtype=np.uint8
            )
            buf.unmap(map_info)
        except Exception as e:
            self.logger.error(f"Error mapping buffer: {e}")
            return Gst.FlowReturn.ERROR

        # 图像数据放入队列
        self.frame_queue.append(img_array)

        # 将图像处理任务调度到主线程
        GLib.idle_add(self.display_frame)

        return Gst.FlowReturn.OK

    def run(self):
        self.start_pipeline()

    def cleanup(self):
        self.running = False
        self.loop.quit()
        self.stop_pipeline()
        cv2.destroyAllWindows()
    
    def get_impact_detection_stats(self):
        """获取撞击检测统计信息"""
        return self.impact_detector.get_detection_stats()
    
    def set_impact_detection_enabled(self, enabled: bool):
        """启用或禁用撞击检测"""
        self.impact_detection_enabled = enabled
        self.logger.info(f"Impact detection {'enabled' if enabled else 'disabled'}")
    
    def update_impact_detection_params(self, params: dict):
        """更新撞击检测参数"""
        self.impact_detector.params.update(params)
        self.logger.info(f"Impact detection parameters updated: {params}")

    # 返回计分程序采集数据
    def call_score_api(self, score, coord, x3, ball_speed, game_type, light):
        url = f"http://localhost:8000/game_serve/update_score/{self.game_id}/{self.ball_number}"
        data = {
            "ball_number": self.ball_number,
            "score": score,
            "coord": coord,
            "x3": x3,
            "ball_speed": ball_speed,
            "game_type": game_type,
            "light": light
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.put(url, json=data, headers=headers)
        # self.logger.debug("update_score request:", data.json())
        # self.logger.debug("update_score response:", response.json())

    # 定义处理视频帧的函数
    def process_frame(self, frame):
        self.frame_count += 1

        trapezoid = [self.config.top_left_xy, self.config.top_right_xy, self.config.bottom_right_xy, self.config.bottom_left_xy]

        # 复制图像数据，使其可写
        frame = frame.copy()

        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 创建掩膜（mask），只保留绿色部分
        mask = cv2.inRange(hsv, self.LOWER_GREEN, self.UPPER_GREEN)

        # 使用高斯模糊减少噪声
        blurred = cv2.GaussianBlur(mask, (11, 11), 0)

        # 寻找轮廓
        contours, _ = cv2.findContours(blurred.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        ball_detected = False
        current_ball_position = None

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > self.config.min_girth:  # 轮廓周长，排除小的干扰
                # 计算圆形度
                perimeter = cv2.arcLength(cnt, True)
                circularity = 4 * np.pi * (area / (perimeter * perimeter))

                (x, y), radius = cv2.minEnclosingCircle(cnt)
                center = (int(x), int(y + self.config.y_offset))

                if circularity > self.config.circularity and is_point_in_polygon(center, trapezoid):
                    ball_detected = True
                    current_ball_position = (x, y)
                    self.ball_detected_frames += 1
                    
                    # 使用优化的撞击检测
                    impact_result = None
                    if self.impact_detection_enabled:
                        curtain_region = np.array([[self.config.top_left_xy, self.config.top_right_xy, 
                                                  self.config.bottom_right_xy, self.config.bottom_left_xy]], 
                                                dtype=np.int32)
                        impact_result = self.impact_detector.detect_impact(frame, current_ball_position, curtain_region)
                    
                    # 判断是否应该处理这次检测
                    should_process = True
                    if self.impact_detection_enabled and impact_result:
                        # 只有在检测到撞击时才处理
                        should_process = impact_result['detected']
                        if impact_result['detected']:
                            self.logger.info(f"撞击检测: {impact_result['reason']} 置信度: {impact_result['confidence']:.2f}")
                    
                    if should_process:
                        score, score_light = self.get_score(x, y)
                        self.logger.info(f"light{self.light},score{score}, score_light{score_light}")
                        x3 = False
                        if int(self.light) == score_light:
                            score = score * self.config.multiple
                            x3 = True

                        # 球速计算km/h： 3.6 * 球场长度/(当前时间s-发球指令时间s-发球机寻位时间s-球飞行时间s)
                        flight_time = self.config.court_length / (self.config.serve_speed * 1000 / 3600)
                        time1 = time.time()

                        ball_speed = 3.6 * (self.config.court_length + self.config.court_length_tuneup) / (
                                time1 - float(self.serve_time) - self.config.locating_time / 1000 - flight_time - self.config.swing_time / 1000)
                        if ball_speed < 0:
                            ball_speed = 25

                        self.logger.info(f"计算球速: {ball_speed} 发球时间: {self.serve_time} 总时长: {time1 - float(self.serve_time)} 发球机寻位时间: {self.config.locating_time} 球飞行时间: {flight_time}")

                        self.call_score_api(score, str(center), x3, math.ceil(ball_speed), self.game_type, score_light)
                        
                        impact_info = ""
                        if impact_result and impact_result['detected']:
                            impact_info = f" [撞击检测: {impact_result['method']}]"
                        
                        self.logger.info(f"帧: {self.frame_count} 坐标: {center} 半径: {radius} 得分: {score} 游戏类型: {self.game_type} 打中灯号: {score_light}{impact_info}")

                        if self.config.save_image:
                            # 绘制撞击检测信息
                            if impact_result and impact_result['detected']:
                                cv2.putText(frame, f"IMPACT: {impact_result['confidence']:.2f}", 
                                          (int(x) - 100, int(y) - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                            
                            cv2.putText(frame, str(center) + str(score), (int(x) - 100, int(y) - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv2.circle(frame, center, int(radius), (0, 0, 255), 2)

                            save_image(frame, f"images/{self.game_id}/ok_{self.ball_number}.jpg")

                        # 识别到球
                        self.recognized = True
                        break  # 只处理第一个检测到的球

        # 更新球的位置信息
        if ball_detected:
            self.last_ball_position = current_ball_position
        else:
            # 如果连续多帧没有检测到球，重置撞击检测器
            if self.ball_detected_frames > 0:
                self.ball_detected_frames = max(0, self.ball_detected_frames - 1)
                if self.ball_detected_frames == 0:
                    self.impact_detector.reset()
                    self.last_ball_position = None

        return frame

    # 定义图像显示函数
    def display_frame(self):
        if self.frame_queue:
            img_array = self.frame_queue.pop(0)

            if self.game_playing:
                if not self.recognized:
                    _ = self.process_frame(img_array)

            # 检查是否按下了ESC键
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC键
                self.logger.info("Exiting...")
                self.pipeline.send_event(Gst.Event.new_eos())
                self.running = False
                self.loop.quit()
        return True

    def get_score(self, x, y):
        # 有效区域梯形的四个顺时针顶点
        trapezoid = [self.config.top_left_xy, self.config.top_right_xy, self.config.bottom_right_xy, self.config.bottom_left_xy]

        # 判断是否在多边形区域内
        if is_point_in_polygon((x, y), trapezoid):
            # 判断是否在矩形区域内
            is_down_area = is_point_in_rectangle(x, y, self.config.mid_left_xy[0], self.config.mid_left_xy[1],
                                                 self.config.bottom_right_xy[0], self.config.bottom_right_xy[1])

            if is_down_area:
                if is_point_in_circle(x, y, self.config.circle_30_xy[0], self.config.circle_30_xy[1], self.config.circle_30):
                    return 30, 3

                if is_point_in_circle(x, y, self.config.circle_50_1_xy[0], self.config.circle_50_1_xy[1], self.config.circle_50):
                    return 50, 4

                if is_point_in_circle(x, y, self.config.circle_50_2_xy[0], self.config.circle_50_2_xy[1], self.config.circle_50):
                    return 50, 5

                return 10, -1
            else:
                if is_point_in_circle(x, y, self.config.circle_20_1_xy[0], self.config.circle_20_1_xy[1], self.config.circle_20):
                    return 20, 1
                if is_point_in_circle(x, y, self.config.circle_20_2_xy[0], self.config.circle_20_2_xy[1], self.config.circle_20):
                    return 20, 2

                return 5, -1
        else:
            return 0, -1


# 判断给定点是否位于指定矩形内
def is_point_in_rectangle(x, y, left_top_x, left_top_y, right_bottom_x, right_bottom_y):
    return left_top_x <= x <= right_bottom_x and left_top_y <= y <= right_bottom_y


# 判断给定点是否位于指定圆内
def is_point_in_circle(point_x, point_y, circle_center_x, circle_center_y, radius):
    return ((point_x - circle_center_x) ** 2 + (point_y - circle_center_y) ** 2) <= radius ** 2


# 判断点是否在多边形内
def is_point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


# 存放计分图片到指定目录
def save_image(image, filepath):
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


# 设置日志文件及控制台输出
def setup_logger():
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'tennis_score_{current_time}.log'

    _logger = logging.getLogger('score')
    _logger.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(log_filename, maxBytes=1024 * 1024, backupCount=16)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)

    return _logger


def signal_handler(sig, frame):
    logger.info('You pressed Ctrl+C!')
    tennis_score.cleanup()
    sys.exit(0)

def print_startup_info():
    project_name = "AI Tennis Score"
    developer = "MXCHIP"
    version = "v1.0"
    date = "2025-01-02"

    banner = f"""
    ======================================
    Project: {project_name}
    Developer: {developer}
    Version: {version}
    Date: {date}
    ======================================
    """
    logger.info(banner)
    logger.info("Startup successful!")


if __name__ == '__main__':
    config = ConfigLoader()

    logger = setup_logger()
    print_startup_info()

    signal.signal(signal.SIGINT, signal_handler)

    tennis_score = TennisStreamProcessor(config, logger)
    tennis_score.run()
