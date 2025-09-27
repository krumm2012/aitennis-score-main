# AI Tennis 撞击检测优化

## 概述

本模块实现了优化的撞击点检测算法，通过多种检测方法的融合，提高了撞击检测的准确性和可靠性。

## 主要特性

### 1. 多方法融合检测
- **速度变化检测**: 基于球的速度和位置变化率
- **区域变化检测**: 基于幕布区域的背景减除和帧间差分
- **阈值判断**: 基于球进入特定区域的阈值检测

### 2. 智能算法
- 球轨迹跟踪和速度计算
- 背景建模和前景检测
- 帧间差分分析
- 多方法置信度融合

### 3. 可配置参数
- 所有检测参数可通过配置文件调整
- 支持运行时参数更新
- 提供默认参数和优化建议

## 文件结构

```
├── impact_detector.py          # 核心撞击检测模块
├── impact_config.py            # 配置管理模块
├── test_impact_detection.py    # 测试脚本
├── demo_impact_detection.py    # 演示脚本
├── impact_config.ini           # 配置文件（自动生成）
└── IMPACT_DETECTION_README.md  # 本文档
```

## 检测方法详解

### 1. 速度变化检测 (Velocity-based Detection)

**原理**: 当球快速接近幕布并在某一帧突然减速或消失时，判断为撞击。

**关键参数**:
- `velocity_change_threshold`: 速度变化阈值 (像素/秒²)
- `position_change_threshold`: 位置变化阈值 (像素/帧)
- `speed_decrease_threshold`: 速度下降阈值

**算法流程**:
1. 跟踪球的连续位置
2. 计算瞬时速度和加速度
3. 检测速度的急剧变化
4. 判断速度下降趋势

### 2. 区域变化检测 (Region-based Detection)

**原理**: 检测幕布区域的异常变化，结合背景减除和帧间差分。

**关键参数**:
- `change_area_threshold`: 变化区域面积阈值
- `frame_diff_threshold`: 帧差阈值
- `background_var_threshold`: 背景方差阈值

**算法流程**:
1. 建立背景模型
2. 检测前景变化
3. 计算帧间差分
4. 分析变化区域特征

### 3. 阈值判断 (Threshold-based Detection)

**原理**: 设定阈值，当球的位置进入幕布的特定区域时判断为撞击。

**关键参数**:
- `impact_zone_margin`: 撞击区域边距
- `confidence_threshold`: 综合置信度阈值

**算法流程**:
1. 定义撞击检测区域
2. 计算球到幕布的距离
3. 判断是否进入撞击区域

## 配置参数

### 速度检测参数
```ini
[VelocityDetection]
velocity_change_threshold = 50.0    # 速度变化阈值
position_change_threshold = 20.0    # 位置变化阈值
speed_decrease_threshold = 0.7      # 速度下降阈值
track_length = 30                   # 跟踪长度
```

### 区域检测参数
```ini
[RegionDetection]
curtain_region_dilate_size = 15     # 幕布区域膨胀大小
change_area_threshold = 1000        # 变化区域面积阈值
frame_diff_threshold = 25           # 帧差阈值
background_history = 500            # 背景历史帧数
background_var_threshold = 16       # 背景方差阈值
```

### 阈值检测参数
```ini
[ThresholdDetection]
impact_zone_margin = 30             # 撞击区域边距
confidence_threshold = 0.6          # 综合置信度阈值
min_impact_interval = 0.5           # 最小撞击间隔（秒）
```

### 融合检测参数
```ini
[FusionDetection]
velocity_weight = 0.4               # 速度检测权重
region_weight = 0.3                 # 区域检测权重
threshold_weight = 0.3              # 阈值检测权重
```

## 使用方法

### 1. 基本使用

```python
from impact_detector import ImpactDetector
from config.config import ConfigLoader

# 加载配置
config = ConfigLoader()

# 创建撞击检测器
detector = ImpactDetector(config)

# 检测撞击
impact_result = detector.detect_impact(frame, ball_position, curtain_region)

if impact_result['detected']:
    print(f"检测到撞击！方法: {impact_result['method']}")
    print(f"置信度: {impact_result['confidence']:.2f}")
```

### 2. 集成到现有系统

在 `score.py` 中已经集成了撞击检测功能：

```python
# 初始化时
self.impact_detector = ImpactDetector(configure)

# 在process_frame中使用
impact_result = self.impact_detector.detect_impact(frame, ball_position, curtain_region)
if impact_result['detected']:
    # 处理撞击事件
    pass
```

### 3. 参数调整

```python
# 更新检测参数
new_params = {
    'velocity_change_threshold': 60.0,
    'confidence_threshold': 0.7
}
detector.update_params(new_params)

# 重新加载配置
detector.reload_config()
```

## 测试和验证

### 1. 运行测试

```bash
python test_impact_detection.py
```

测试包括：
- 速度检测测试
- 区域变化检测测试
- 阈值检测测试
- 综合检测测试

### 2. 运行演示

```bash
python demo_impact_detection.py
```

演示包括：
- 自动演示场景
- 交互式演示

### 3. 创建配置文件

```bash
python impact_config.py
```

## 性能优化

### 1. 算法优化
- 使用高效的背景减除算法
- 优化轨迹跟踪算法
- 减少不必要的计算

### 2. 参数调优
- 根据实际环境调整阈值
- 优化检测权重分配
- 调整跟踪长度和采样频率

### 3. 系统集成
- 与现有球检测系统无缝集成
- 最小化性能影响
- 支持动态启用/禁用

## 故障排除

### 1. 常见问题

**问题**: 撞击检测过于敏感
**解决**: 调整 `confidence_threshold` 和 `min_impact_interval` 参数

**问题**: 撞击检测不准确
**解决**: 检查球检测质量，调整速度变化阈值

**问题**: 性能影响较大
**解决**: 减少跟踪长度，优化背景减除参数

### 2. 调试模式

启用调试模式获取详细信息：

```python
# 在配置文件中设置
[System]
debug_mode = true
save_debug_images = true
```

### 3. 日志分析

检查日志文件中的撞击检测信息：
```
撞击检测: High velocity change; Speed decreasing; 置信度: 0.75
```

## 未来改进

### 1. 算法改进
- 深度学习模型集成
- 更精确的轨迹预测
- 多球检测支持

### 2. 功能扩展
- 撞击强度评估
- 撞击角度分析
- 历史数据统计

### 3. 性能优化
- GPU加速支持
- 并行处理优化
- 内存使用优化

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请联系开发团队。