# AI Tennis 撞击检测优化使用指南

## 快速开始

### 1. 启用撞击检测

撞击检测功能已经集成到现有的 `score.py` 系统中。默认情况下，撞击检测是启用的。

### 2. 配置参数

撞击检测参数可以通过 `impact_config.ini` 文件进行配置：

```bash
# 创建默认配置文件
python3 impact_config.py

# 查看当前配置
cat impact_config.ini
```

### 3. 运行测试

```bash
# 运行简化测试（无需OpenCV）
python3 simple_impact_test.py

# 运行完整测试（需要OpenCV）
python3 test_impact_detection.py

# 运行演示
python3 demo_impact_detection.py
```

## 配置参数说明

### 速度检测参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `velocity_change_threshold` | 50.0 | 速度变化阈值 (像素/秒²) |
| `position_change_threshold` | 20.0 | 位置变化阈值 (像素/帧) |
| `speed_decrease_threshold` | 0.7 | 速度下降阈值 |

### 区域检测参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `change_area_threshold` | 1000 | 变化区域面积阈值 |
| `frame_diff_threshold` | 25 | 帧差阈值 |
| `background_history` | 500 | 背景历史帧数 |

### 阈值检测参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `impact_zone_margin` | 30 | 撞击区域边距 |
| `confidence_threshold` | 0.6 | 综合置信度阈值 |
| `min_impact_interval` | 0.5 | 最小撞击间隔（秒） |

## 使用场景

### 场景1：高精度撞击检测

适用于需要高精度撞击检测的场景：

```ini
[ThresholdDetection]
confidence_threshold = 0.8
min_impact_interval = 0.3

[VelocityDetection]
velocity_change_threshold = 30.0
```

### 场景2：快速响应

适用于需要快速响应的场景：

```ini
[ThresholdDetection]
confidence_threshold = 0.4
min_impact_interval = 0.2

[VelocityDetection]
velocity_change_threshold = 80.0
```

### 场景3：减少误检

适用于需要减少误检的场景：

```ini
[ThresholdDetection]
confidence_threshold = 0.7
min_impact_interval = 0.8

[FusionDetection]
velocity_weight = 0.6
region_weight = 0.2
threshold_weight = 0.2
```

## 调试和优化

### 1. 启用调试模式

在配置文件中设置：

```ini
[System]
debug_mode = true
save_debug_images = true
```

### 2. 查看日志

撞击检测的详细信息会记录在日志中：

```
撞击检测: High velocity change; Speed decreasing; 置信度: 0.75
```

### 3. 性能监控

使用内置的统计功能：

```python
# 获取检测统计信息
stats = detector.get_detection_stats()
print(f"总撞击次数: {stats['total_impacts']}")
print(f"平均置信度: {stats['avg_confidence']:.2f}")
```

## 常见问题

### Q1: 撞击检测过于敏感怎么办？

**A**: 调整以下参数：
- 增加 `confidence_threshold`（如从0.6到0.8）
- 增加 `min_impact_interval`（如从0.5到0.8）
- 增加 `velocity_change_threshold`

### Q2: 撞击检测不够敏感怎么办？

**A**: 调整以下参数：
- 减少 `confidence_threshold`（如从0.6到0.4）
- 减少 `min_impact_interval`（如从0.5到0.2）
- 减少 `velocity_change_threshold`

### Q3: 如何优化性能？

**A**: 
- 减少 `track_length`（球轨迹跟踪长度）
- 减少 `background_history`（背景历史帧数）
- 禁用不需要的检测方法

### Q4: 如何集成到现有系统？

**A**: 撞击检测已经集成到 `score.py` 中，只需：
1. 确保 `impact_detector.py` 和 `impact_config.py` 在项目目录中
2. 运行 `python3 impact_config.py` 创建配置文件
3. 根据需要调整配置参数

## 高级用法

### 1. 动态参数调整

```python
# 运行时调整参数
new_params = {
    'velocity_change_threshold': 60.0,
    'confidence_threshold': 0.7
}
detector.update_params(new_params)
```

### 2. 禁用特定检测方法

```python
# 只使用速度检测
detector.params['method_weights'] = {
    'velocity': 1.0,
    'region': 0.0,
    'threshold': 0.0
}
```

### 3. 自定义检测逻辑

可以继承 `ImpactDetector` 类并重写检测方法：

```python
class CustomImpactDetector(ImpactDetector):
    def detect_custom_impact(self, ball_center, curtain_region):
        # 自定义检测逻辑
        pass
```

## 技术支持

如有问题或建议，请：

1. 检查日志文件中的错误信息
2. 运行测试脚本验证功能
3. 查看配置文件是否正确
4. 联系开发团队获取支持

## 更新日志

### v1.0 (2025-01-27)
- 初始版本发布
- 实现三种撞击检测方法
- 支持配置参数调整
- 集成到现有计分系统