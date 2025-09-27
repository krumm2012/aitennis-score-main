# -*- coding: utf-8 -*-
"""
撞击检测配置管理模块
用于管理撞击检测的各种参数和设置
"""
import configparser
import os
from typing import Dict, Any


class ImpactDetectionConfig:
    """撞击检测配置管理类"""
    
    def __init__(self, config_file='impact_config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        # 速度变化检测参数
        self.config.add_section('VelocityDetection')
        self.config.set('VelocityDetection', 'velocity_change_threshold', '50.0')
        self.config.set('VelocityDetection', 'position_change_threshold', '20.0')
        self.config.set('VelocityDetection', 'speed_decrease_threshold', '0.7')
        self.config.set('VelocityDetection', 'track_length', '30')
        
        # 区域变化检测参数
        self.config.add_section('RegionDetection')
        self.config.set('RegionDetection', 'curtain_region_dilate_size', '15')
        self.config.set('RegionDetection', 'change_area_threshold', '1000')
        self.config.set('RegionDetection', 'frame_diff_threshold', '25')
        self.config.set('RegionDetection', 'background_history', '500')
        self.config.set('RegionDetection', 'background_var_threshold', '16')
        
        # 阈值判断参数
        self.config.add_section('ThresholdDetection')
        self.config.set('ThresholdDetection', 'impact_zone_margin', '30')
        self.config.set('ThresholdDetection', 'confidence_threshold', '0.6')
        self.config.set('ThresholdDetection', 'min_impact_interval', '0.5')
        
        # 融合检测参数
        self.config.add_section('FusionDetection')
        self.config.set('FusionDetection', 'velocity_weight', '0.4')
        self.config.set('FusionDetection', 'region_weight', '0.3')
        self.config.set('FusionDetection', 'threshold_weight', '0.3')
        
        # 系统设置
        self.config.add_section('System')
        self.config.set('System', 'impact_detection_enabled', 'true')
        self.config.set('System', 'debug_mode', 'false')
        self.config.set('System', 'save_debug_images', 'false')
        
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_velocity_params(self) -> Dict[str, Any]:
        """获取速度检测参数"""
        section = 'VelocityDetection'
        return {
            'velocity_change_threshold': self.config.getfloat(section, 'velocity_change_threshold'),
            'position_change_threshold': self.config.getfloat(section, 'position_change_threshold'),
            'speed_decrease_threshold': self.config.getfloat(section, 'speed_decrease_threshold'),
            'track_length': self.config.getint(section, 'track_length')
        }
    
    def get_region_params(self) -> Dict[str, Any]:
        """获取区域检测参数"""
        section = 'RegionDetection'
        return {
            'curtain_region_dilate_size': self.config.getint(section, 'curtain_region_dilate_size'),
            'change_area_threshold': self.config.getint(section, 'change_area_threshold'),
            'frame_diff_threshold': self.config.getint(section, 'frame_diff_threshold'),
            'background_history': self.config.getint(section, 'background_history'),
            'background_var_threshold': self.config.getint(section, 'background_var_threshold')
        }
    
    def get_threshold_params(self) -> Dict[str, Any]:
        """获取阈值检测参数"""
        section = 'ThresholdDetection'
        return {
            'impact_zone_margin': self.config.getint(section, 'impact_zone_margin'),
            'confidence_threshold': self.config.getfloat(section, 'confidence_threshold'),
            'min_impact_interval': self.config.getfloat(section, 'min_impact_interval')
        }
    
    def get_fusion_params(self) -> Dict[str, Any]:
        """获取融合检测参数"""
        section = 'FusionDetection'
        return {
            'velocity_weight': self.config.getfloat(section, 'velocity_weight'),
            'region_weight': self.config.getfloat(section, 'region_weight'),
            'threshold_weight': self.config.getfloat(section, 'threshold_weight')
        }
    
    def get_system_params(self) -> Dict[str, Any]:
        """获取系统参数"""
        section = 'System'
        return {
            'impact_detection_enabled': self.config.getboolean(section, 'impact_detection_enabled'),
            'debug_mode': self.config.getboolean(section, 'debug_mode'),
            'save_debug_images': self.config.getboolean(section, 'save_debug_images')
        }
    
    def get_all_params(self) -> Dict[str, Any]:
        """获取所有参数"""
        return {
            'velocity': self.get_velocity_params(),
            'region': self.get_region_params(),
            'threshold': self.get_threshold_params(),
            'fusion': self.get_fusion_params(),
            'system': self.get_system_params()
        }
    
    def update_params(self, section: str, params: Dict[str, Any]):
        """更新参数"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        for key, value in params.items():
            self.config.set(section, key, str(value))
        
        self.save_config()
    
    def set_impact_detection_enabled(self, enabled: bool):
        """设置撞击检测是否启用"""
        self.config.set('System', 'impact_detection_enabled', str(enabled).lower())
        self.save_config()
    
    def set_debug_mode(self, enabled: bool):
        """设置调试模式"""
        self.config.set('System', 'debug_mode', str(enabled).lower())
        self.save_config()
    
    def print_config(self):
        """打印当前配置"""
        print("\n" + "="*60)
        print("           撞击检测配置参数")
        print("="*60)
        
        for section_name in self.config.sections():
            print(f"\n【{section_name}】")
            for option in self.config.options(section_name):
                value = self.config.get(section_name, option)
                print(f"  {option}: {value}")
        
        print("\n" + "="*60)


def create_impact_config():
    """创建撞击检测配置文件"""
    config = ImpactDetectionConfig()
    print("✅ 撞击检测配置文件已创建: impact_config.ini")
    config.print_config()
    return config


if __name__ == '__main__':
    create_impact_config()