#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置验证脚本
验证自动生成的配置文件是否正确
"""

import configparser
import os

def verify_config():
    """验证配置文件"""
    print("🔍 验证自动生成的配置文件...")
    
    if not os.path.exists('config.ini'):
        print("❌ 配置文件不存在")
        return False
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # 验证必需的sections
    required_sections = ['Settings', 'ScoreBoard']
    for section in required_sections:
        if not config.has_section(section):
            print(f"❌ 缺少必需的section: {section}")
            return False
    
    # 验证得分圆圈坐标
    score_circles = [
        'circle_20_1_xy',
        'circle_20_2_xy', 
        'circle_30_xy',
        'circle_50_1_xy',
        'circle_50_2_xy'
    ]
    
    print("\n📍 得分圆圈坐标验证:")
    for circle in score_circles:
        if config.has_option('ScoreBoard', circle):
            coords = config.get('ScoreBoard', circle)
            print(f"  ✅ {circle}: {coords}")
        else:
            print(f"  ❌ 缺少: {circle}")
            return False
    
    # 验证边界坐标
    boundary_points = [
        'top_left_xy',
        'top_right_xy',
        'mid_left_xy', 
        'mid_center_xy',
        'mid_right_xy',
        'bottom_left_xy',
        'bottom_center_xy',
        'bottom_right_xy'
    ]
    
    print("\n🔲 边界坐标验证:")
    for point in boundary_points:
        if config.has_option('ScoreBoard', point):
            coords = config.get('ScoreBoard', point)
            print(f"  ✅ {point}: {coords}")
        else:
            print(f"  ❌ 缺少: {point}")
            return False
    
    # 验证圆圈半径
    circle_radii = ['circle_20', 'circle_30', 'circle_50']
    print("\n⚪ 圆圈半径验证:")
    for radius in circle_radii:
        if config.has_option('ScoreBoard', radius):
            value = config.get('ScoreBoard', radius)
            print(f"  ✅ {radius}: {value}")
        else:
            print(f"  ❌ 缺少: {radius}")
            return False
    
    print("\n✅ 配置文件验证通过！")
    return True

def print_config_summary():
    """打印配置摘要"""
    print("\n" + "="*60)
    print("           自动生成配置摘要")
    print("="*60)
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    print(f"\n🏟️  球馆: {config.get('Settings', 'court_name')}")
    print(f"🎯 球道: {config.get('Settings', 'court_number')}")
    print(f"📏 球场长度: {config.get('Settings', 'court_length')}米")
    
    print("\n📍 得分区域坐标 (基于图像识别):")
    print(f"  20分圈1(灯1): {config.get('ScoreBoard', 'circle_20_1_xy')}")
    print(f"  20分圈2(灯2): {config.get('ScoreBoard', 'circle_20_2_xy')}")
    print(f"  30分圈(灯3):  {config.get('ScoreBoard', 'circle_30_xy')}")
    print(f"  50分圈1(灯4): {config.get('ScoreBoard', 'circle_50_1_xy')}")
    print(f"  50分圈2(灯5): {config.get('ScoreBoard', 'circle_50_2_xy')}")
    
    print("\n⚪ 圆圈半径:")
    print(f"  20分圈半径: {config.get('ScoreBoard', 'circle_20')}")
    print(f"  30分圈半径: {config.get('ScoreBoard', 'circle_30')}")
    print(f"  50分圈半径: {config.get('ScoreBoard', 'circle_50')}")
    
    print("\n" + "="*60)

def main():
    """主函数"""
    print("🚀 AI Tennis 配置验证工具")
    print("-" * 40)
    
    # 验证配置
    if verify_config():
        print_config_summary()
        print("\n🎉 配置验证成功！")
        print("\n📋 下一步操作:")
        print("  1. 运行 python3 configure.py 查看可视化效果")
        print("  2. 如果位置准确，运行 python3 score.py 开始计分")
        print("  3. 如需微调，编辑 config.ini 中的相应坐标")
        return 0
    else:
        print("\n❌ 配置验证失败，请检查配置文件")
        return 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)