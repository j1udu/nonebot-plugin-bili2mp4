<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-bili2mp4

_✨ NoneBot2 插件，自动将B站视频转换为MP4并分享 ✨_


<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/j1udu/nonebot-plugin-bili2mp4.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-bili2mp4">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-bili2mp4.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

这是一个用于 NoneBot2 的插件，可以在指定的QQ群中自动检测B站分享链接和小程序卡片，并将这些B站视频自动下载并转换为MP4格式后发送到群中。
## 📖 介绍

nonebot-plugin-bili2mp4 是一个用于 NoneBot2 的插件，主要功能包括：

- 自动检测群聊中的B站视频分享链接和小程序卡片识别并转换为MP4格式发到群里
- 支持识别B站短链接
- 支持控制开启的群
- 支持自定义视频清晰度、大小限制等参数
- 支持设置B站Cookie以获取更高清晰度或者大会员限定视频

## 💿 安装
 
<details open>
<summary>使用 nb-cli 安装</summary>

在 nonebot2 项目的根目录下打开命令行，输入以下指令：
```bash
nb plugin install nonebot-plugin-bili2mp4
```
</details>

<details open>
<summary>使用包管理器安装</summary>

在 nonebot2 项目的根目录下，打开命令行，根据你使用的包管理器，输入相应的安装命令
<details open>
<summary>pip</summary>

```bash
pip install nonebot-plugin-bili2mp4
```
</details>

打开 nonebot2 项目根目录下的 pyproject.toml 文件, 在 [tool.nonebot] 部分追加写入
```toml
plugins = ["nonebot_plugin_bili2mp4"]
```
</details>

## 📦 依赖

<details open>
<summary>yt-dlp</summary>

如果创建项目时使用了虚拟环境请在虚拟环境内安装依赖
```bash
pip install yt-dlp
```
</details>

<details open>
<summary>ffmpeg</summary>

插件依赖FFmpeg进行视频格式转换，需要手动安装：
**Windows:**
1. 访问 [FFmpeg官网](https://ffmpeg.org/) 下载Windows版本
2. 解压下载的压缩包到任意目录（如 `C:\ffmpeg`）
3. 将 `ffmpeg.exe` 所在目录添加到系统环境变量PATH中
4. 在命令行中运行 `ffmpeg -version` 验证安装是否成功

**Linux :**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```
</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| super_admins | 是 | [] | 管理员QQ号列表 |


## 🎉 使用

### 指令表
| 指令 | 说明 |
|:-----:|:-----:|
| fhelp | 显示所有管理员可用命令的帮助信息 |
| 转换 <群号> | 开启指定群的B站视频转换功能 |
| 停止转换 <群号> | 停止指定群的B站视频转换功能 |
| 设置B站COOKIE <cookie字符串> | 设置B站Cookie |
| 清除B站COOKIE | 清除已设置的B站Cookie |
| 设置清晰度 <数字> | 设置视频清晰度 |
| 设置最大大小 <数字>MB | 设置视频大小限制 |
| 查看参数 | 查看当前配置参数 |
| 查看转换列表 | 查看已开启转换功能的群列表 |

**注**：
以上指令均需管理员私聊bot

Cookie可以不设置，设置大会员账号的cookie可以获取更高清晰度或者大会员限定视频

Cookie中至少需要包含SESSDATA、bili_jct、DedeUserID和buvid3/buvid4四个字段
## 效果图
<img src="images/picture1.png" width="500">
<img src="images/picture2.png" width="500">
