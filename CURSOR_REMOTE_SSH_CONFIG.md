# Cursor Remote-SSH 配置完成 ✅

## 配置摘要

我已经成功为您配置了Cursor的Remote-SSH插件，用于连接RK3588硬件环境进行AI Tennis项目开发。

### 🔧 已完成的配置

1. **SSH配置文件更新** (`~/.ssh/config`)
   ```ssh
   Host rk3588-aitennis
       HostName 192.168.1.99
       User blueberry
       Port 22
       PasswordAuthentication yes
       PubkeyAuthentication no
       PreferredAuthentications password
   ```

2. **快速连接脚本** (`connect_rk3588.sh`)
   - 网络连通性检查
   - 多种连接方式选择
   - 文件同步功能
   - 远程工具执行

3. **详细说明文档** (`RK3588_SSH_SETUP.md`)
   - 完整的使用指南
   - 故障排除方法
   - 快速命令集合

## 🚀 立即使用

### 方法1: Cursor Remote-SSH (推荐)

1. **打开Cursor**
2. **打开命令面板**: `Cmd+Shift+P` (macOS) 或 `Ctrl+Shift+P` (Windows/Linux)
3. **输入**: `Remote-SSH: Connect to Host...`
4. **选择**: `rk3588-aitennis`
5. **输入密码**: `blueberry`
6. **打开文件夹**: `/home/blueberry/aitennis/score`

### 方法2: 快速连接脚本

```bash
# 运行交互式连接工具
./connect_rk3588.sh

# 选项包括:
# 1. 直接连接
# 2. 进入工作目录
# 3. 运行环境检查
# 4-5. 运行校准工具
# 6. 查看文件
# 7-8. 文件同步
# 9. 使用说明
```

### 方法3: 直接SSH命令

```bash
# 直接连接
ssh rk3588-aitennis

# 进入工作目录
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && bash"

# 执行远程命令
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 demo_info.py"
```

## 🎯 RK3588环境特性

### 硬件信息
- **设备IP**: 192.168.1.99
- **用户**: blueberry
- **密码**: blueberry
- **工作目录**: `/home/blueberry/aitennis/score`

### 软件环境
- **Python**: 3.9.2
- **OpenCV**: 4.10.0
- **GStreamer**: 已安装
- **RK3588**: 硬件加速支持

### 已部署的AI Tennis工具
```
/home/blueberry/aitennis/score/
├── manual_calibrate.py     # 完整版校准工具
├── simple_calibrate.py     # 简化版校准工具
├── configure.py           # 配置查看工具
├── setup_environment.py   # 环境设置工具
├── test_manual_calibrate.py # 测试图像生成
├── demo_info.py           # 项目信息展示
├── score.py              # 主识别程序
├── config.ini            # 当前配置
├── calibration_data/      # 校准数据
└── images/               # 图像文件
```

## 🔄 常用工作流程

### 1. 开发调试流程
```bash
# 1. 连接到RK3588
ssh rk3588-aitennis

# 2. 进入工作目录
cd /home/blueberry/aitennis/score

# 3. 运行环境检查
python3 demo_info.py

# 4. 运行校准工具
python3 simple_calibrate.py

# 5. 验证配置
python3 configure.py

# 6. 运行主程序
python3 score.py
```

### 2. 文件同步流程
```bash
# 上传本地文件到RK3588
scp *.py rk3588-aitennis:/home/blueberry/aitennis/score/

# 下载RK3588文件到本地
scp rk3588-aitennis:/home/blueberry/aitennis/score/config.ini ./
```

### 3. Cursor远程开发流程
1. 在Cursor中连接到RK3588
2. 直接编辑远程文件
3. 在Cursor的终端中运行测试
4. 实时查看结果和日志

## 🛠️ 故障排除

### 连接问题
```bash
# 检查网络
ping 192.168.1.99

# 检查SSH配置
ssh -v rk3588-aitennis

# 重置连接
ssh-keygen -R 192.168.1.99
```

### 权限问题
```bash
# 检查SSH配置文件权限
ls -la ~/.ssh/config

# 修复权限
chmod 600 ~/.ssh/config
```

## 📋 快速命令备忘录

```bash
# 连接命令
ssh rk3588-aitennis                    # 直接连接
./connect_rk3588.sh                    # 交互式连接

# 文件操作
scp file.py rk3588-aitennis:~/aitennis/score/    # 上传文件
scp rk3588-aitennis:~/aitennis/score/config.ini ./  # 下载文件

# 远程执行
ssh rk3588-aitennis "cd ~/aitennis/score && python3 demo_info.py"

# 环境检查
ssh rk3588-aitennis "python3 --version && python3 -c 'import cv2; print(cv2.__version__)'"
```

## ✅ 验证配置

运行以下命令验证配置是否成功：

```bash
# 测试连接
ssh rk3588-aitennis "whoami && pwd"

# 测试工作目录
ssh rk3588-aitennis "ls /home/blueberry/aitennis/score"

# 测试Python环境
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 demo_info.py"
```

如果以上命令都能正常执行，说明配置完全成功！

---

**🎉 配置完成！现在您可以在Cursor中直接连接到RK3588硬件环境，进行AI Tennis项目的开发和测试了！**

有任何问题请参考 `RK3588_SSH_SETUP.md` 详细文档或使用 `./connect_rk3588.sh` 交互式工具。