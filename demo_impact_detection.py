# -*- coding: utf-8 -*-
"""
撞击检测演示脚本
展示优化后的撞击检测功能
"""
import cv2
import numpy as np
import time
import logging
from pathlib import Path
from impact_detector import ImpactDetector
from impact_config import ImpactDetectionConfig

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImpactDetectionDemo:
    """撞击检测演示类"""
    
    def __init__(self):
        # 创建模拟配置对象
        class MockConfig:
            def __init__(self):
                self.top_left_xy = (100, 100)
                self.top_right_xy = (540, 100)
                self.bottom_left_xy = (100, 380)
                self.bottom_right_xy = (540, 380)
                self.circle_20_1_xy = (200, 150)
                self.circle_20_2_xy = (440, 150)
                self.circle_30_xy = (320, 240)
                self.circle_50_1_xy = (220, 330)
                self.circle_50_2_xy = (420, 330)
                self.circle_20 = 60
                self.circle_30 = 65
                self.circle_50 = 55
        
        self.config = MockConfig()
        self.impact_detector = ImpactDetector(self.config)
        
        # 演示参数
        self.demo_frames = []
        self.current_frame = 0
        self.demo_running = False
        
    def create_demo_scene(self):
        """创建演示场景"""
        # 创建幕布区域
        curtain_region = np.array([
            [self.config.top_left_xy, self.config.top_right_xy,
             self.config.bottom_right_xy, self.config.bottom_left_xy]
        ], dtype=np.int32)
        
        # 创建背景
        background = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 绘制幕布
        cv2.fillPoly(background, curtain_region, (100, 150, 200))  # 蓝色幕布
        
        # 绘制得分圆圈
        cv2.circle(background, self.config.circle_20_1_xy, self.config.circle_20, (0, 255, 255), 2)
        cv2.circle(background, self.config.circle_20_2_xy, self.config.circle_20, (0, 255, 255), 2)
        cv2.circle(background, self.config.circle_30_xy, self.config.circle_30, (0, 255, 0), 2)
        cv2.circle(background, self.config.circle_50_1_xy, self.config.circle_50, (0, 0, 255), 2)
        cv2.circle(background, self.config.circle_50_2_xy, self.config.circle_50, (0, 0, 255), 2)
        
        # 添加标签
        cv2.putText(background, "20", (self.config.circle_20_1_xy[0]-10, self.config.circle_20_1_xy[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(background, "20", (self.config.circle_20_2_xy[0]-10, self.config.circle_20_2_xy[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(background, "30", (self.config.circle_30_xy[0]-10, self.config.circle_30_xy[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(background, "50", (self.config.circle_50_1_xy[0]-10, self.config.circle_50_1_xy[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(background, "50", (self.config.circle_50_2_xy[0]-10, self.config.circle_50_2_xy[1]+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        return background, curtain_region
    
    def simulate_ball_movement(self, start_pos, end_pos, num_frames=60):
        """模拟球的运动"""
        frames = []
        background, curtain_region = self.create_demo_scene()
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        for i in range(num_frames):
            frame = background.copy()
            
            # 计算球的当前位置
            t = i / (num_frames - 1)
            # 使用二次函数模拟球的抛物线运动
            t_smooth = t * t * (3 - 2 * t)  # smoothstep函数
            x = int(x1 + (x2 - x1) * t_smooth)
            y = int(y1 + (y2 - y1) * t_smooth)
            
            # 添加抛物线效果
            if i > num_frames // 2:
                # 后半段添加重力效果
                gravity_offset = (i - num_frames // 2) * 2
                y += gravity_offset
            
            ball_pos = (x, y)
            
            # 绘制球
            cv2.circle(frame, ball_pos, 15, (0, 255, 0), -1)  # 绿色球
            cv2.circle(frame, ball_pos, 20, (255, 255, 255), 2)  # 白色边框
            
            # 执行撞击检测
            impact_result = self.impact_detector.detect_impact(frame, ball_pos, curtain_region)
            
            # 绘制检测信息
            if impact_result['detected']:
                # 撞击时绘制特殊效果
                cv2.circle(frame, ball_pos, 40, (0, 255, 255), 3)  # 黄色撞击圈
                cv2.putText(frame, f"IMPACT! {impact_result['confidence']:.2f}", 
                           (ball_pos[0]-80, ball_pos[1]-50), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 255), 2)
                cv2.putText(frame, f"Method: {impact_result['method']}", 
                           (ball_pos[0]-60, ball_pos[1]-30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (0, 255, 255), 1)
            
            # 绘制速度信息
            velocity = self.impact_detector.ball_tracker.get_current_velocity()
            if velocity > 0:
                cv2.putText(frame, f"Speed: {velocity:.1f} px/s", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 绘制帧信息
            cv2.putText(frame, f"Frame: {i+1}/{num_frames}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            frames.append(frame)
        
        return frames
    
    def create_multiple_scenarios(self):
        """创建多个演示场景"""
        scenarios = []
        
        # 场景1: 球撞击30分圈
        scenario1 = self.simulate_ball_movement((50, 50), (320, 240), 40)
        scenarios.append(("撞击30分圈", scenario1))
        
        # 场景2: 球撞击50分圈
        scenario2 = self.simulate_ball_movement((100, 80), (220, 330), 45)
        scenarios.append(("撞击50分圈", scenario2))
        
        # 场景3: 球撞击20分圈
        scenario3 = self.simulate_ball_movement((200, 50), (200, 150), 35)
        scenarios.append(("撞击20分圈", scenario3))
        
        # 场景4: 球快速飞过（无撞击）
        scenario4 = self.simulate_ball_movement((50, 200), (590, 200), 30)
        scenarios.append(("快速飞过", scenario4))
        
        return scenarios
    
    def run_demo(self):
        """运行演示"""
        print("🎯 撞击检测演示")
        print("="*50)
        print("演示场景:")
        print("1. 球撞击30分圈")
        print("2. 球撞击50分圈") 
        print("3. 球撞击20分圈")
        print("4. 球快速飞过（无撞击）")
        print("\n按任意键开始演示，按ESC退出...")
        
        scenarios = self.create_multiple_scenarios()
        
        for scenario_name, frames in scenarios:
            print(f"\n🎬 演示场景: {scenario_name}")
            print("按任意键继续，按ESC跳过...")
            
            # 等待用户输入
            key = cv2.waitKey(0) & 0xFF
            if key == 27:  # ESC键
                print("跳过当前场景")
                continue
            
            # 播放场景
            for i, frame in enumerate(frames):
                cv2.imshow('撞击检测演示', frame)
                
                key = cv2.waitKey(100) & 0xFF  # 100ms延迟
                if key == 27:  # ESC键退出
                    print("演示被用户中断")
                    cv2.destroyAllWindows()
                    return
                
                # 检查是否有撞击
                if i < len(frames) - 1:  # 不是最后一帧
                    # 这里可以添加撞击检测的逻辑
                    pass
            
            print(f"场景 '{scenario_name}' 播放完成")
        
        print("\n✅ 演示完成！")
        cv2.destroyAllWindows()
    
    def run_interactive_demo(self):
        """运行交互式演示"""
        print("🎮 交互式撞击检测演示")
        print("="*50)
        print("用鼠标点击屏幕上的任意位置，模拟球撞击该点")
        print("按ESC退出")
        
        background, curtain_region = self.create_demo_scene()
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # 模拟球撞击点击位置
                frame = background.copy()
                
                # 绘制球
                cv2.circle(frame, (x, y), 15, (0, 255, 0), -1)
                cv2.circle(frame, (x, y), 20, (255, 255, 255), 2)
                
                # 执行撞击检测
                impact_result = self.impact_detector.detect_impact(frame, (x, y), curtain_region)
                
                # 显示检测结果
                if impact_result['detected']:
                    cv2.circle(frame, (x, y), 40, (0, 255, 255), 3)
                    cv2.putText(frame, f"IMPACT! {impact_result['confidence']:.2f}", 
                               (x-80, y-50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    cv2.putText(frame, f"Method: {impact_result['method']}", 
                               (x-60, y-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    print(f"检测到撞击！位置: ({x}, {y}), 方法: {impact_result['method']}, 置信度: {impact_result['confidence']:.2f}")
                else:
                    print(f"未检测到撞击。位置: ({x}, {y})")
                
                cv2.imshow('交互式撞击检测', frame)
        
        cv2.namedWindow('交互式撞击检测')
        cv2.setMouseCallback('交互式撞击检测', mouse_callback)
        cv2.imshow('交互式撞击检测', background)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC键退出
                break
        
        cv2.destroyAllWindows()


def main():
    """主函数"""
    demo = ImpactDetectionDemo()
    
    print("选择演示模式:")
    print("1. 自动演示")
    print("2. 交互式演示")
    print("3. 退出")
    
    choice = input("请选择 (1-3): ").strip()
    
    if choice == '1':
        demo.run_demo()
    elif choice == '2':
        demo.run_interactive_demo()
    elif choice == '3':
        print("退出演示")
    else:
        print("无效选择")


if __name__ == '__main__':
    main()