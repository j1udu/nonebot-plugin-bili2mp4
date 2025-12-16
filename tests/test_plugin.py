import pytest
from nonebot import get_plugin_config
from nonebot.test import MockBot, MockMessageEvent

from nonebot_plugin_bili2mp4 import __plugin_meta__
from nonebot_plugin_bili2mp4.config import Config


def test_plugin_meta():
    """测试插件元数据是否正确加载"""
    assert __plugin_meta__ is not None
    assert __plugin_meta__.name == "nonebot_plugin_bili2mp4"
    assert __plugin_meta__.type == "application"
    assert "~onebot.v11" in __plugin_meta__.supported_adapters


def test_plugin_config():
    """测试插件配置是否正确加载"""
    config = get_plugin_config(Config)
    assert hasattr(config, "super_admins")
    assert isinstance(config.super_admins, list)
    assert all(isinstance(admin_id, int) for admin_id in config.super_admins)


@pytest.mark.asyncio
async def test_plugin_load():
    """测试插件是否能正确加载"""
    from nonebot import load_plugin

    plugin = load_plugin("nonebot_plugin_bili2mp4")
    assert plugin is not None
    assert plugin.name == "nonebot_plugin_bili2mp4"
    assert plugin.metadata is __plugin_meta__


@pytest.mark.asyncio
async def test_url_extraction():
    """测试B站链接提取功能"""
    from nonebot_plugin_bili2mp4.__main__ import (
        _extract_bili_urls_from_event,
        _find_urls_in_text,
    )

    # 测试文本中的链接提取
    text = "这是一个测试 https://www.bilibili.com/video/BV1234567890 还有一些文本"
    urls = _find_urls_in_text(text)
    assert len(urls) == 1
    assert "www.bilibili.com/video/BV1234567890" in urls[0]

    # 测试事件中的链接提取
    bot = MockBot()
    event = MockMessageEvent(message=f"分享视频: {text}", user_id=12345, self_id=67890)

    bili_urls = await _extract_bili_urls_from_event(bot, event)
    assert len(bili_urls) > 0
    assert any("bilibili.com" in url for url in bili_urls)
