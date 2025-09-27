# RK3588 Remote SSH 配置说明

## SSH 配置已添加

SSH配置文件 `~/.ssh/config` 已经更新，添加了RK3588硬件环境的配置。

### 配置详情

```ssh
# RK3588 AI Tennis 开发环境
Host rk3588-aitennis
    HostName 192.168.1.99
    User blueberry
    Port 22
    PasswordAuthentication yes
    PubkeyAuthentication no
    PreferredAuthentications password
    # 工作目录: /home/blueberry/aitennis/score
    # 用途: AI Tennis 网球计分系统开发和测试
    
    # 连接优化设置
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    
    # 避免连接超时
    ConnectTimeout 10
```

## 使用方法

### 1. 命令行连接

现在您可以使用简化的命令连接到RK3588：

```bash
# 直接连接
ssh rk3588-aitennis

# 执行远程命令
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && ls -la"

# 连接并进入工作目录
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && bash"
```

### 2. Cursor Remote-SSH 插件使用

#### 步骤1: 打开 Cursor
1. 启动 Cursor 编辑器
2. 按 `Cmd+Shift+P` (macOS) 或 `Ctrl+Shift+P` (Windows/Linux) 打开命令面板

#### 步骤2: 连接远程服务器
1. 输入 `Remote-SSH: Connect to Host...`
2. 选择 `rk3588-aitennis` 
3. 输入密码 `blueberry`
4. 等待连接建立

#### 步骤3: 打开工作目录
1. 连接成功后，点击 "Open Folder"
2. 输入路径: `/home/blueberry/aitennis/score`
3. 点击 "OK"

#### 步骤4: 开始开发
现在您可以在Cursor中直接编辑RK3588上的AI Tennis项目文件了！

## 快速测试工具

### 环境检查脚本
```bash
# 连接并检查环境
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 demo_info.py"
```

### 运行校准工具
```bash
# 运行简化版校准工具
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 simple_calibrate.py"

# 运行完整版校准工具
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 manual_calibrate.py"

# 运行环境设置工具
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 setup_environment.py"
```

### 查看配置
```bash
# 查看当前配置
ssh rk3588-aitennis "cd /home/blueberry/aitennis/score && python3 configure.py"
```

## 文件同步

### 从本地上传到RK3588
```bash
# 上传单个文件
scp file.py rk3588-aitennis:/home/blueberry/aitennis/score/

# 上传整个目录
scp -r local_dir/ rk3588-aitennis:/home/blueberry/aitennis/score/
```

### 从RK3588下载到本地
```bash
# 下载单个文件
scp rk3588-aitennis:/home/blueberry/aitennis/score/config.ini ./

# 下载整个目录
scp -r rk3588-aitennis:/home/blueberry/aitennis/score/images/ ./
```

## 注意事项

### 1. 密码输入
- 每次连接都需要输入密码 `blueberry`
- 建议设置SSH密钥对以免密登录

### 2. 网络要求
- 确保本地网络能访问 `192.168.1.99`
- RK3588设备需要保持开机状态

### 3. 工作目录
- 远程工作目录: `/home/blueberry/aitennis/score`
- 包含所有AI Tennis项目文件

### 4. 环境特性
- Python 3.9.2
- OpenCV 4.10.0
- GStreamer支持
- RK3588硬件加速

## 故障排除

### 连接失败
```bash
# 检查网络连通性
ping 192.168.1.99

# 检查SSH服务
ssh -v rk3588-aitennis
```

### 权限问题
```bash
# 检查SSH配置文件权限
ls -la ~/.ssh/config

# 修复权限（如需要）
chmod 600 ~/.ssh/config
```

### 重置连接
```bash
# 清除已知主机记录（如果有问题）
ssh-keygen -R 192.168.1.99
```

## 快速命令集合

```bash
# 快速连接命令集合
alias rk3588="ssh rk3588-aitennis"
alias rk3588-work="ssh rk3588-aitennis 'cd /home/blueberry/aitennis/score && bash'"
alias rk3588-test="ssh rk3588-aitennis 'cd /home/blueberry/aitennis/score && python3 demo_info.py'"
alias rk3588-calibrate="ssh rk3588-aitennis 'cd /home/blueberry/aitennis/score && python3 simple_calibrate.py'"
```

将以上别名添加到 `~/.zshrc` 或 `~/.bashrc` 文件中，就可以使用简化命令了。

---

**配置完成！** 🎉

现在您可以在Cursor中使用Remote-SSH插件直接连接到RK3588硬件环境进行AI Tennis项目的开发和测试了。