# AI Tennis 手动校准工具快速开始指南

## 概述

本项目现在提供了三种校准工具来满足不同的使用场景：

1. **manual_calibrate.py** - 完整版手动校准工具（支持RTSP实时视频流）
2. **simple_calibrate.py** - 简化版校准工具（仅支持图片文件，推荐测试使用）
3. **configure.py** - 配置查看和验证工具

## 环境设置

### 基础依赖安装

在macOS上：
```bash
# 安装Python包管理器pipx（推荐）
brew install pipx

# 或者创建虚拟环境
python3 -m venv aitennis_env
source aitennis_env/bin/activate

# 安装必要的包
pip install opencv-python numpy
```

在Ubuntu/Linux上：
```bash
# 安装基础依赖
sudo apt-get update
sudo apt-get install python3-pip python3-opencv python3-numpy

# 或者使用pip安装
pip3 install opencv-python numpy

# 对于完整版（支持RTSP），还需要安装GStreamer
sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly python3-gi
```

### 项目依赖安装

```bash
# 在项目目录下安装所有依赖
pip install -r requirements.txt
```

## 快速开始

### 方法一：简化版校准（推荐新手）

适用于开发测试环境，只需要OpenCV即可：

```bash
# 步骤1：生成测试图像
python3 test_manual_calibrate.py

# 步骤2：启动简化版校准工具
python3 simple_calibrate.py

# 步骤3：按照提示输入图片路径
# 输入: images/test_tennis_screen.jpg

# 步骤4：按照屏幕指示依次点击13个标记点
# 步骤5：按 's' 键保存配置
```

### 方法二：完整版校准（推荐生产环境）

适用于有RK3588硬件和RTSP摄像头的环境：

```bash
# 启动完整版校准工具
python3 manual_calibrate.py

# 选择图像源：
# 1. RTSP视频流 (从摄像头获取当前画面)
# 2. 图片文件 (从本地图片文件)

# 按照屏幕指示完成校准
```

### 方法三：配置验证

验证现有配置是否正确：

```bash
# 启动配置查看工具
python3 configure.py
```

## 校准流程详解

### 13个关键标记点

校准过程需要依次标记以下13个点：

#### 边界点（8个）
1. **顶部左角(TL)** - 幕布左上角边界点
2. **顶部右角(TR)** - 幕布右上角边界点
3. **中线左点(ML)** - 中线与左边界的交点
4. **中线中心(MC)** - 中线的中心点
5. **中线右点(MR)** - 中线与右边界的交点
6. **底部左角(BL)** - 幕布左下角边界点
7. **底部中心(BC)** - 底部边界的中心点
8. **底部右角(BR)** - 幕布右下角边界点

#### 得分圆圈（5个）
9. **20分圈1(灯1)** - 左上角20分圆圈中心
10. **20分圈2(灯2)** - 右上角20分圆圈中心
11. **30分圈(灯3)** - 中央30分圆圈中心
12. **50分圈1(灯4)** - 左下角50分圆圈中心
13. **50分圈2(灯5)** - 右下角50分圆圈中心

### 测试图像参考坐标

如果使用 `test_manual_calibrate.py` 生成的测试图像，推荐以下坐标：

```
边界点：
1. 顶部左角(TL): (320, 70)
2. 顶部右角(TR): (960, 70)
3. 中线左点(ML): (330, 320)
4. 中线中心(MC): (640, 320)
5. 中线右点(MR): (950, 320)
6. 底部左角(BL): (340, 580)
7. 底部中心(BC): (640, 580)
8. 底部右角(BR): (940, 580)

得分圆圈：
9. 20分圈1(灯1): (480, 180)
10. 20分圈2(灯2): (800, 180)
11. 30分圈(灯3): (640, 450)
12. 50分圈1(灯4): (450, 450)
13. 50分圈2(灯5): (830, 450)
```

## 操作说明

### 鼠标操作
- **左键点击**: 标记当前步骤的坐标点
- **右键点击**: 撤销上一步操作（可连续撤销）

### 键盘操作
- **'r' 键**: 重置所有已标记的点，重新开始
- **'s' 键**: 保存当前校准结果到配置文件
- **'q' 键**: 退出校准程序
- **ESC 键**: 退出校准程序

## 输出文件说明

校准完成后会生成以下文件：

### 配置文件
- `config.ini` - 更新的当前系统配置文件
- `config_*_calibrated_YYYYMMDD_HHMMSS.ini` - 带时间戳的配置备份

### 校准数据
- `calibration_data/calibration_YYYYMMDD_HHMMSS.json` - JSON格式的校准数据
- `images/*_calibration_YYYYMMDD_HHMMSS.jpg` - 带标记的校准结果图片

### 数据格式示例

生成的 `config.ini` 文件格式：
```ini
[Settings]
court_name = HeHaa AI TENNIS
court_number = 1
court_length = 8
serve_speed = 25
# ... 其他参数

[ScoreBoard]
# 边界坐标
top_left_xy = 320, 70
top_right_xy = 960, 70
# ... 其他坐标

# 得分圆圈坐标
circle_20_1_xy = 480, 180
circle_20_2_xy = 800, 180
# ... 其他圆圈坐标
```

## 故障排除

### 常见问题

1. **模块导入错误**
   ```
   ModuleNotFoundError: No module named 'cv2'
   ```
   **解决方案**: 安装OpenCV
   ```bash
   pip install opencv-python
   ```

2. **权限错误（macOS）**
   ```
   error: externally-managed-environment
   ```
   **解决方案**: 使用虚拟环境
   ```bash
   python3 -m venv aitennis_env
   source aitennis_env/bin/activate
   pip install opencv-python numpy
   ```

3. **RTSP连接失败**
   ```
   RTSP加载失败
   ```
   **解决方案**: 
   - 检查RTSP地址是否正确
   - 确认网络连接
   - 使用简化版校准工具（图片文件模式）

4. **GStreamer错误**
   ```
   无法解析导入"gi"
   ```
   **解决方案**: 安装GStreamer开发包
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-gi gstreamer1.0-tools
   
   # macOS (使用Homebrew)
   brew install gstreamer gtk+3 pygobject3
   ```

### 调试技巧

1. **使用简化版工具测试**
   ```bash
   python3 simple_calibrate.py
   ```

2. **生成测试图像验证**
   ```bash
   python3 test_manual_calibrate.py
   ```

3. **检查生成的配置文件**
   ```bash
   cat config.ini
   ```

4. **查看校准数据**
   ```bash
   ls -la calibration_data/
   ls -la images/
   ```

## 下一步

校准完成后，您可以：

1. **验证配置**: 使用 `python3 configure.py` 查看配置效果
2. **运行识别**: 使用 `python3 score.py` 开始网球识别
3. **调整参数**: 编辑 `config.ini` 文件微调识别参数
4. **重新校准**: 如果需要，重复校准过程

## 支持

如果遇到问题，请：

1. 检查本文档的故障排除部分
2. 查看项目的 README.md 文件
3. 检查系统日志输出
4. 联系开发团队

---

*本指南涵盖了AI Tennis手动校准工具的完整使用流程，确保您能够快速上手并成功完成校准。*