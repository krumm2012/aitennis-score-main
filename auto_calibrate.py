# -*- coding: utf-8 -*-
"""
AI Tennis 自动坐标校准工具
功能：
1. 自动识别图像中的边界和得分区域
2. 智能检测白色圆形目标的位置和大小
3. 自动生成精确的config.ini配置文件
"""
import cv2
import numpy as np
import configparser
import os
import sys
from pathlib import Path
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutoCalibrator:
    def __init__(self, image_path=None, debug_mode=False):
        """
        自动校准器初始化
        Args:
            image_path: 配置图片路径，如果为None则使用最新的配置图片
            debug_mode: 是否启用调试模式，保存中间检测结果
        """
        self.image_path = image_path
        self.image = None
        self.results = {}
        self.debug_mode = debug_mode
        
        # 检测参数 - 根据实际幕布图像优化
        self.params = {
            'white_circle_threshold': (180, 255),  # 白色圆圈检测阈值
            'blue_area_threshold': (90, 130, 120, 255, 50, 200),  # HSV蓝色区域阈值 (深蓝色幕布)
            'min_circle_radius': 30,  # 最小圆圈半径
            'max_circle_radius': 70,  # 最大圆圈半径
            'contour_area_threshold': 1000,  # 轮廓面积阈值
            'min_curtain_area': 50000,  # 最小幕布面积阈值
        }
        
        logger.info("AutoCalibrator initialized")

    def load_image(self):
        """加载图像"""
        if self.image_path is None:
            # 自动查找最新的配置图片
            image_dir = Path("images")
            if not image_dir.exists():
                raise FileNotFoundError("Images directory not found")
            
            config_images = list(image_dir.glob("configure_*.jpg"))
            if not config_images:
                raise FileNotFoundError("No configuration images found")
            
            # 按修改时间排序，获取最新的
            self.image_path = max(config_images, key=lambda p: p.stat().st_mtime)
            logger.info(f"Using latest image: {self.image_path}")
        
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"Could not load image: {self.image_path}")
        
        logger.info(f"Image loaded: {self.image.shape}")
        return self.image

    def detect_blue_curtain_boundary(self):
        """检测蓝色幕布边界"""
        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        
        # 创建蓝色掩膜
        lower_blue = np.array([self.params['blue_area_threshold'][0], 
                              self.params['blue_area_threshold'][2], 
                              self.params['blue_area_threshold'][4]])
        upper_blue = np.array([self.params['blue_area_threshold'][1], 
                              self.params['blue_area_threshold'][3], 
                              self.params['blue_area_threshold'][5]])
        
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 调试模式：保存原始蓝色掩膜
        if self.debug_mode:
            cv2.imwrite('debug_blue_mask_raw.jpg', blue_mask)
            logger.info("Saved debug_blue_mask_raw.jpg")
        
        # 增强形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_CLOSE, kernel)
        blue_mask = cv2.morphologyEx(blue_mask, cv2.MORPH_OPEN, kernel)
        
        # 调试模式：保存处理后的蓝色掩膜
        if self.debug_mode:
            cv2.imwrite('debug_blue_mask_processed.jpg', blue_mask)
            logger.info("Saved debug_blue_mask_processed.jpg")
        
        # 查找轮廓
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            logger.error("No blue curtain found")
            return None
        
        # 过滤小面积轮廓，找到最大的蓝色区域（应该是幕布）
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > self.params['min_curtain_area']]
        
        if not valid_contours:
            logger.error(f"No large blue areas found (min area: {self.params['min_curtain_area']})")
            return None
        
        largest_contour = max(valid_contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        logger.info(f"Found curtain contour with area: {contour_area}")
        
        # 使用轮廓的实际形状来确定边界点，而不是简单的矩形
        # 获取轮廓的外接矩形
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # 分析轮廓的实际形状特征
        # 获取轮廓在不同高度的宽度
        top_y = y
        mid_y = y + h // 2
        bottom_y = y + h
        
        # 在不同高度找到左右边界点
        def find_contour_boundaries_at_y(contour, target_y):
            """在指定Y坐标找轮廓的左右边界"""
            points_at_y = []
            for point in contour:
                px, py = point[0]
                if abs(py - target_y) <= 5:  # 允许5像素的误差
                    points_at_y.append(px)
            
            if points_at_y:
                return min(points_at_y), max(points_at_y)
            return None, None
        
        # 计算8个关键边界点
        # 顶部边界
        top_left_x, top_right_x = find_contour_boundaries_at_y(largest_contour, top_y)
        if top_left_x is None:
            top_left_x, top_right_x = x, x + w
        
        # 中线边界
        mid_left_x, mid_right_x = find_contour_boundaries_at_y(largest_contour, mid_y)
        if mid_left_x is None:
            mid_left_x, mid_right_x = x, x + w
        
        # 底部边界
        bottom_left_x, bottom_right_x = find_contour_boundaries_at_y(largest_contour, bottom_y)
        if bottom_left_x is None:
            bottom_left_x, bottom_right_x = x, x + w
        
        boundary_points = {
            'top_left_xy': (top_left_x, top_y),
            'top_right_xy': (top_right_x, top_y),
            'mid_left_xy': (mid_left_x, mid_y),
            'mid_center_xy': ((mid_left_x + mid_right_x) // 2, mid_y),
            'mid_right_xy': (mid_right_x, mid_y),
            'bottom_left_xy': (bottom_left_x, bottom_y),
            'bottom_center_xy': ((bottom_left_x + bottom_right_x) // 2, bottom_y),
            'bottom_right_xy': (bottom_right_x, bottom_y)
        }
        
        logger.info(f"Blue curtain boundary detected: {boundary_points}")
        return boundary_points

    def detect_white_circles(self):
        """检测白色圆形目标"""
        # 转换为灰度
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # 使用自适应阈值和固定阈值结合
        # 自适应阈值
        adaptive_mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY, 11, 2)
        
        # 固定阈值
        _, fixed_mask = cv2.threshold(gray, self.params['white_circle_threshold'][0], 
                                     self.params['white_circle_threshold'][1], cv2.THRESH_BINARY)
        
        # 结合两种掩膜
        white_mask = cv2.bitwise_and(adaptive_mask, fixed_mask)
        
        # 调试模式：保存白色检测掩膜
        if self.debug_mode:
            cv2.imwrite('debug_white_mask_adaptive.jpg', adaptive_mask)
            cv2.imwrite('debug_white_mask_fixed.jpg', fixed_mask)
            cv2.imwrite('debug_white_mask_combined.jpg', white_mask)
            logger.info("Saved white detection masks")
        
        # 增强形态学处理
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        
        # 去除小噪点
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel_open)
        
        # 调试模式：保存最终白色掩膜
        if self.debug_mode:
            cv2.imwrite('debug_white_mask_final.jpg', white_mask)
            logger.info("Saved debug_white_mask_final.jpg")
        
        # 查找轮廓
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        circles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.params['contour_area_threshold']:
                continue
            
            # 计算圆形度
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # 降低圆形度要求，因为图像中的圆可能不完美
            if circularity > 0.5:  # 降低圆形度阈值
                # 获取外接圆
                (x, y), radius = cv2.minEnclosingCircle(contour)
                
                # 验证半径范围
                if self.params['min_circle_radius'] <= radius <= self.params['max_circle_radius']:
                    # 额外验证：检查轮廓的长宽比
                    rect = cv2.boundingRect(contour)
                    aspect_ratio = rect[2] / rect[3] if rect[3] > 0 else 0
                    
                    # 圆形的长宽比应该接近1
                    if 0.7 <= aspect_ratio <= 1.3:
                        circles.append({
                            'center': (int(x), int(y)),
                            'radius': int(radius),
                            'area': area,
                            'circularity': circularity,
                            'aspect_ratio': aspect_ratio
                        })
        
        # 按圆形度和面积综合排序
        circles.sort(key=lambda c: (c['circularity'] * 0.7 + (c['area'] / 10000) * 0.3), reverse=True)
        
        logger.info(f"Detected {len(circles)} white circles")
        for i, circle in enumerate(circles):
            logger.info(f"Circle {i+1}: center={circle['center']}, radius={circle['radius']}, "
                       f"circularity={circle['circularity']:.3f}, area={circle['area']}")
        
        return circles

    def classify_score_regions(self, circles, boundary_points):
        """分类得分区域"""
        if len(circles) < 5:
            logger.warning(f"Expected 5 circles, found {len(circles)}")
        
        # 获取图像中心和边界信息
        img_height, img_width = self.image.shape[:2]
        img_center_x = img_width // 2
        
        # 根据位置分类圆圈
        upper_y_threshold = boundary_points['mid_center_xy'][1]  # 中线Y坐标
        
        score_regions = {}
        
        # 分为上半部分和下半部分
        upper_circles = [c for c in circles if c['center'][1] < upper_y_threshold]
        lower_circles = [c for c in circles if c['center'][1] >= upper_y_threshold]
        
        # 上半部分：20分圈（2个）
        upper_circles.sort(key=lambda c: c['center'][0])  # 按X坐标排序
        if len(upper_circles) >= 2:
            score_regions['circle_20_1_xy'] = upper_circles[0]['center']
            score_regions['circle_20_2_xy'] = upper_circles[1]['center']
            score_regions['circle_20'] = max(upper_circles[0]['radius'], upper_circles[1]['radius'])
        
        # 下半部分：30分圈（中间）+ 50分圈（左右两个）
        lower_circles.sort(key=lambda c: c['center'][0])  # 按X坐标排序
        
        if len(lower_circles) >= 3:
            # 左边50分圈
            score_regions['circle_50_1_xy'] = lower_circles[0]['center']
            score_regions['circle_50'] = lower_circles[0]['radius']
            
            # 中间30分圈
            score_regions['circle_30_xy'] = lower_circles[1]['center']
            score_regions['circle_30'] = lower_circles[1]['radius']
            
            # 右边50分圈
            score_regions['circle_50_2_xy'] = lower_circles[2]['center']
            # 使用50分圈的平均半径
            if 'circle_50' in score_regions:
                score_regions['circle_50'] = (score_regions['circle_50'] + lower_circles[2]['radius']) // 2
        
        logger.info(f"Score regions classified: {score_regions}")
        return score_regions

    def generate_config(self, boundary_points, score_regions):
        """生成配置文件"""
        # 读取现有配置作为模板
        config = configparser.ConfigParser()
        
        # 如果存在配置文件，读取非坐标参数
        if os.path.exists('config.ini'):
            config.read('config.ini')
        else:
            # 创建默认配置
            config.add_section('Settings')
            config.add_section('ScoreBoard')
        
        # 确保sections存在
        if not config.has_section('Settings'):
            config.add_section('Settings')
        if not config.has_section('ScoreBoard'):
            config.add_section('ScoreBoard')
        
        # 保留原有的非坐标设置
        default_settings = {
            'court_name': 'HeHaa AI TENNIS',
            'court_name_font_size': '3',
            'court_number': '1',
            'court_length': '8',
            'serve_speed': '25',
            'court_length_tuneup': '0',
            'serve_time': '0',
            'min_girth': '250',
            'circularity': '0.85',
            'locating_time': '0',
            'swing_time': '350',
            'save_image': 'true',
            'rtsp_url': 'rtsp://admin:Mxchip5538@192.168.20.166:554/h264/ch1/main/av_stream'
        }
        
        for key, default_value in default_settings.items():
            if not config.has_option('Settings', key):
                config.set('Settings', key, default_value)
        
        # 设置显示参数
        display_settings = {
            'point_size': '5',
            'point_color': '0, 0, 255',
            'line_width': '2',
            'line_color': '0, 255, 0',
            'ball_color': '0, 204, 0',
            'y_offset': '20',
            'multiple': '1'
        }
        
        for key, value in display_settings.items():
            config.set('ScoreBoard', key, value)
        
        # 设置自动检测的坐标
        # 边界坐标
        for key, (x, y) in boundary_points.items():
            config.set('ScoreBoard', key, f'{x}, {y}')
        
        # 得分区域坐标和半径
        for key, value in score_regions.items():
            if key.endswith('_xy'):
                x, y = value
                config.set('ScoreBoard', key, f'{x}, {y}')
            else:
                config.set('ScoreBoard', key, str(value))
        
        return config

    def save_config(self, config, backup=True):
        """保存配置文件"""
        config_path = 'config.ini'
        
        # 备份原配置
        if backup and os.path.exists(config_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'config_backup_{timestamp}.ini'
            os.rename(config_path, backup_path)
            logger.info(f"Original config backed up to: {backup_path}")
        
        # 保存新配置
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        logger.info(f"New configuration saved to: {config_path}")

    def save_detection_result(self, boundary_points, score_regions, circles):
        """保存检测结果（用于调试）"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'image_path': str(self.image_path),
            'boundary_points': boundary_points,
            'score_regions': score_regions,
            'detected_circles': circles
        }
        
        result_path = f'detection_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detection result saved to: {result_path}")

    def draw_detection_result(self, boundary_points, score_regions, circles):
        """绘制检测结果"""
        debug_image = self.image.copy()
        
        # 绘制检测到的圆圈
        for i, circle in enumerate(circles):
            center = circle['center']
            radius = circle['radius']
            cv2.circle(debug_image, center, radius, (0, 255, 0), 2)
            cv2.circle(debug_image, center, 3, (0, 0, 255), -1)
            cv2.putText(debug_image, f"C{i+1}", (center[0]-10, center[1]-radius-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 绘制边界点
        for label, (x, y) in boundary_points.items():
            cv2.circle(debug_image, (x, y), 5, (255, 0, 0), -1)
            cv2.putText(debug_image, label[:2].upper(), (x+10, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        
        # 绘制分类后的得分区域
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        score_items = [(k, v) for k, v in score_regions.items() if k.endswith('_xy')]
        
        for i, (key, (x, y)) in enumerate(score_items):
            color = colors[i % len(colors)]
            cv2.circle(debug_image, (x, y), 8, color, -1)
            cv2.putText(debug_image, key.replace('circle_', '').replace('_xy', ''),
                       (x+15, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 保存调试图片
        debug_path = f'auto_calibrate_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        cv2.imwrite(debug_path, debug_image)
        logger.info(f"Debug image saved to: {debug_path}")
        
        return debug_image

    def run_auto_calibration(self):
        """运行自动校准"""
        try:
            logger.info("Starting auto calibration...")
            
            # 1. 加载图像
            self.load_image()
            
            # 2. 检测蓝色幕布边界
            boundary_points = self.detect_blue_curtain_boundary()
            if boundary_points is None:
                raise ValueError("Failed to detect curtain boundary")
            
            # 3. 检测白色圆形目标
            circles = self.detect_white_circles()
            if len(circles) < 3:
                raise ValueError(f"Insufficient circles detected: {len(circles)}")
            
            # 4. 分类得分区域
            score_regions = self.classify_score_regions(circles, boundary_points)
            
            # 5. 生成配置
            config = self.generate_config(boundary_points, score_regions)
            
            # 6. 保存结果
            self.save_config(config)
            self.save_detection_result(boundary_points, score_regions, circles)
            self.draw_detection_result(boundary_points, score_regions, circles)
            
            logger.info("Auto calibration completed successfully!")
            
            # 打印结果摘要
            self.print_calibration_summary(boundary_points, score_regions)
            
            return True
            
        except Exception as e:
            logger.error(f"Auto calibration failed: {e}")
            return False

    def print_calibration_summary(self, boundary_points, score_regions):
        """打印校准结果摘要"""
        print("\n" + "="*60)
        print("           自动校准结果摘要")
        print("="*60)
        
        print("\n【检测到的边界坐标】")
        for key, (x, y) in boundary_points.items():
            print(f"  {key}: ({x}, {y})")
        
        print("\n【检测到的得分区域】")
        for key, value in score_regions.items():
            if key.endswith('_xy'):
                x, y = value
                print(f"  {key}: ({x}, {y})")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "="*60)
        print("配置文件已自动生成并保存到 config.ini")
        print("请运行 python configure.py 验证新配置")
        print("="*60)


def main():
    """主函数"""
    print_banner()
    
    # 解析命令行参数
    import sys
    image_path = None
    debug_mode = False
    
    # 正确处理命令行参数
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '--debug' or arg == '-d':
            debug_mode = True
            print("🐛 调试模式已启用，将保存中间检测结果")
        elif not arg.startswith('-'):
            # 这是图片路径
            if image_path is None:
                image_path = arg
        i += 1
    
    # 创建自动校准器
    calibrator = AutoCalibrator(image_path, debug_mode)
    
    # 运行自动校准
    success = calibrator.run_auto_calibration()
    
    if success:
        print("\n🎉 自动校准成功完成！")
        print("📁 生成的文件：")
        print("   - config.ini (新配置文件)")
        print("   - auto_calibrate_result_*.jpg (检测结果图)")
        print("   - detection_result_*.json (详细检测数据)")
        print("\n🔄 下一步：运行 python configure.py 验证配置")
    else:
        print("\n❌ 自动校准失败，请检查日志信息")
        return 1
    
    return 0


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                AI Tennis 自动校准工具                        ║
    ║                Auto Calibration Tool                         ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  功能: 基于图像识别自动生成精确的配置坐标                    ║
    ║  版本: v1.0                                                  ║
    ║  开发: MXCHIP                                                ║
    ╚══════════════════════════════════════════════════════════════╝
    
    【智能检测功能】
    🎯 自动识别蓝色幕布边界
    ⚪ 智能检测白色圆形目标
    📊 自动分类得分区域
    ⚙️ 智能生成配置文件
    
    【使用说明】
    - 自动使用最新的配置图片进行分析
    - 或指定图片路径: python auto_calibrate.py image_path
    - 启用调试模式: python auto_calibrate.py --debug
    - 调试模式会保存中间检测结果到debug_*.jpg
    - 自动备份原配置文件
    - 生成详细的检测结果
    
    """
    print(banner)


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)