# nonebot_plugin_bili2mp4

[![pypi](https://img.shields.io/pypi/v/nonebot_plugin_bili2mp4.svg)](https://pypi.org/project/nonebot_plugin_bili2mp4)
[![nonebot](https://img.shields.io/badge/nonebot-2-red)](https://nonebot.dev/)

在指定群内自动将B站小程序/分享链接解析并下载为MP4后发送的NoneBot2插件。

## 功能特点

- 自动检测群内B站分享链接和小程序卡片
- 自动下载视频并转换为MP4格式发送
- 支持私聊管理开启/停止转换功能
- 支持设置B站Cookie以获取更高清视频
- 支持自定义视频清晰度和大小限制
- 管理员可配置的权限控制系统
- 支持短链接自动展开
- 自动处理B站小程序卡片

## 安装

### 通过nb-cli安装（推荐）

```bash
nb plugin install nonebot-plugin-bili2mp4
```

### 通过pip安装

```bash
pip install nonebot-plugin-bili2mp4
```

### 从源码安装

```bash
git clone https://github.com/shengwang52005/nonebot-plugin-bili2mp4.git
cd nonebot-plugin-bili2mp4
pip install -e .
```

## 使用方法

### 前置要求

1. 确保系统已安装FFmpeg并添加到环境变量
2. 确保网络环境可以访问B站

### 配置

在NoneBot的配置文件中添加以下配置：

```python
# 超级管理员QQ号列表（可私聊控制本插件）
super_admins = [1234567890]  # 替换为你的QQ号
```

### 命令说明

超级管理员私聊命令：

1. `转换<群号>` - 开启指定群的B站视频转换功能
2. `停止转换<群号>` - 停止指定群的B站视频转换功能
3. `设置B站COOKIE <cookie字符串>` - 设置B站Cookie，用于获取更高清视频
4. `清除B站COOKIE` - 清除已设置的B站Cookie
5. `设置清晰度<数字>` - 设置视频清晰度（如 720/1080，0 代表不限制）
6. `设置最大大小<数字>MB` - 设置视频大小限制（0 代表不限制）
7. `查看参数` - 查看当前配置参数
8. `查看转换列表` - 查看已开启转换功能的群列表

### 使用流程

1. 超级管理员私聊机器人，使用`转换<群号>`命令开启指定群的功能
2. 群成员发送B站分享链接或小程序卡片
3. 机器人自动解析链接，下载视频并转换为MP4格式发送到群中
4. 如需停止功能，超级管理员可使用`停止转换<群号>`命令

### 获取B站Cookie

1. 登录B站网页版
2. 打开浏览器开发者工具 (F12)
3. 刷新页面
4. 在网络(Network)标签中找到任意请求
5. 在请求头中找到Cookie字段
6. 复制完整的Cookie字符串

### 配置示例

```python
# NoneBot配置文件示例
CONFIG = {
    "super_admins": [1234567890],  # 替换为你的QQ号
    # 其他配置...
}
```

## 依赖项

- Python 3.8+
- nonebot2>=2.0.0
- nonebot-adapter-onebot>=2.0.0
- pydantic>=1.10.0
- yt-dlp>=2023.3.4
- aiofiles>=0.8.0
- loguru>=0.6.0
- ffmpeg (系统级依赖)

## 注意事项

1. 本插件需要系统安装FFmpeg，用于视频格式转换
   - Windows: 下载FFmpeg二进制包并添加到PATH
   - Linux: 使用包管理器安装，如 `apt install ffmpeg`
   - macOS: 使用Homebrew安装，如 `brew install ffmpeg`

2. 插件会自动下载并管理yt-dlp用于视频下载

3. 设置B站Cookie可以获取更高清的视频，但不是必须的

4. 下载视频会消耗服务器资源和带宽，请合理使用

5. 大文件下载可能需要较长时间，请耐心等待

## 故障排除

### 常见问题

1. **FFmpeg未找到**
   - 确保已安装FFmpeg并添加到系统PATH
   - 检查环境变量设置

2. **下载失败**
   - 检查网络连接
   - 尝试设置B站Cookie
   - 检查视频是否可用或是否有地区限制

3. **内存占用过高**
   - 调整视频清晰度限制
   - 设置视频大小限制

## 开发

### 本地测试

```bash
# 克隆仓库
git clone https://github.com/shengwang52005/nonebot-plugin-bili2mp4.git
cd nonebot-plugin-bili2mp4

# 安装依赖
pip install -e .[dev]

# 运行测试
pytest
```

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 贡献

欢迎提交Issue和Pull Request来帮助改进这个插件！

## 作者

shengwang52005

## 致谢

感谢以下项目和贡献者：
- [NoneBot](https://github.com/nonebot/nonebot2)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)