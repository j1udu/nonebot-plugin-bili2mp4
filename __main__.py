from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import shutil
import subprocess
import time
import urllib.request
from typing import List, Optional, Set, Tuple
from urllib.parse import unquote, urlparse, parse_qs

from loguru import logger
from nonebot import on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    Event,
    GroupMessageEvent,
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.plugin import get_plugin_config

from .config import Config

# 可调的 ffmpeg 检测超时（秒），如遇到 Windows 首次运行较慢，可在启动前设置：
# PowerShell: $env:BILI2MP4_FFMPEG_TIMEOUT="30"
FFMPEG_CHECK_TIMEOUT = int(os.getenv("BILI2MP4_FFMPEG_TIMEOUT", "30"))

# 配置加载
plugin_config = get_plugin_config(Config)
super_admins: List[int] = plugin_config.super_admins or [3200825668]
logger.info(f"nonebot_plugin_bili2mp4 初始化：超管={super_admins}")

# 固定使用此目录中的 ffmpeg/ffprobe（请确保该路径存在并包含 ffmpeg.exe 与 ffprobe.exe）
HARD_CODED_FFMPEG_DIR = r"C:\Users\Administrator\Desktop\nonebot\yousa\.venv\ffmpeg\bin"
FFMPEG_DIR: Optional[str] = None


def _ffmpeg_works() -> bool:
    try:
        p = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=FFMPEG_CHECK_TIMEOUT,
        )
        return p.returncode == 0
    except Exception:
        return False


def _safe_cmd_version(cmd: list[str]) -> str:
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=FFMPEG_CHECK_TIMEOUT,
        )
        head = (p.stdout or b"").decode(errors="ignore").splitlines()
        return head[0] if head else ""
    except Exception as e:
        return f"{cmd[0]} 执行失败: {e}"


def _setup_ffmpeg_fixed() -> None:
    """
    强制使用硬编码目录中的 ffmpeg/ffprobe。
    """
    global FFMPEG_DIR

    dirpath = HARD_CODED_FFMPEG_DIR
    if not dirpath or not os.path.isdir(dirpath):
        logger.error(
            f"[ffmpeg] 硬编码目录不存在：{dirpath}\n"
            "请确认路径正确，且该目录中包含 ffmpeg.exe 与 ffprobe.exe。"
        )
        return

    # 预置到 PATH，便于子进程查找
    os.environ["PATH"] = dirpath + os.pathsep + os.environ.get("PATH", "")
    ff = shutil.which("ffmpeg")
    fp = shutil.which("ffprobe")

    if not ff:
        # 直接按目录拼路径再试一遍
        ff_candidate = os.path.join(dirpath, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.isfile(ff_candidate):
            ff = ff_candidate
        else:
            logger.error(
                f"[ffmpeg] 在硬编码目录中未找到 ffmpeg 可执行文件：{dirpath}\n"
                "请将 ffmpeg.exe 放入该目录。"
            )
            return

    if not fp:
        fp_candidate = os.path.join(dirpath, "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.isfile(fp_candidate):
            fp = fp_candidate
        else:
            logger.warning(f"[ffmpeg] 在目录中未找到 ffprobe，可导致功能受限：{dirpath}")

    FFMPEG_DIR = os.path.dirname(ff)
    logger.info(f"[ffmpeg] 使用硬编码目录：ffmpeg={ff}；ffprobe={fp or '未找到'}")
    logger.info(_safe_cmd_version(["ffmpeg", "-version"]))


_setup_ffmpeg_fixed()

# 数据目录与持久化
PLUGIN_NAME = "nonebot_plugin_bili2mp4"


def _get_data_dir() -> str:
    try:
        from nonebot_plugin_localstore import get_plugin_data_dir  # type: ignore

        path = str(get_plugin_data_dir())
        os.makedirs(path, exist_ok=True)
        logger.debug(f"使用 nonebot-plugin-localstore 数据目录: {path}")
        return path
    except Exception:
        base = os.path.join(os.getcwd(), "data", PLUGIN_NAME)
        os.makedirs(base, exist_ok=True)
        logger.debug(f"使用回退数据目录: {base}")
        return base


DATA_DIR = _get_data_dir()
STATE_PATH = os.path.join(DATA_DIR, "state.json")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "downloads")
COOKIE_FILE_PATH = os.path.join(DATA_DIR, "bili_cookies.txt")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 全局状态
enabled_groups: Set[int] = set()
bilibili_cookie: str = ""
max_height: int = 0           # 0 表示不限制（示例：720/1080/2160）
max_filesize_mb: int = 0      # 0 表示不限制
# 简单去重：正在处理中的 key = f"{group_id}|{url}"
_processing: Set[str] = set()


def _save_state() -> None:
    try:
        data = {
            "enabled_groups": sorted(list(enabled_groups)),
            "bilibili_cookie": bilibili_cookie or "",
            "max_height": int(max_height),
            "max_filesize_mb": int(max_filesize_mb),
        }
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"状态已保存: {STATE_PATH}")
    except Exception as e:
        logger.error(f"保存状态失败: {e}")


def _load_state() -> None:
    global enabled_groups, bilibili_cookie, max_height, max_filesize_mb
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            enabled_groups = {int(g) for g in data.get("enabled_groups", [])}
            bilibili_cookie = str(data.get("bilibili_cookie", "") or "")
            max_height = int(data.get("max_height", 0) or 0)
            max_filesize_mb = int(data.get("max_filesize_mb", 0) or 0)
            logger.info(
                f"已加载状态: 启用群数={len(enabled_groups)}，Cookie={bool(bilibili_cookie)}，"
                f"清晰度<= {max_height or '不限'}，大小<= {str(max_filesize_mb)+'MB' if max_filesize_mb else '不限'}"
            )
            return
        except Exception as e:
            logger.warning(f"读取状态失败，使用默认空状态: {e}")
    enabled_groups = set()
    bilibili_cookie = ""
    max_height = 0
    max_filesize_mb = 0
    _save_state()


_load_state()

# 更宽松的域名匹配（含 m.bilibili.com、t.bilibili.com 等）
BILI_URL_RE = re.compile(
    r"(https?://(?:[\w-]+\.)?(?:bilibili\.com|b23\.tv)/[^\s\"'<>]+)",
    flags=re.IGNORECASE,
)


def _find_urls_in_text(text: str) -> List[str]:
    urls = []
    for m in BILI_URL_RE.findall(text or ""):
        if m not in urls:
            urls.append(m)
    # 兼容 schema 中的 url 参数
    try:
        parsed = urlparse(text)
        if parsed and parsed.query:
            qs = parse_qs(parsed.query)
            for key in ("url", "qqdocurl", "jumpUrl", "webpageUrl"):
                for v in qs.get(key, []):
                    v = unquote(v)
                    for u in BILI_URL_RE.findall(v):
                        if u not in urls:
                            urls.append(u)
    except Exception:
        pass
    return urls


def _walk_strings(obj) -> List[str]:
    out: List[str] = []
    try:
        if isinstance(obj, dict):
            for v in obj.values():
                out.extend(_walk_strings(v))
        elif isinstance(obj, list):
            for it in obj:
                out.extend(_walk_strings(it))
        elif isinstance(obj, str):
            out.append(obj)
    except Exception:
        pass
    return out


def _extract_bili_urls_from_event(event: GroupMessageEvent) -> List[str]:
    urls: List[str] = []
    try:
        for seg in event.message:
            # 1) 纯文本
            if seg.type == "text":
                txt = seg.data.get("text", "")
                for u in _find_urls_in_text(txt):
                    if u not in urls:
                        urls.append(u)
            # 2) JSON 卡片
            elif seg.type == "json":
                raw = seg.data.get("data") or seg.data.get("content") or ""
                for u in _find_urls_in_text(raw):
                    if u not in urls:
                        urls.append(u)
                try:
                    obj = json.loads(raw)
                    for s in _walk_strings(obj):
                        for u in _find_urls_in_text(s):
                            if u not in urls:
                                urls.append(u)
                except Exception:
                    pass
            # 3) XML 卡片
            elif seg.type == "xml":
                raw = seg.data.get("data") or seg.data.get("content") or ""
                for u in _find_urls_in_text(raw):
                    if u not in urls:
                        urls.append(u)
            # 4) 分享卡片
            elif seg.type == "share":
                u = seg.data.get("url") or ""
                for u2 in _find_urls_in_text(u):
                    if u2 not in urls:
                        urls.append(u2)
            else:
                s = str(seg)
                for u in _find_urls_in_text(s):
                    if u not in urls:
                        urls.append(u)
    except Exception as e:
        logger.debug(f"提取链接异常: {e}")
    return urls


# 群消息监听（只在启用群里生效）
group_listener = on_message(priority=100, block=False)


@group_listener.handle()
async def handle_group(bot: Bot, event: Event):
    if not isinstance(event, GroupMessageEvent):
        return

    group_id = int(event.group_id)
    if group_id not in enabled_groups:
        return  # 未开启转换的群聊里保持静默

    urls = _extract_bili_urls_from_event(event)
    if not urls:
        logger.debug(f"[bili2mp4] 群{group_id} 未在该消息中发现B站链接")
        return

    url = urls[0]
    key = f"{group_id}|{url}"
    if key in _processing:
        logger.debug(f"[bili2mp4] 已在处理中，忽略重复: {key}")
        return
    _processing.add(key)
    logger.info(f"[bili2mp4] 群{group_id} 检测到B站链接：{url}")

    async def work():
        try:
            await _download_and_send(bot, group_id, url)
        except Exception as e:
            # 失败时静默（仅日志）
            logger.error(f"[bili2mp4] 处理失败（静默）：{e}")
        finally:
            _processing.discard(key)

    asyncio.create_task(work())


# 私聊控制（超级管理员）
ctrl_listener = on_message(priority=50, block=False)

CMD_ENABLE_RE = re.compile(r"^转换(\d+)$")
CMD_DISABLE_RE = re.compile(r"^停止转换(\d+)$")
CMD_SET_COOKIE_RE = re.compile(r"^设置B站COOKIE\s+(.+)$", flags=re.S)
CMD_CLEAR_COOKIE = {"清除B站COOKIE", "删除B站COOKIE"}
CMD_LIST = {"查看转换列表", "查看列表"}
CMD_SHOW_PARAMS = {"查看参数", "状态"}
CMD_SET_HEIGHT_RE = re.compile(r"^设置清晰度\s*(\d+)\s*p?$", flags=re.I)
CMD_SET_MAXSIZE_RE = re.compile(r"^设置最大大小\s*(\d+)\s*(?:mb|m)?$", flags=re.I)


@ctrl_listener.handle()
async def handle_private(bot: Bot, event: Event):
    if not isinstance(event, PrivateMessageEvent):
        return

    try:
        uid = int(event.user_id)
    except Exception:
        return
    if uid not in super_admins:
        return

    global bilibili_cookie, max_height, max_filesize_mb

    text = event.get_plaintext().strip()

    # 管理员帮助
    if text.lower() == "fhelp":
        help_msg = (
            "管理员指令：\n"
            "• fhelp\n"
            "  返回本帮助列表\n"
            "• 转换<群号>\n"
            "  在指定群开启 B 站视频自动转换。例如：转换123456\n"
            "• 停止转换<群号>\n"
            "  在指定群关闭自动转换。例如：停止转换123456\n"
            "• 设置B站COOKIE <cookie内容>\n"
            "  设置下载用的 B 站 Cookie，例如：设置B站COOKIE SESSDATA=...; bili_jct=...; buvid3=...\n"
            "• 清除B站COOKIE / 删除B站COOKIE\n"
            "  清除已设置的 Cookie\n"
            "• 设置清晰度 <数字> 或 <数字>p\n"
            "  限制最大分辨率（高度），0 表示不限制。例如：设置清晰度 720 或 1080p\n"
            "• 设置最大大小 <数字> 或 <数字>MB/m\n"
            "  限制最终视频大小（MB），0 表示不限制。例如：设置最大大小 45MB\n"
            "• 查看转换列表 / 查看列表\n"
            "  查看当前已开启自动转换的群\n"
            "• 查看参数 / 状态\n"
            "  查看当前参数（清晰度、大小上限、Cookie 是否设置、启用群数量）"
        )
        await bot.send(event, Message(help_msg))
        return

    # 开启群
    m = CMD_ENABLE_RE.fullmatch(text)
    if m:
        gid = int(m.group(1))
        enabled_groups.add(gid)
        _save_state()
        await bot.send(event, Message(f"✅ 已开启群 {gid} 的B站视频转换"))
        return

    # 关闭群
    m = CMD_DISABLE_RE.fullmatch(text)
    if m:
        gid = int(m.group(1))
        if gid in enabled_groups:
            enabled_groups.discard(gid)
            _save_state()
            await bot.send(event, Message(f"🛑 已停止群 {gid} 的B站视频转换"))
        else:
            await bot.send(event, Message(f"ℹ️ 群 {gid} 未开启转换"))
        return

    # 设置Cookie
    m = CMD_SET_COOKIE_RE.fullmatch(text)
    if m:
        bilibili_cookie = m.group(1).strip()
        _save_state()
        await bot.send(event, Message("✅ 已设置B站 Cookie"))
        return

    # 清除Cookie
    if text in CMD_CLEAR_COOKIE:
        bilibili_cookie = ""
        _save_state()
        await bot.send(event, Message("🧹 已清除B站 Cookie"))
        return

    # 设置清晰度（高度）
    m = CMD_SET_HEIGHT_RE.fullmatch(text)
    if m:
        h = int(m.group(1))
        if h < 0:
            h = 0
        max_height = h
        _save_state()
        await bot.send(event, Message(f"⏱ 清晰度已设置为 {'不限制' if h == 0 else f'<= {h}p'}"))
        return

    # 设置最大大小（MB）
    m = CMD_SET_MAXSIZE_RE.fullmatch(text)
    if m:
        lim = int(m.group(1))
        if lim < 0:
            lim = 0
        max_filesize_mb = lim
        _save_state()
        await bot.send(event, Message(f"📦 文件大小限制为 {'不限制' if lim == 0 else f'<= {lim}MB'}"))
        return

    # 查看列表
    if text in CMD_LIST:
        if enabled_groups:
            sorted_g = sorted(list(enabled_groups))
            await bot.send(event, Message("当前已开启转换的群：" + ", ".join(map(str, sorted_g))))
        else:
            await bot.send(event, Message("暂无开启转换的群"))
        return

    # 查看参数
    if text in CMD_SHOW_PARAMS:
        await bot.send(
            event,
            Message(
                f"参数：清晰度<= {max_height or '不限'}；大小<= {str(max_filesize_mb)+'MB' if max_filesize_mb else '不限'}；"
                f"Cookie={'已设置' if bool(bilibili_cookie) else '未设置'}；启用群数={len(enabled_groups)}"
            ),
        )
        return

    # 未匹配其他命令
    return


def _build_browser_like_headers() -> dict:
    # 避免 412：使用常见浏览器头，并固定 Referer
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.bilibili.com/",
        "Origin": "https://www.bilibili.com",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }


def _expand_short_url(u: str, timeout: float = 8.0) -> str:
    try:
        host = urlparse(u).hostname or ""
        if host.lower() not in {"b23.tv", "www.b23.tv"}:
            return u
        # 优先 HEAD，失败再 GET
        hdrs = {
            "User-Agent": _build_browser_like_headers()["User-Agent"],
            "Referer": "https://www.bilibili.com/",
        }
        try:
            req = urllib.request.Request(u, headers=hdrs, method="HEAD")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                final = resp.geturl()
                return final or u
        except Exception:
            req = urllib.request.Request(u, headers=hdrs, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                final = resp.geturl()
                return final or u
    except Exception as e:
        logger.debug(f"短链展开失败，使用原链接（{u}）：{e}")
        return u


def _ensure_cookiefile(cookie_string: str) -> Optional[str]:
    """
    将形如 'SESSDATA=...; bili_jct=...; buvid3=...' 的 Cookie 字符串
    转为 Netscape Cookie File 写入 COOKIE_FILE_PATH，供 yt-dlp 使用。
    """
    cookie_string = (cookie_string or "").strip().strip(";")
    if not cookie_string:
        # 清除旧文件避免误用
        try:
            if os.path.exists(COOKIE_FILE_PATH):
                os.remove(COOKIE_FILE_PATH)
        except Exception:
            pass
        return None

    # 解析键值
    pairs: list[tuple[str, str]] = []
    for part in cookie_string.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k and v:
            pairs.append((k, v))
    if not pairs:
        return None

    # 生成 Netscape 格式
    expiry = int(time.time()) + 180 * 24 * 3600  # 180 天
    lines = [
        "# Netscape HTTP Cookie File",
        "# This file was generated by nonebot_plugin_bili2mp4",
        "",
    ]
    for k, v in pairs:
        # domain include_subdomains path secure expiry name value
        line = f".bilibili.com\tTRUE\t/\tFALSE\t{expiry}\t{k}\t{v}"
        lines.append(line)

    try:
        with open(COOKIE_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return COOKIE_FILE_PATH
    except Exception as e:
        logger.warning(f"写入 Cookie 文件失败，回退到无 Cookie：{e}")
        return None


async def _download_and_send(bot: Bot, group_id: int, url: str) -> None:
    # 执行下载（阻塞IO放后台线程）
    try:
        path, title = await asyncio.to_thread(
            _download_with_ytdlp, url, bilibili_cookie, DOWNLOAD_DIR, max_height, max_filesize_mb
        )
    except ImportError as e:
        logger.error(f"缺少 yt_dlp 依赖：{e}")
        return  # 静默
    except RuntimeError as e:
        logger.warning(f"下载失败（RuntimeError，静默）：{e}")
        return  # 静默
    except Exception as e:
        logger.error(f"下载异常（静默）：{e}")
        return  # 静默

    # 文件大小检查（下载后）
    try:
        if max_filesize_mb and os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb > max_filesize_mb:
                logger.info(f"视频大小超限：{size_mb:.1f}MB > {max_filesize_mb}MB，取消发送（静默）。")
                try:
                    os.remove(path)
                except Exception:
                    pass
                return
    except Exception as e:
        logger.debug(f"大小检查异常: {e}")

    # 发送视频（若失败保持静默，只记录日志）
    try:
        await bot.send_group_msg(
            group_id=group_id,
            message=MessageSegment.video(file=path) + Message(f"\n{title or 'B站视频'}"),
        )
    except Exception as e:
        logger.error(f"发送视频失败（静默）：{e}")
    finally:
        # 清理文件以节省空间
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _build_format_candidates(height_limit: int, size_limit_mb: int) -> List[str]:
    h = height_limit if height_limit and height_limit > 0 else None
    size = size_limit_mb if size_limit_mb and size_limit_mb > 0 else None

    def h_filter():
        return f"[height<={h}]" if h else ""

    def s_filter():
        return f"[filesize<={size}M]" if size else ""

    # 优先 avc/h264，提高兼容性；再退而求其次
    v1 = f"bv*{h_filter()}{s_filter()}[vcodec^=avc]+ba/best{h_filter()}{s_filter()}[vcodec^=avc]/best{h_filter()}{s_filter()}"
    v2 = f"bv*{h_filter()}{s_filter()}+ba/best{h_filter()}{s_filter()}"
    v3 = f"bv*+ba/best"
    return [v1, v2, v3]


def _download_with_ytdlp(
    url: str, cookie: str, out_dir: str, height_limit: int, size_limit_mb: int
) -> Tuple[str, str]:
    try:
        from yt_dlp import YoutubeDL  # type: ignore
        from yt_dlp.utils import DownloadError  # type: ignore
    except Exception:
        raise ImportError("yt_dlp not installed")

    # 展开 b23 短链，确保首个请求命中 bilibili.com 域（Cookie 生效）
    final_url = _expand_short_url(url)

    # 生成 Cookie 文件（若配置了 Cookie）
    cookiefile = _ensure_cookiefile(cookie)

    # 逐个尝试不同的格式表达式（从最严格到最宽松）
    candidates = _build_format_candidates(height_limit, size_limit_mb)
    last_err: Optional[Exception] = None

    for fmt in candidates:
        headers = _build_browser_like_headers()
        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(out_dir, "%(title).80s [%(id)s].%(ext)s"),
            "noplaylist": True,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "http_headers": headers,
            # 更换客户端有助于过检；失败可回退为 web
            "extractor_args": {
                "bili": {
                    "player_client": ["android"],  # 可按需改为 ["android","web"] 轮询
                    "lang": ["zh-CN"],
                }
            },
        }
        # 告诉 yt-dlp ffmpeg 在哪里（如果可用）
        if FFMPEG_DIR:
            ydl_opts["ffmpeg_location"] = FFMPEG_DIR
        # 使用 cookiefile 注入 Cookie，避免通过 Header 传 Cookie 的弃用警告和域不匹配
        if cookiefile:
            ydl_opts["cookiefile"] = cookiefile

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(final_url, download=True)
                title = info.get("title") or "B站视频"
                final_path = _locate_final_file(ydl, info)
                if not final_path or not os.path.exists(final_path):
                    raise RuntimeError("未找到已下载的视频文件，可能未安装 ffmpeg")
                return final_path, title
        except DownloadError as e:
            last_err = e
            logger.debug(f"尝试格式失败（{fmt}）：{e}")
            continue
        except Exception as e:
            last_err = e
            logger.debug(f"下载异常（{fmt}）：{e}")
            continue

    if last_err:
        raise RuntimeError(str(last_err))
    raise RuntimeError("无法下载该视频")


def _locate_final_file(ydl, info) -> Optional[str]:
    # 优先从下载项中取
    for key in ("requested_downloads", "requested_formats"):
        arr = info.get(key)
        if isinstance(arr, list):
            for it in arr:
                fp = it.get("filepath")
                if fp and os.path.exists(fp):
                    return fp
    # 兼容字段
    for key in ("filepath", "_filename"):
        fp = info.get(key)
        if fp and os.path.exists(fp):
            return fp
    # 预测合并后 mp4
    base = ydl.prepare_filename(info)
    root, _ = os.path.splitext(base)
    candidate = root + ".mp4"
    if os.path.exists(candidate):
        return candidate
    # 兜底：按视频ID在目录中搜
    vid = info.get("id") or ""
    if vid:
        dirpath = os.path.dirname(base) or os.getcwd()
        try:
            files = [os.path.join(dirpath, f) for f in os.listdir(dirpath) if vid in f]
            if files:
                files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                return files[0]
        except Exception:
            pass
    return None