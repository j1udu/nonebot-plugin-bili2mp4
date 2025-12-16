# NoneBot插件配置示例
# 复制此文件到你的NoneBot项目目录并根据需要修改

from nonebot import get_driver

# 超级管理员QQ号列表（可私聊控制本插件）
# 将下面的数字替换为你的QQ号
SUPER_ADMINS = [1234567890]  # 替换为你的QQ号

# 以下配置可以根据需要添加到你的NoneBot配置文件中

# 插件配置示例
from nonebot_plugin_bili2mp4 import Config

# 方式1: 直接在配置文件中配置
plugin_config = Config(
    super_admins=[1234567890]  # 替换为你的QQ号
)

# 方式2: 通过环境变量配置（推荐）
# 在.env文件中添加:
# NONEBOT_PLUGIN_BILI2MP4_SUPER_ADMINS=["1234567890"]

# 方式3: 在NoneBot配置中配置
# 在你的配置文件中添加:
# {
#     "super_admins": [1234567890]  # 替换为你的QQ号
# }

# 加载配置到驱动器
driver = get_driver()
driver.config.super_admins = SUPER_ADMINS
