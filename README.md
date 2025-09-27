# AI Tennis Score - 智能网球计分系统

> 🚀 **快速开始**: 如果您是新手用户，请先阅读 [QUICK_START.md](QUICK_START.md) 快速开始指南

## 项目概述

这是一个基于OpenCV在RK3588设备上运行的智能网球击打幕布识别系统。系统通过RTSP视频流实时监测网球击中得分幕布的位置，自动计算得分并记录球速等数据。

### 🆕 新增功能

- **手动校准工具**: 交互式鼠标标点校准系统
- **简化版校准**: 仅需OpenCV即可运行的校准工具  
- **环境设置工具**: 自动检查和安装依赖
- **测试图像生成**: 快速生成标准测试图像

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RTSP摄像头    │───→│   RK3588设备    │───→│   计分系统      │
│   (网络摄像头)  │    │   (硬件解码)    │    │   (API后端)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   ZeroMQ消息    │
                    │   (游戏控制)    │
                    └─────────────────┘
```

## 核心功能

### 1. 实时视频流处理
- **RTSP流接收**：通过GStreamer接收网络摄像头的H.264视频流
- **硬件加速解码**：使用RK3588的mppvideodec进行硬件解码
- **自动重连机制**：视频流中断时自动重启管道

### 2. 网球识别与追踪
- **颜色检测**：基于HSV颜色空间检测绿色网球
- **轮廓分析**：通过轮廓周长和圆形度筛选有效目标
- **区域判断**：判断网球是否击中有效得分区域

### 3. 智能计分系统
- **多级得分区**：
  - 20分区域（上方两个圆形区域）
  - 30分区域（下方中央圆形区域）  
  - 50分区域（下方左右两个圆形区域）
  - 10分区域（下半区域其他位置）
  - 5分区域（上半区域其他位置）
- **指哪打哪倍数**：击中指定灯号区域可获得倍数得分
- **球速计算**：根据发球时间和击中时间计算球速(km/h)

### 4. 游戏控制与通信
- **ZeroMQ消息通信**：接收游戏开始/结束/发球指令
- **RESTful API集成**：自动提交得分结果到后端系统
- **实时日志记录**：完整记录所有识别和计分过程

## 文件结构说明

```
score/
├── README.md              # 项目说明文档
├── QUICK_START.md         # 快速开始指南
├── configure.py           # 识别区域配置查看工具
├── manual_calibrate.py    # 手动校准标点工具（完整版，支持RTSP）
├── simple_calibrate.py    # 简化版校准工具（仅图片文件）
├── test_manual_calibrate.py  # 校准测试工具
├── setup_environment.py   # 环境设置工具
├── demo_info.py          # 项目演示信息工具
├── quick_calibrate.sh     # 快速校准脚本
├── score.py              # 主要计分识别程序
├── config.ini            # 系统配置文件
├── config/
│   ├── __init__.py
│   └── config.py         # 配置加载器
├── calibration_data/      # 校准数据存储目录
└── images/               # 识别结果图片存储目录
    ├── 1286/            # 按游戏ID分组存储
    ├── 1292/
    └── ...
```

## 核心模块详解

### configure.py - 识别区域配置查看工具
专业的可视化配置查看和验证工具：
- **RTSPStreamProcessor类**：增强的RTSP视频流处理器
- **核心功能**：
  - 🎯 实时显示所有边界区域和得分圆圈
  - 📍 智能坐标标注系统（TL/TR/ML/MC/MR/BL/BC/BR）
  - 🔍 可视化区域划分（5分区域/10分区域标注）
  - 📊 实时系统信息显示（帧数、时间、球馆信息）
  - ✅ 配置参数验证和错误检查
  - 📷 自动配置图片生成（每30帧保存）
- **特色功能**：
  - 边界多边形绘制和半透明填充
  - 十字靶心精确标记
  - 灯号和得分对应关系显示
  - 防超界文字定位算法
  - 专业启动横幅和配置摘要
- **用途**：部署验证、角度调试、坐标检查、识别区域可视化
- **输出**：时间戳命名的高质量配置图片

### manual_calibrate.py - 手动校准标点工具
交互式鼠标校准工具，专为精确坐标标定设计：
- **ManualCalibrator类**：鼠标交互式校准处理器
- **核心功能**：
  - 🖱️ 鼠标左键点击标记坐标点
  - 🖱️ 鼠标右键撤销上一步操作
  - 🎯 13个关键点依次标记（8个边界点+5个得分圈）
  - 📐 实时预览边界区域和得分圆圈
  - 💾 自动生成新的配置文件
  - 📊 完整的校准摘要报告
- **支持的图像源**：
  - RTSP实时视频流（推荐）
  - 本地图片文件
- **校准流程**：
  - 按步骤指示依次标记13个关键点
  - 实时显示已标记点和预览效果
  - 支持撤销和重置操作
  - 自动保存配置文件和校准数据
- **输出文件**：
  - `config.ini`：更新当前配置
  - `config_manual_calibrated_TIMESTAMP.ini`：带时间戳的备份
  - `calibration_data/calibration_TIMESTAMP.json`：校准数据
  - `images/manual_calibration_TIMESTAMP.jpg`：校准图片
- **用途**：首次部署校准、重新校准、精确坐标调整

### simple_calibrate.py - 简化版校准工具
基于OpenCV的轻量级校准工具，适用于开发和测试环境：
- **SimpleCalibrator类**：简化的鼠标交互式校准处理器
- **核心功能**：
  - 🖱️ 鼠标左键点击标记坐标点
  - 🖱️ 鼠标右键撤销上一步操作
  - 🎯 13个关键点依次标记（8个边界点+5个得分圈）
  - 📐 实时预览边界区域和得分圆圈
  - 💾 自动生成新的配置文件
  - 📊 完整的校准摘要报告
- **适用场景**：
  - 开发和测试环境
  - 没有RK3588硬件的情况
  - 基于图片文件的校准
  - 快速原型验证
- **输入源**：仅支持本地图片文件
- **输出文件**：
  - `config.ini`：更新当前配置
  - `config_simple_calibrated_TIMESTAMP.ini`：带时间戳的备份
  - `calibration_data/simple_calibration_TIMESTAMP.json`：校准数据
  - `images/simple_calibration_TIMESTAMP.jpg`：校准图片
- **用途**：开发测试、离线校准、快速验证

### test_manual_calibrate.py - 校准测试工具
生成测试用网球幕布图像的辅助工具：
- **create_test_image()**: 生成标准的测试用网球幕布图像
- **功能特性**：
  - 🎯 1280x720分辨率的标准测试图像
  - 🟦 蓝色幕布背景模拟真实环境
  - ⚪ 白色得分圆圈（5个不同分值区域）
  - 🟢 绿色边界线标记有效区域
  - 🟡 黄色中线分割5分/10分区域
  - 📍 推荐校准坐标显示
- **输出文件**：`images/test_tennis_screen.jpg`
- **用途**：校准测试、功能验证、演示展示

### setup_environment.py - 环境设置工具
自动化环境配置和依赖安装工具：
- **功能特性**：
  - 🔍 自动检查Python版本和已安装模块
  - 📦 智能安装缺失的依赖包
  - 🎯 支持多种安装方式（pip3、虚拟环境、系统包管理器）
  - 🖼️ 自动创建测试图像
  - 📋 提供下一步操作指引
- **支持平台**：
  - macOS（pip3、虚拟环境、brew）
  - Linux（apt-get、pip3、虚拟环境）
  - Windows（pip3、虚拟环境）
- **用途**：快速环境配置、依赖检查、新手入门

### score.py - 主计分识别程序
系统的核心识别和计分模块：
- **TennisStreamProcessor类**：主要处理器
- **游戏状态管理**：通过ZeroMQ接收游戏控制指令
- **网球检测流程**：
  1. 获取视频帧
  2. HSV颜色空间转换
  3. 绿色区域掩膜提取
  4. 高斯模糊降噪
  5. 轮廓检测与筛选
  6. 圆形度验证
  7. 区域判断与计分
- **数据提交**：自动调用API提交得分结果

### config.py - 配置管理器
统一管理系统所有配置参数：
- **ConfigLoader类**：从config.ini加载配置
- **参数类型**：
  - 球场物理参数（长度、球速）
  - 得分区域坐标配置
  - 图像识别参数
  - 系统运行参数

## 配置文件说明

### config.ini 主要参数

#### [Settings] - 系统设置
```ini
court_name = HeHaa AI TENNIS    # 球馆名称
court_number = 1                # 场地编号
court_length = 8                # 球场长度(米)
serve_speed = 25                # 发球机球速(米/秒)
court_length_tuneup = 0         # 球场长度调整值
min_girth = 250                 # 最小轮廓周长
circularity = 0.85              # 圆形度阈值(85%)
swing_time = 350                # 挥拍时延(毫秒)
locating_time = 0               # 寻位时延(毫秒)
save_image = true               # 是否保存识别图片
rtsp_url = rtsp://admin:password@ip:554/path  # RTSP地址
```

#### [ScoreBoard] - 得分板配置
```ini
# 得分圆圈大小
circle_20 = 60                  # 20分圈半径
circle_30 = 60                  # 30分圈半径  
circle_50 = 55                  # 50分圈半径

# 得分圆圈坐标(x,y)
circle_20_1_xy = 495, 210       # 左侧20分圈
circle_20_2_xy = 855, 210       # 右侧20分圈
circle_30_xy = 680, 470         # 30分圈
circle_50_1_xy = 480, 470       # 左侧50分圈
circle_50_2_xy = 880, 460       # 右侧50分圈

# 边界坐标点
top_left_xy = 358, 60           # 顶部左角
top_right_xy = 980, 60          # 顶部右角
mid_left_xy = 345, 340          # 中线左点
mid_center_xy = 680, 333        # 中线中心
mid_right_xy = 988, 330         # 中线右点
bottom_left_xy = 360, 580       # 底部左角
bottom_center_xy = 680, 580     # 底部中心
bottom_right_xy = 970, 570      # 底部右角

# 其他参数
y_offset = 20                   # Y坐标补偿
multiple = 1                    # 得分倍数
```

## 安装与部署

### 系统要求
- **硬件**：RK3588开发板或兼容设备
- **操作系统**：Ubuntu 20.04/22.04 或其他Linux发行版
- **Python版本**：Python 3.7+

### 一键快速校准（推荐新手）
使用自动化校准脚本：
```bash
# 一键运行完整校准流程
./quick_calibrate.sh

# 或者分步骤运行
./quick_calibrate.sh --setup     # 仅环境设置
./quick_calibrate.sh --calibrate # 仅运行校准
./quick_calibrate.sh --verify    # 仅验证配置
```

### 手动环境设置
使用环境设置工具：
```bash
# 自动检查和安装所有依赖
python3 setup_environment.py

# 按照提示选择安装方式
# 工具会自动创建测试图像并提供下一步指引
```

### 手动安装
#### 基础Python依赖
```bash
# 方法1: 使用pip3
pip3 install opencv-python numpy requests pyzmq

# 方法2: 使用虚拟环境（推荐）
python3 -m venv aitennis_env
source aitennis_env/bin/activate
pip install -r requirements.txt

# 方法3: 在macOS上使用--break-system-packages
pip3 install --break-system-packages opencv-python numpy requests pyzmq
```

#### 系统级依赖
```bash
# Ubuntu/Debian
sudo apt-get install python3-opencv python3-numpy python3-requests

# 安装GStreamer (完整版校准工具需要)
sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly python3-gi

# 安装RK3588 MPP解码器
# (具体安装方法取决于RK3588 SDK版本)
```

### 配置摄像头
1. 确保网络摄像头支持RTSP协议
2. 修改`config.ini`中的`rtsp_url`参数
3. 运行配置工具验证视频流：
```bash
python configure.py
```

### 运行系统
```bash
# 启动主计分程序
python score.py
```

## 使用说明

### 1. 区域配置和校准

#### 方法一：手动校准（推荐首次使用）
使用交互式手动校准工具进行精确坐标标定：

##### 启动手动校准工具
```bash
python manual_calibrate.py
```

##### 手动校准详细流程
1. **选择图像源**：
   ```bash
   请选择校准图像源:
   1. RTSP视频流 (从摄像头获取当前画面)    # 推荐
   2. 图片文件 (从本地图片文件)
   ```

2. **依次标记13个关键点**：
   - **边界点标记**（8个点）：
     - 顶部左角(TL) → 顶部右角(TR)
     - 中线左点(ML) → 中线中心(MC) → 中线右点(MR)
     - 底部左角(BL) → 底部中心(BC) → 底部右角(BR)
   - **得分圈标记**（5个点）：
     - 20分圈1(灯1) → 20分圈2(灯2)
     - 30分圈(灯3)
     - 50分圈1(灯4) → 50分圈2(灯5)

3. **实时预览和调整**：
   - 实时显示边界多边形和得分圆圈
   - 右键点击可撤销上一步操作
   - 按 'r' 键重置所有标记
   - 按 's' 键保存当前配置

4. **自动生成配置文件**：
   - `config.ini`：更新当前系统配置
   - `config_manual_calibrated_YYYYMMDD_HHMMSS.ini`：带时间戳的备份
   - `calibration_data/calibration_YYYYMMDD_HHMMSS.json`：校准数据记录
   - `images/manual_calibration_YYYYMMDD_HHMMSS.jpg`：校准结果图片

##### 手动校准操作说明
- **鼠标左键**：标记当前步骤的坐标点
- **鼠标右键**：撤销上一步操作，可连续撤销
- **'r' 键**：重置所有已标记的点，重新开始
- **'s' 键**：保存当前校准结果到配置文件
- **'q' 键**：退出校准程序

##### 校准质量检查
完成校准后系统会显示校准摘要：
```
【校准时间】: 2025-01-08 16:30:15
【校准点数】: 13
【图像尺寸】: 1920 x 1080

【边界坐标】
  顶部左角(TL): (358, 60)
  顶部右角(TR): (980, 60)
  ...

【得分区域】
  20分圈1(灯1): (495, 210)
  20分圈2(灯2): (855, 210)
  ...
```

#### 方法二：简化版校准（推荐测试环境）
使用基于OpenCV的简化版校准工具，适用于开发测试：

##### 生成测试图像
```bash
# 先生成测试用的网球幕布图像
python test_manual_calibrate.py
```

##### 启动简化版校准工具
```bash
python simple_calibrate.py
```

##### 简化版校准流程
1. **输入图片路径**：
   ```bash
   请选择要校准的图片文件:
   建议使用: images/test_tennis_screen.jpg
   请输入图片文件路径: images/test_tennis_screen.jpg
   ```

2. **按照测试图像的推荐坐标进行标记**：
   - 系统会显示推荐的校准坐标
   - 按顺序点击13个关键点
   - 实时预览校准效果

3. **保存配置**：
   - 按 's' 键保存校准结果
   - 自动生成配置文件和校准数据

##### 简化版校准的优势
- ✅ 不依赖GStreamer和RK3588硬件
- ✅ 仅需OpenCV和基本Python库
- ✅ 适合开发环境快速测试
- ✅ 可以使用任何网球幕布图片
- ✅ 生成标准格式的配置文件

#### 方法三：配置验证和查看
使用配置查看工具验证现有配置：

##### 启动配置查看工具
```bash
python configure.py
```

#### 配置工具功能说明
1. **自动启动检查**：
   - 显示专业启动横幅
   - 自动验证配置文件完整性
   - 检查RTSP连接状态

2. **实时可视化显示**：
   - 🔴 红色边界多边形：完整的幕布有效识别区域
   - 🟡 黄色中线：5分/10分区域分界线
   - 🔵 彩色得分圈：不同颜色标识不同分值
   - ⚪ 白色标记点：8个关键边界坐标点
   - 📋 坐标标注：TL/TR/ML/MC/MR/BL/BC/BR标识

3. **智能标注系统**：
   - **坐标显示**：每个关键点显示实际像素坐标
   - **得分信息**：每个圆圈显示分值和对应灯号
   - **区域标注**：明确标识5分区域和10分区域
   - **系统信息**：实时显示帧数、时间、球馆信息

4. **配置校准流程**：
   ```bash
   # 步骤1：启动配置工具
   python configure.py
   
   # 步骤2：观察视频流显示
   # - 检查红色边界是否正确框住幕布
   # - 确认得分圆圈位置是否准确
   # - 验证坐标标注是否符合实际
   
   # 步骤3：调整配置参数
   # 编辑 config.ini 中的坐标参数
   
   # 步骤4：重新启动验证
   # 按 'q' 退出，修改配置后重新运行
   ```

5. **配置图片生成**：
   - 自动保存：每30帧生成一张配置图片
   - 文件命名：`configure_YYYYMMDD_HHMMSS_frameXXX.jpg`
   - 保存位置：`images/` 目录
   - 用途：文档记录、远程调试、配置存档

#### 坐标参数调整指南
根据可视化显示调整以下参数：
- **边界坐标**：`top_left_xy`, `top_right_xy`, `bottom_left_xy`, `bottom_right_xy`
- **中线坐标**：`mid_left_xy`, `mid_center_xy`, `mid_right_xy`
- **得分圆圈**：`circle_20_1_xy`, `circle_20_2_xy`, `circle_30_xy`, `circle_50_1_xy`, `circle_50_2_xy`
- **圆圈大小**：`circle_20`, `circle_30`, `circle_50`

### 2. 计分流程
系统通过ZeroMQ接收以下消息格式：
- **开始游戏**：`begin {game_id} {game_type}`
- **发球指令**：`ball {game_id} {ball_number} {light} {serve_time} {interval}`
- **结束游戏**：`end {game_id}`

### 3. 得分规则
- **区域得分**：根据击中位置自动判定基础得分
- **倍数得分**：击中指定灯号(light)区域时得分翻倍
- **球速计算**：自动计算并记录球速数据
- **API提交**：识别结果自动提交到`http://localhost:8000/game_serve/update_score/`

### 4. 日志监控
系统运行时会生成详细日志：
- **文件日志**：`tennis_score_YYYYMMDD_HHMMSS.log`
- **控制台输出**：实时显示识别状态
- **图片保存**：识别成功时保存带标记的图片

## 技术特性

### 高性能视频处理
- **硬件解码**：利用RK3588的MPP硬件解码器
- **零拷贝**：GStreamer管道减少内存拷贝
- **异步处理**：多线程处理视频流和消息

### 高精度识别算法
- **HSV颜色检测**：在不同光照条件下稳定检测绿色球
- **形状验证**：通过圆形度筛选真实网球
- **区域几何判断**：精确的多边形和圆形区域判断

### 鲁棒性设计
- **自动重连**：视频流中断自动恢复
- **异常处理**：完善的错误处理和日志记录
- **参数调优**：丰富的可调参数适应不同环境

## 故障排除

### 常见问题

1. **视频流无法连接**
   - 检查RTSP地址是否正确
   - 确认网络连通性
   - 验证摄像头用户名密码

2. **识别精度不高**
   - 调整`circularity`圆形度阈值
   - 修改`min_girth`最小轮廓参数
   - 检查光照条件和球的颜色

3. **坐标不准确**
   - 使用`configure.py`重新校准
   - 调整摄像头角度和距离
   - 修改相应坐标参数

4. **球速计算异常**
   - 检查`serve_speed`发球机速度设置
   - 调整`swing_time`和`locating_time`时延参数
   - 验证时间同步

### 调试方法
```bash
# 启用图片保存进行调试
save_image = true

# 查看详细日志
tail -f tennis_score_*.log

# 测试视频流
gst-launch-1.0 rtspsrc location=rtsp://... ! autovideosink
```

## 开发说明

### 代码结构
- **模块化设计**：清晰的类结构和职责分离
- **配置驱动**：所有参数通过配置文件管理
- **异步架构**：视频处理、消息处理、API调用分离
- **日志系统**：完整的日志记录和轮转

### 扩展开发
- **新得分区域**：在`get_score`方法中添加新的判断逻辑
- **识别算法**：在`process_frame`中实现新的检测算法
- **通信协议**：在`zmq_message_handler`中添加新的消息类型
- **数据输出**：修改`call_score_api`实现新的数据格式

## 版本信息

- **项目名称**：AI Tennis Score
- **开发者**：MXCHIP
- **版本**：v1.0
- **发布日期**：2025-01-02

## 联系方式

如有技术问题或改进建议，请联系开发团队。

---

*本系统专为智能网球训练场景设计，提供准确可靠的自动计分解决方案。*