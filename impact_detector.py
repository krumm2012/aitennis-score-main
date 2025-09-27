# -*- coding: utf-8 -*-
"""
AI Tennis 撞击点检测优化模块
功能：
1. 基于速度变化率的撞击检测
2. 基于幕布区域变化的撞击检测
3. 基于阈值的撞击判断
4. 多方法融合的智能撞击检测
"""
import cv2
import numpy as np
import logging
from collections import deque
from typing import Tuple, List, Optional, Dict
import time

logger = logging.getLogger(__name__)


class BallTracker:
    """球轨迹跟踪器"""
    
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
                velocity = np.sqrt(vx**2 + vy**2)
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
            
        # 计算速度变化率（加速度的绝对值）
        velocity_changes = []
        for i in range(1, len(recent_velocities)):
            change = abs(recent_velocities[i] - recent_velocities[i-1])
            velocity_changes.append(change)
        
        return np.mean(velocity_changes) if velocity_changes else 0
    
    def get_position_change_rate(self, window_size: int = 3) -> float:
        """获取位置变化率"""
        if len(self.positions) < window_size:
            return 0
        
        recent_positions = list(self.positions)[-window_size:]
        if len(recent_positions) < 2:
            return 0
            
        # 计算位置变化率
        position_changes = []
        for i in range(1, len(recent_positions)):
            prev_x, prev_y = recent_positions[i-1]
            curr_x, curr_y = recent_positions[i]
            change = np.sqrt((curr_x - prev_x)**2 + (curr_y - prev_y)**2)
            position_changes.append(change)
        
        return np.mean(position_changes) if position_changes else 0
    
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


class BackgroundSubtractor:
    """背景减除器"""
    
    def __init__(self, history=500, varThreshold=16, detectShadows=True):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history, 
            varThreshold=varThreshold, 
            detectShadows=detectShadows
        )
        self.background_initialized = False
        self.frames_for_init = 30
        self.frame_count = 0
        
    def update(self, frame: np.ndarray) -> np.ndarray:
        """更新背景模型并返回前景掩膜"""
        self.frame_count += 1
        
        # 前30帧用于初始化背景
        if self.frame_count <= self.frames_for_init:
            self.bg_subtractor.apply(frame)
            return np.zeros_like(frame[:, :, 0])
        
        # 获取前景掩膜
        fg_mask = self.bg_subtractor.apply(frame)
        
        if self.frame_count == self.frames_for_init + 1:
            self.background_initialized = True
            logger.info("Background model initialized")
        
        return fg_mask


class FrameDifferencer:
    """帧间差分器"""
    
    def __init__(self, threshold=30):
        self.threshold = threshold
        self.prev_frame = None
        self.prev_gray = None
        
    def compute_difference(self, frame: np.ndarray) -> np.ndarray:
        """计算帧间差分"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return np.zeros_like(gray)
        
        # 计算帧差
        diff = cv2.absdiff(gray, self.prev_gray)
        
        # 二值化
        _, binary_diff = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)
        
        # 更新前一帧
        self.prev_gray = gray.copy()
        
        return binary_diff


class ImpactDetector:
    """撞击点检测器"""
    
    def __init__(self, config):
        self.config = config
        self.ball_tracker = BallTracker(max_track_length=30)
        self.background_subtractor = BackgroundSubtractor()
        self.frame_differencer = FrameDifferencer()
        
        # 加载撞击检测配置
        try:
            from impact_config import ImpactDetectionConfig
            self.impact_config = ImpactDetectionConfig()
            self.params = self._load_params_from_config()
        except ImportError:
            logger.warning("撞击检测配置文件未找到，使用默认参数")
            self.params = self._get_default_params()
        
        # 根据配置更新组件参数
        self._update_component_params()
        
        # 状态变量
        self.last_impact_time = 0
        self.min_impact_interval = self.params.get('min_impact_interval', 0.5)
        self.impact_history = deque(maxlen=10)
        
        logger.info("ImpactDetector initialized")
    
    def _get_default_params(self):
        """获取默认参数"""
        return {
            # 速度变化检测参数
            'velocity_change_threshold': 50.0,
            'position_change_threshold': 20.0,
            'speed_decrease_threshold': 0.7,
            'track_length': 30,
            
            # 区域变化检测参数
            'curtain_region_dilate_size': 15,
            'change_area_threshold': 1000,
            'frame_diff_threshold': 25,
            'background_history': 500,
            'background_var_threshold': 16,
            
            # 阈值判断参数
            'impact_zone_margin': 30,
            'confidence_threshold': 0.6,
            'min_impact_interval': 0.5,
            
            # 融合检测参数
            'method_weights': {
                'velocity': 0.4,
                'region': 0.3,
                'threshold': 0.3
            }
        }
    
    def _load_params_from_config(self):
        """从配置文件加载参数"""
        all_config = self.impact_config.get_all_params()
        
        params = {}
        
        # 速度检测参数
        velocity_params = all_config.get('velocity', {})
        params.update({
            'velocity_change_threshold': velocity_params.get('velocity_change_threshold', 50.0),
            'position_change_threshold': velocity_params.get('position_change_threshold', 20.0),
            'speed_decrease_threshold': velocity_params.get('speed_decrease_threshold', 0.7),
            'track_length': velocity_params.get('track_length', 30)
        })
        
        # 区域检测参数
        region_params = all_config.get('region', {})
        params.update({
            'curtain_region_dilate_size': region_params.get('curtain_region_dilate_size', 15),
            'change_area_threshold': region_params.get('change_area_threshold', 1000),
            'frame_diff_threshold': region_params.get('frame_diff_threshold', 25),
            'background_history': region_params.get('background_history', 500),
            'background_var_threshold': region_params.get('background_var_threshold', 16)
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
    
    def _update_component_params(self):
        """根据配置更新组件参数"""
        # 更新球跟踪器
        self.ball_tracker = BallTracker(max_track_length=self.params.get('track_length', 30))
        
        # 更新背景减除器
        self.background_subtractor = BackgroundSubtractor(
            history=self.params.get('background_history', 500),
            varThreshold=self.params.get('background_var_threshold', 16)
        )
        
        # 更新帧间差分器
        self.frame_differencer = FrameDifferencer(
            threshold=self.params.get('frame_diff_threshold', 25)
        )
    
    def update_params(self, new_params: dict):
        """更新参数"""
        self.params.update(new_params)
        self._update_component_params()
        self.min_impact_interval = self.params.get('min_impact_interval', 0.5)
        logger.info(f"Impact detection parameters updated: {new_params}")
    
    def reload_config(self):
        """重新加载配置"""
        try:
            if hasattr(self, 'impact_config'):
                self.impact_config.load_config()
                self.params = self._load_params_from_config()
                self._update_component_params()
                logger.info("Impact detection configuration reloaded")
        except Exception as e:
            logger.error(f"Failed to reload impact detection config: {e}")
    
    def detect_velocity_based_impact(self, ball_center: Tuple[int, int]) -> Dict:
        """基于速度变化的撞击检测"""
        x, y = ball_center
        self.ball_tracker.add_position(x, y)
        
        result = {
            'detected': False,
            'confidence': 0.0,
            'reason': '',
            'velocity': self.ball_tracker.get_current_velocity(),
            'velocity_change_rate': self.ball_tracker.get_velocity_change_rate(),
            'position_change_rate': self.ball_tracker.get_position_change_rate(),
            'speed_decreasing': self.ball_tracker.is_speed_decreasing()
        }
        
        # 检查速度变化率
        velocity_change = result['velocity_change_rate']
        if velocity_change > self.params['velocity_change_threshold']:
            result['confidence'] += 0.4
            result['reason'] += 'High velocity change; '
        
        # 检查位置变化率
        position_change = result['position_change_rate']
        if position_change > self.params['position_change_threshold']:
            result['confidence'] += 0.3
            result['reason'] += 'High position change; '
        
        # 检查速度下降
        if result['speed_decreasing']:
            result['confidence'] += 0.3
            result['reason'] += 'Speed decreasing; '
        
        # 判断是否检测到撞击
        if result['confidence'] > 0.5:
            result['detected'] = True
            
        return result
    
    def detect_region_based_impact(self, frame: np.ndarray, curtain_region: np.ndarray) -> Dict:
        """基于区域变化的撞击检测"""
        result = {
            'detected': False,
            'confidence': 0.0,
            'reason': '',
            'change_area': 0,
            'frame_diff_area': 0
        }
        
        # 获取幕布区域的掩膜
        curtain_mask = self._create_curtain_mask(frame, curtain_region)
        
        # 背景减除检测
        bg_mask = self.background_subtractor.update(frame)
        bg_mask = cv2.bitwise_and(bg_mask, curtain_mask)
        
        # 帧间差分检测
        frame_diff = self.frame_differencer.compute_difference(frame)
        frame_diff = cv2.bitwise_and(frame_diff, curtain_mask)
        
        # 计算变化区域面积
        bg_contours, _ = cv2.findContours(bg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bg_area = sum(cv2.contourArea(cnt) for cnt in bg_contours if cv2.contourArea(cnt) > 100)
        
        diff_contours, _ = cv2.findContours(frame_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        diff_area = sum(cv2.contourArea(cnt) for cnt in diff_contours if cv2.contourArea(cnt) > 100)
        
        result['change_area'] = bg_area
        result['frame_diff_area'] = diff_area
        
        # 判断区域变化
        if bg_area > self.params['change_area_threshold']:
            result['confidence'] += 0.5
            result['reason'] += 'Background change detected; '
        
        if diff_area > self.params['change_area_threshold']:
            result['confidence'] += 0.5
            result['reason'] += 'Frame difference detected; '
        
        # 判断是否检测到撞击
        if result['confidence'] > 0.4:
            result['detected'] = True
            
        return result
    
    def detect_threshold_based_impact(self, ball_center: Tuple[int, int], 
                                    curtain_region: np.ndarray) -> Dict:
        """基于阈值的撞击判断"""
        x, y = ball_center
        
        result = {
            'detected': False,
            'confidence': 0.0,
            'reason': '',
            'in_impact_zone': False,
            'distance_to_curtain': 0
        }
        
        # 检查球是否在撞击区域内
        impact_zones = self._get_impact_zones(curtain_region)
        in_zone = False
        
        for zone in impact_zones:
            if self._point_in_zone((x, y), zone):
                in_zone = True
                break
        
        result['in_impact_zone'] = in_zone
        
        if in_zone:
            result['confidence'] = 0.8
            result['reason'] = 'Ball in impact zone; '
            result['detected'] = True
        
        # 计算到幕布的距离
        distance = self._distance_to_curtain((x, y), curtain_region)
        result['distance_to_curtain'] = distance
        
        if distance < self.params['impact_zone_margin']:
            result['confidence'] = max(result['confidence'], 0.6)
            result['reason'] += 'Close to curtain; '
            if not result['detected']:
                result['detected'] = True
        
        return result
    
    def detect_impact(self, frame: np.ndarray, ball_center: Tuple[int, int], 
                     curtain_region: np.ndarray) -> Dict:
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
        
        # 执行各种检测方法
        velocity_result = self.detect_velocity_based_impact(ball_center)
        region_result = self.detect_region_based_impact(frame, curtain_region)
        threshold_result = self.detect_threshold_based_impact(ball_center, curtain_region)
        
        # 融合检测结果
        final_result = self._fuse_detection_results(
            velocity_result, region_result, threshold_result
        )
        
        # 如果检测到撞击，更新状态
        if final_result['detected']:
            self.last_impact_time = current_time
            self.impact_history.append({
                'time': current_time,
                'position': ball_center,
                'confidence': final_result['confidence'],
                'method': final_result['method']
            })
            
            logger.info(f"Impact detected at {ball_center} with confidence {final_result['confidence']:.2f}")
        
        return final_result
    
    def _fuse_detection_results(self, velocity_result: Dict, region_result: Dict, 
                              threshold_result: Dict) -> Dict:
        """融合多种检测方法的结果"""
        weights = self.params['method_weights']
        
        # 计算加权置信度
        total_confidence = (
            velocity_result['confidence'] * weights['velocity'] +
            region_result['confidence'] * weights['region'] +
            threshold_result['confidence'] * weights['threshold']
        )
        
        # 确定检测方法
        method = 'unknown'
        if velocity_result['detected']:
            method = 'velocity'
        elif region_result['detected']:
            method = 'region'
        elif threshold_result['detected']:
            method = 'threshold'
        
        # 综合判断
        detected = (
            total_confidence > self.params['confidence_threshold'] or
            (velocity_result['detected'] and region_result['detected']) or
            (velocity_result['detected'] and threshold_result['detected']) or
            (region_result['detected'] and threshold_result['detected'])
        )
        
        # 构建原因字符串
        reasons = []
        if velocity_result['detected']:
            reasons.append(f"Velocity: {velocity_result['reason']}")
        if region_result['detected']:
            reasons.append(f"Region: {region_result['reason']}")
        if threshold_result['detected']:
            reasons.append(f"Threshold: {threshold_result['reason']}")
        
        return {
            'detected': detected,
            'confidence': total_confidence,
            'reason': '; '.join(reasons),
            'method': method,
            'velocity_result': velocity_result,
            'region_result': region_result,
            'threshold_result': threshold_result
        }
    
    def _create_curtain_mask(self, frame: np.ndarray, curtain_region: np.ndarray) -> np.ndarray:
        """创建幕布区域掩膜"""
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        # 使用幕布区域坐标创建掩膜
        if len(curtain_region) >= 3:
            cv2.fillPoly(mask, [curtain_region], 255)
        
        # 膨胀操作，扩展检测区域
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                         (self.params['curtain_region_dilate_size'], 
                                          self.params['curtain_region_dilate_size']))
        mask = cv2.dilate(mask, kernel, iterations=1)
        
        return mask
    
    def _get_impact_zones(self, curtain_region: np.ndarray) -> List[np.ndarray]:
        """获取撞击区域"""
        zones = []
        
        # 在幕布区域周围创建撞击检测区域
        margin = self.params['impact_zone_margin']
        
        for point in curtain_region:
            x, y = point[0]
            # 创建以该点为中心的圆形区域
            zone = np.array([[
                [x - margin, y - margin],
                [x + margin, y - margin],
                [x + margin, y + margin],
                [x - margin, y + margin]
            ]], dtype=np.int32)
            zones.append(zone)
        
        return zones
    
    def _point_in_zone(self, point: Tuple[int, int], zone: np.ndarray) -> bool:
        """判断点是否在区域内"""
        x, y = point
        return cv2.pointPolygonTest(zone, (x, y), False) >= 0
    
    def _distance_to_curtain(self, point: Tuple[int, int], curtain_region: np.ndarray) -> float:
        """计算点到幕布的最短距离"""
        if len(curtain_region) == 0:
            return float('inf')
        
        distances = []
        for contour_point in curtain_region:
            px, py = contour_point[0]
            dist = np.sqrt((point[0] - px)**2 + (point[1] - py)**2)
            distances.append(dist)
        
        return min(distances) if distances else float('inf')
    
    def reset(self):
        """重置检测器状态"""
        self.ball_tracker.clear()
        self.background_subtractor = BackgroundSubtractor()
        self.frame_differencer = FrameDifferencer()
        self.last_impact_time = 0
        self.impact_history.clear()
        logger.info("ImpactDetector reset")
    
    def get_detection_stats(self) -> Dict:
        """获取检测统计信息"""
        if not self.impact_history:
            return {'total_impacts': 0, 'avg_confidence': 0}
        
        confidences = [impact['confidence'] for impact in self.impact_history]
        return {
            'total_impacts': len(self.impact_history),
            'avg_confidence': np.mean(confidences),
            'max_confidence': np.max(confidences),
            'min_confidence': np.min(confidences),
            'recent_impacts': list(self.impact_history)[-5:]  # 最近5次撞击
        }