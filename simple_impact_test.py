# -*- coding: utf-8 -*-
"""
简化的撞击检测测试脚本（不依赖OpenCV）
用于验证撞击检测的核心逻辑
"""
import time
import logging
from collections import deque
from impact_config import ImpactDetectionConfig

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleBallTracker:
    """简化的球跟踪器"""
    
    def __init__(self, max_track_length=30):
        self.positions = deque(maxlen=max_track_length)
        self.timestamps = deque(maxlen=max_track_length)
        self.velocities = deque(maxlen=max_track_length)
        self.max_track_length = max_track_length
        
    def add_position(self, x: int, y: int):
        """添加球的位置"""
        current_time = time.time()
        
        if len(self.positions) > 0:
            # 计算速度
            prev_x, prev_y = self.positions[-1]
            prev_time = self.timestamps[-1]
            
            dt = current_time - prev_time
            if dt > 0:
                vx = (x - prev_x) / dt
                vy = (y - prev_y) / dt
                velocity = (vx**2 + vy**2)**0.5
                self.velocities.append(velocity)
            else:
                self.velocities.append(0)
        else:
            self.velocities.append(0)
            
        self.positions.append((x, y))
        self.timestamps.append(current_time)
    
    def get_current_velocity(self) -> float:
        """获取当前速度"""
        return self.velocities[-1] if len(self.velocities) > 0 else 0
    
    def get_velocity_change_rate(self, window_size: int = 5) -> float:
        """获取速度变化率"""
        if len(self.velocities) < window_size:
            return 0
        
        recent_velocities = list(self.velocities)[-window_size:]
        if len(recent_velocities) < 2:
            return 0
            
        # 计算速度变化率
        velocity_changes = []
        for i in range(1, len(recent_velocities)):
            change = abs(recent_velocities[i] - recent_velocities[i-1])
            velocity_changes.append(change)
        
        return sum(velocity_changes) / len(velocity_changes) if velocity_changes else 0
    
    def is_speed_decreasing(self, threshold: float = 0.8) -> bool:
        """判断速度是否在下降"""
        if len(self.velocities) < 3:
            return False
        
        recent_velocities = list(self.velocities)[-3:]
        # 检查最近3帧的速度是否持续下降
        for i in range(1, len(recent_velocities)):
            if recent_velocities[i] >= recent_velocities[i-1] * threshold:
                return False
        return True
    
    def clear(self):
        """清空轨迹数据"""
        self.positions.clear()
        self.timestamps.clear()
        self.velocities.clear()


class SimpleImpactDetector:
    """简化的撞击检测器"""
    
    def __init__(self):
        self.ball_tracker = SimpleBallTracker()
        
        # 加载配置
        self.impact_config = ImpactDetectionConfig()
        self.params = self._load_params()
        
        # 状态变量
        self.last_impact_time = 0
        self.min_impact_interval = self.params.get('min_impact_interval', 0.5)
        
        logger.info("SimpleImpactDetector initialized")
    
    def _load_params(self):
        """加载参数"""
        all_config = self.impact_config.get_all_params()
        
        params = {}
        
        # 速度检测参数
        velocity_params = all_config.get('velocity', {})
        params.update({
            'velocity_change_threshold': velocity_params.get('velocity_change_threshold', 50.0),
            'position_change_threshold': velocity_params.get('position_change_threshold', 20.0),
            'speed_decrease_threshold': velocity_params.get('speed_decrease_threshold', 0.7),
        })
        
        # 阈值检测参数
        threshold_params = all_config.get('threshold', {})
        params.update({
            'impact_zone_margin': threshold_params.get('impact_zone_margin', 30),
            'confidence_threshold': threshold_params.get('confidence_threshold', 0.6),
            'min_impact_interval': threshold_params.get('min_impact_interval', 0.5)
        })
        
        # 融合检测参数
        fusion_params = all_config.get('fusion', {})
        params['method_weights'] = {
            'velocity': fusion_params.get('velocity_weight', 0.4),
            'region': fusion_params.get('region_weight', 0.3),
            'threshold': fusion_params.get('threshold_weight', 0.3)
        }
        
        return params
    
    def detect_velocity_impact(self, ball_center):
        """检测基于速度的撞击"""
        x, y = ball_center
        self.ball_tracker.add_position(x, y)
        
        result = {
            'detected': False,
            'confidence': 0.0,
            'reason': '',
            'velocity': self.ball_tracker.get_current_velocity(),
            'velocity_change_rate': self.ball_tracker.get_velocity_change_rate(),
            'speed_decreasing': self.ball_tracker.is_speed_decreasing()
        }
        
        # 检查速度变化率
        velocity_change = result['velocity_change_rate']
        if velocity_change > self.params['velocity_change_threshold']:
            result['confidence'] += 0.4
            result['reason'] += 'High velocity change; '
        
        # 检查速度下降
        if result['speed_decreasing']:
            result['confidence'] += 0.3
            result['reason'] += 'Speed decreasing; '
        
        # 判断是否检测到撞击
        if result['confidence'] > 0.5:
            result['detected'] = True
            
        return result
    
    def detect_threshold_impact(self, ball_center, curtain_region):
        """检测基于阈值的撞击"""
        x, y = ball_center
        
        result = {
            'detected': False,
            'confidence': 0.0,
            'reason': '',
            'in_impact_zone': False,
        }
        
        # 简化的区域检测：检查是否在幕布区域内
        if self._point_in_curtain_region((x, y), curtain_region):
            result['confidence'] = 0.8
            result['reason'] = 'Ball in curtain region; '
            result['detected'] = True
            result['in_impact_zone'] = True
        
        return result
    
    def _point_in_curtain_region(self, point, curtain_region):
        """简化的点在区域内检测"""
        x, y = point
        # 假设curtain_region是一个矩形区域
        if len(curtain_region) >= 4:
            x1, y1 = curtain_region[0]
            x2, y2 = curtain_region[2]  # 对角点
            return x1 <= x <= x2 and y1 <= y <= y2
        return False
    
    def detect_impact(self, ball_center, curtain_region):
        """综合撞击检测"""
        current_time = time.time()
        
        # 检查撞击间隔
        if current_time - self.last_impact_time < self.min_impact_interval:
            return {
                'detected': False,
                'confidence': 0.0,
                'reason': 'Too frequent impact detection',
                'method': 'interval_check'
            }
        
        # 执行检测方法
        velocity_result = self.detect_velocity_impact(ball_center)
        threshold_result = self.detect_threshold_impact(ball_center, curtain_region)
        
        # 融合结果
        weights = self.params['method_weights']
        total_confidence = (
            velocity_result['confidence'] * weights['velocity'] +
            threshold_result['confidence'] * weights['threshold']
        )
        
        # 确定检测方法
        method = 'unknown'
        if velocity_result['detected']:
            method = 'velocity'
        elif threshold_result['detected']:
            method = 'threshold'
        
        # 综合判断
        detected = (
            total_confidence > self.params['confidence_threshold'] or
            (velocity_result['detected'] and threshold_result['detected'])
        )
        
        # 构建原因字符串
        reasons = []
        if velocity_result['detected']:
            reasons.append(f"Velocity: {velocity_result['reason']}")
        if threshold_result['detected']:
            reasons.append(f"Threshold: {threshold_result['reason']}")
        
        result = {
            'detected': detected,
            'confidence': total_confidence,
            'reason': '; '.join(reasons),
            'method': method,
            'velocity_result': velocity_result,
            'threshold_result': threshold_result
        }
        
        # 如果检测到撞击，更新状态
        if result['detected']:
            self.last_impact_time = current_time
            logger.info(f"Impact detected at {ball_center} with confidence {result['confidence']:.2f}")
        
        return result
    
    def reset(self):
        """重置检测器状态"""
        self.ball_tracker.clear()
        self.last_impact_time = 0
        logger.info("SimpleImpactDetector reset")


def test_velocity_detection():
    """测试速度检测"""
    logger.info("开始测试速度检测...")
    
    detector = SimpleImpactDetector()
    curtain_region = [(50, 50), (590, 50), (590, 430), (50, 430)]
    
    # 模拟球从远处飞向幕布
    start_pos = (100, 100)
    end_pos = (300, 200)
    num_frames = 20
    
    results = []
    
    for i in range(num_frames):
        # 计算球的当前位置
        t = i / (num_frames - 1)
        x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * t)
        y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * t)
        ball_center = (x, y)
        
        # 执行撞击检测
        result = detector.detect_impact(ball_center, curtain_region)
        
        if result['detected']:
            logger.info(f"帧 {i}: 检测到撞击 - {result['reason']} (置信度: {result['confidence']:.2f})")
            results.append({
                'frame': i,
                'position': ball_center,
                'result': result
            })
        
        # 添加小延迟模拟真实帧率
        time.sleep(0.05)
    
    logger.info(f"速度检测测试完成，检测到 {len(results)} 次撞击")
    return results


def test_threshold_detection():
    """测试阈值检测"""
    logger.info("开始测试阈值检测...")
    
    detector = SimpleImpactDetector()
    curtain_region = [(50, 50), (590, 50), (590, 430), (50, 430)]
    
    # 测试不同位置的球
    test_positions = [
        (320, 240),  # 幕布中心
        (100, 100),  # 幕布内
        (30, 30),    # 幕布外
        (600, 400),  # 幕布内
    ]
    
    results = []
    for i, pos in enumerate(test_positions):
        result = detector.detect_impact(pos, curtain_region)
        
        logger.info(f"位置 {pos}: 检测到: {result['detected']}, 置信度: {result['confidence']:.2f}")
        results.append({
            'position': pos,
            'result': result
        })
    
    logger.info(f"阈值检测测试完成")
    return results


def main():
    """主函数"""
    print("🎯 简化撞击检测测试")
    print("="*50)
    
    # 创建配置文件
    try:
        impact_config = ImpactDetectionConfig()
        print("✅ 撞击检测配置文件已加载")
    except Exception as e:
        print(f"❌ 撞击检测配置文件加载失败: {e}")
        return
    
    print("\n开始测试...")
    
    # 运行测试
    velocity_results = test_velocity_detection()
    threshold_results = test_threshold_detection()
    
    # 统计结果
    total_detections = len(velocity_results) + len([r for r in threshold_results if r['result']['detected']])
    print(f"\n测试完成！总共检测到 {total_detections} 次撞击")
    print(f"速度检测: {len(velocity_results)} 次")
    print(f"阈值检测: {len([r for r in threshold_results if r['result']['detected']])} 次")
    
    print("\n✅ 所有测试完成！")


if __name__ == '__main__':
    main()