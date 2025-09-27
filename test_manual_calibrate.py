#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动校准工具测试脚本
用于验证手动校准功能的基本操作
"""
import cv2
import numpy as np
from pathlib import Path

def create_test_image():
    """创建一个测试用的网球幕布图像"""
    # 创建 1280x720 的测试图像
    img = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # 绘制蓝色背景（模拟网球幕布）
    cv2.rectangle(img, (300, 50), (980, 600), (139, 69, 19), -1)  # 深蓝色背景
    
    # 绘制边界线（绿色）
    # 上边界
    cv2.line(img, (320, 70), (960, 70), (0, 255, 0), 3)
    # 下边界  
    cv2.line(img, (340, 580), (940, 580), (0, 255, 0), 3)
    # 左边界
    cv2.line(img, (320, 70), (340, 580), (0, 255, 0), 3)
    # 右边界
    cv2.line(img, (960, 70), (940, 580), (0, 255, 0), 3)
    
    # 绘制中线
    cv2.line(img, (330, 320), (950, 320), (255, 255, 0), 3)
    
    # 绘制得分圆圈（白色圆圈）
    # 20分圈
    cv2.circle(img, (480, 180), 55, (255, 255, 255), 3)
    cv2.circle(img, (800, 180), 55, (255, 255, 255), 3)
    
    # 30分圈  
    cv2.circle(img, (640, 450), 58, (255, 255, 255), 3)
    
    # 50分圈
    cv2.circle(img, (450, 450), 53, (255, 255, 255), 3)
    cv2.circle(img, (830, 450), 53, (255, 255, 255), 3)
    
    # 添加得分标注
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "20", (470, 185), font, 1, (255, 255, 255), 2)
    cv2.putText(img, "20", (790, 185), font, 1, (255, 255, 255), 2)
    cv2.putText(img, "30", (630, 455), font, 1, (255, 255, 255), 2)
    cv2.putText(img, "50", (440, 455), font, 1, (255, 255, 255), 2)
    cv2.putText(img, "50", (820, 455), font, 1, (255, 255, 255), 2)
    
    # 添加区域标注
    cv2.putText(img, "5 Point Area", (500, 120), font, 0.8, (255, 255, 0), 2)
    cv2.putText(img, "10 Point Area", (500, 380), font, 0.8, (255, 255, 0), 2)
    
    return img

def test_manual_calibrate_basic():
    """测试手动校准工具的基本功能"""
    print("创建测试用网球幕布图像...")
    
    # 创建测试图像
    test_img = create_test_image()
    
    # 保存测试图像
    Path("images").mkdir(exist_ok=True)
    test_img_path = "images/test_tennis_screen.jpg"
    cv2.imwrite(test_img_path, test_img)
    
    print(f"测试图像已保存: {test_img_path}")
    print(f"图像尺寸: {test_img.shape[1]} x {test_img.shape[0]}")
    
    # 显示测试图像和校准点位置建议
    print("\n推荐的校准点坐标（基于测试图像）:")
    print("1. 顶部左角(TL): (320, 70)")
    print("2. 顶部右角(TR): (960, 70)")
    print("3. 中线左点(ML): (330, 320)")
    print("4. 中线中心(MC): (640, 320)")  
    print("5. 中线右点(MR): (950, 320)")
    print("6. 底部左角(BL): (340, 580)")
    print("7. 底部中心(BC): (640, 580)")
    print("8. 底部右角(BR): (940, 580)")
    print("9. 20分圈1(灯1): (480, 180)")
    print("10. 20分圈2(灯2): (800, 180)")
    print("11. 30分圈(灯3): (640, 450)")
    print("12. 50分圈1(灯4): (450, 450)")
    print("13. 50分圈2(灯5): (830, 450)")
    
    print(f"\n现在可以使用以下命令测试手动校准:")
    print(f"python manual_calibrate.py")
    print(f"选择选项 2 (图片文件)")
    print(f"输入图片路径: {test_img_path}")
    
    return test_img_path

if __name__ == "__main__":
    test_img_path = test_manual_calibrate_basic()
    
    print(f"\n测试完成！")
    print(f"您可以使用生成的测试图像来验证手动校准工具的功能。")