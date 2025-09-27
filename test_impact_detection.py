# -*- coding: utf-8 -*-
"""
撞击检测测试脚本
用于测试和验证撞击检测功能
"""
import cv2
import numpy as np
import time
import logging
from pathlib import Path
from impact_detector import ImpactDetector
from impact_config import ImpactDetectionConfig
from config.config import ConfigLoader

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImpactDetectionTester:
    """撞击检测测试器"""
    
    def __init__(self):
        # 加载配置
        try:
            self.config = ConfigLoader()
            logger.info("主配置文件加载成功")
        except Exception as e:
            logger.error(f"主配置文件加载失败: {e}")
            self.config = None
        
        # 初始化撞击检测器
        self.impact_detector = ImpactDetector(self.config)
        
        # 测试参数
        self.test_frames = []
        self.test_results = []
        
    def load_test_video(self, video_path: str):
        """加载测试视频"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return False
        
        self.test_frames = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 每5帧取一帧，减少数据量
            if frame_count % 5 == 0:
                self.test_frames.append(frame.copy())
            
            frame_count += 1
            
            # 限制测试帧数
            if len(self.test_frames) >= 100:
                break
        
        cap.release()
        logger.info(f"加载了 {len(self.test_frames)} 帧测试数据")
        return True
    
    def simulate_ball_trajectory(self, start_pos: tuple, end_pos: tuple, num_frames: int = 30):
        """模拟球轨迹"""
        frames = []
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        for i in range(num_frames):
            # 创建黑色背景
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # 计算当前球的位置（线性插值）
            t = i / (num_frames - 1)
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            
            # 绘制球（绿色圆圈）
            cv2.circle(frame, (x, y), 15, (0, 255, 0), -1)
            
            frames.append(frame)
        
        return frames
    
    def test_velocity_detection(self):
        """测试速度检测"""
        logger.info("开始测试速度检测...")
        
        # 创建模拟球轨迹：从左上角到右下角，模拟撞击幕布
        start_pos = (100, 100)
        end_pos = (500, 400)
        frames = self.simulate_ball_trajectory(start_pos, end_pos, 50)
        
        results = []
        curtain_region = np.array([[(50, 50), (590, 50), (590, 430), (50, 430)]], dtype=np.int32)
        
        for i, frame in enumerate(frames):
            # 计算球的位置
            t = i / (len(frames) - 1)
            x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * t)
            y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * t)
            ball_center = (x, y)
            
            # 执行撞击检测
            result = self.impact_detector.detect_impact(frame, ball_center, curtain_region)
            
            if result['detected']:
                logger.info(f"帧 {i}: 检测到撞击 - {result['reason']} (置信度: {result['confidence']:.2f})")
                results.append({
                    'frame': i,
                    'position': ball_center,
                    'result': result
                })
        
        logger.info(f"速度检测测试完成，检测到 {len(results)} 次撞击")
        return results
    
    def test_region_detection(self):
        """测试区域变化检测"""
        logger.info("开始测试区域变化检测...")
        
        # 创建静态背景
        background = np.zeros((480, 640, 3), dtype=np.uint8)
        curtain_region = np.array([[(50, 50), (590, 50), (590, 430), (50, 430)]], dtype=np.int32)
        cv2.fillPoly(background, curtain_region, (100, 150, 200))  # 蓝色幕布
        
        # 模拟撞击：在幕布上添加扰动
        frames = [background.copy()]
        
        # 添加撞击效果
        impact_frame = background.copy()
        cv2.circle(impact_frame, (320, 240), 50, (255, 255, 255), -1)  # 白色撞击区域
        frames.append(impact_frame)
        
        # 恢复背景
        frames.append(background.copy())
        
        results = []
        ball_center = (320, 240)  # 撞击点
        
        for i, frame in enumerate(frames):
            result = self.impact_detector.detect_impact(frame, ball_center, curtain_region)
            
            if result['detected']:
                logger.info(f"帧 {i}: 区域变化检测 - {result['reason']} (置信度: {result['confidence']:.2f})")
                results.append({
                    'frame': i,
                    'result': result
                })
        
        logger.info(f"区域变化检测测试完成，检测到 {len(results)} 次撞击")
        return results
    
    def test_threshold_detection(self):
        """测试阈值检测"""
        logger.info("开始测试阈值检测...")
        
        # 创建测试帧
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        curtain_region = np.array([[(50, 50), (590, 50), (590, 430), (50, 430)]], dtype=np.int32)
        cv2.fillPoly(frame, curtain_region, (100, 150, 200))  # 蓝色幕布
        
        # 测试不同位置的球
        test_positions = [
            (320, 240),  # 幕布中心
            (100, 100),  # 幕布边缘
            (50, 50),    # 幕布角点
            (600, 400),  # 幕布内
            (30, 30),    # 幕布外
        ]
        
        results = []
        for i, pos in enumerate(test_positions):
            # 在帧上绘制球
            test_frame = frame.copy()
            cv2.circle(test_frame, pos, 15, (0, 255, 0), -1)
            
            result = self.impact_detector.detect_impact(test_frame, pos, curtain_region)
            
            logger.info(f"位置 {pos}: 阈值检测 - 检测到: {result['detected']}, 置信度: {result['confidence']:.2f}")
            results.append({
                'position': pos,
                'result': result
            })
        
        logger.info(f"阈值检测测试完成")
        return results
    
    def test_integrated_detection(self):
        """测试综合检测"""
        logger.info("开始测试综合检测...")
        
        # 创建复杂的测试场景
        frames = []
        curtain_region = np.array([[(50, 50), (590, 50), (590, 430), (50, 430)]], dtype=np.int32)
        
        # 创建背景
        background = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.fillPoly(background, curtain_region, (100, 150, 200))  # 蓝色幕布
        
        # 模拟球从远处飞来撞击幕布
        ball_positions = []
        for i in range(30):
            # 球从左上角飞向幕布中心
            x = 50 + i * 15
            y = 50 + i * 10
            if x > 590:
                x = 590
            if y > 240:
                y = 240
            
            ball_positions.append((x, y))
        
        # 生成帧序列
        for i, pos in enumerate(ball_positions):
            frame = background.copy()
            cv2.circle(frame, pos, 15, (0, 255, 0), -1)  # 绿色球
            
            # 在撞击点添加效果
            if i >= 25:  # 接近撞击时
                cv2.circle(frame, pos, 30, (255, 255, 255), 2)  # 撞击效果
            
            frames.append(frame)
        
        results = []
        for i, (frame, pos) in enumerate(zip(frames, ball_positions)):
            result = self.impact_detector.detect_impact(frame, pos, curtain_region)
            
            if result['detected']:
                logger.info(f"帧 {i}: 综合检测 - 方法: {result['method']}, 置信度: {result['confidence']:.2f}")
                logger.info(f"  原因: {result['reason']}")
                results.append({
                    'frame': i,
                    'position': pos,
                    'result': result
                })
        
        logger.info(f"综合检测测试完成，检测到 {len(results)} 次撞击")
        return results
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行撞击检测测试...")
        
        test_results = {
            'velocity': self.test_velocity_detection(),
            'region': self.test_region_detection(),
            'threshold': self.test_threshold_detection(),
            'integrated': self.test_integrated_detection()
        }
        
        # 统计结果
        total_detections = sum(len(results) for results in test_results.values())
        logger.info(f"\n测试完成！总共检测到 {total_detections} 次撞击")
        
        for test_name, results in test_results.items():
            logger.info(f"{test_name} 测试: {len(results)} 次检测")
        
        # 获取检测统计信息
        stats = self.impact_detector.get_detection_stats()
        logger.info(f"检测统计: {stats}")
        
        return test_results
    
    def save_test_results(self, results, filename='impact_test_results.txt'):
        """保存测试结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("撞击检测测试结果\n")
            f.write("="*50 + "\n\n")
            
            for test_name, test_results in results.items():
                f.write(f"{test_name.upper()} 测试结果:\n")
                f.write("-" * 30 + "\n")
                
                for result in test_results:
                    f.write(f"检测结果: {result}\n")
                
                f.write(f"\n检测次数: {len(test_results)}\n\n")
        
        logger.info(f"测试结果已保存到: {filename}")


def main():
    """主函数"""
    print("🎯 撞击检测测试工具")
    print("="*50)
    
    # 创建测试器
    tester = ImpactDetectionTester()
    
    # 创建撞击检测配置文件
    try:
        impact_config = ImpactDetectionConfig()
        print("✅ 撞击检测配置文件已加载")
        impact_config.print_config()
    except Exception as e:
        print(f"❌ 撞击检测配置文件加载失败: {e}")
    
    print("\n开始测试...")
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 保存结果
    tester.save_test_results(results)
    
    print("\n✅ 所有测试完成！")


if __name__ == '__main__':
    main()