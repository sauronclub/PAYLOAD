# -*- coding: utf-8 -*-
"""
Patched handlers.py — minimal targeted fix.

ROOT CAUSE:
原代码假设只要 goto ranking URL 时 age_check 按钮会自动出现并被 _handle_age_check
点掉. 但实际:
1) Playwright 启动后首次 goto ranking 时,DMM 立即 redirect 到 age_check 页面
   (不是渲染了 ranking 才报按钮), 所以 _handle_age_check 实际是在 age_check 页面
   上 click 该按钮, 但 click 后页面再次被 redirect, 因为 age_check cookie 还没种上
   (还没真访问过 /declared=yes).
2) 就算 click 成功, SPA 在拿到 age cookie 后才会 hydrate, 而 handler 没在 goto 之前
   绑 request 监听 — 这条 capture.py 已经修了.

FIX:
- capture_with_retry 开始前, 先在 browser_manager.context 上访问一次
  /age_check/=/declared=yes/?rurl=... (浏览器真实 fetch 一次), 种 cookie.
  之后所有该 context 的新 page 默认带 cookie.
- 保留 3 次 retry, 因为页面 redirect 偶尔有 race.
"""
import os
import time
import urllib.parse
from typing import Dict, List

from .config import constants, settings
from .logger import setup_logger
from .browser import BrowserManager
from .capture import PayloadCapture, CaptureConfig


def get_capture_configs() -> List[CaptureConfig]:
    return [
        CaptureConfig(
            url=settings.TYPE_ID_URL,
            operations=[constants.TARGET_OPERATIONNAME_ID],
            filename="PAYLOAD_ID.json"
        ),
        CaptureConfig(
            url=settings.TYPE_ACTRESS_URL,
            operations=[constants.TARGET_OPERATIONNAME_ACTRESS],
            filename="PAYLOAD_ACTRESS.json"
        ),
        CaptureConfig(
            url=settings.TYPE_REALTIME_URL,
            operations=[constants.TARGET_OPERATIONNAME_REALTIME],
            filename="PAYLOAD_REALTIME.json"
        ),
        CaptureConfig(
            url=settings.TYPE_REALTIME_VR_URL,
            operations=[constants.TARGET_OPERATIONNAME_REALTIME_VR],
            filename="PAYLOAD_REALTIME_VR.json"
        ),
        CaptureConfig(
            url=settings.TYPE_DATE_URL,
            operations=[constants.TARGET_OPERATIONNAME_DATE],
            filename="PAYLOAD_DATE.json"
        ),
        CaptureConfig(
            url=settings.TYPE_DAILY_URL,
            operations=[constants.TARGET_OPERATIONNAME_DAILY],
            filename="PAYLOAD_DAILY.json"
        ),
        CaptureConfig(
            url=settings.TYPE_WEEKLY_URL,
            operations=[constants.TARGET_OPERATIONNAME_WEEKLY],
            filename="PAYLOAD_WEEKLY.json"
        ),
        CaptureConfig(
            url=settings.TYPE_MONTHLY_URL,
            operations=[constants.TARGET_OPERATIONNAME_MONTHLY],
            filename="PAYLOAD_MONTHLY.json"
        ),
        CaptureConfig(
            url=settings.TYPE_MONTHLY_ACTRESS_URL,
            operations=[constants.TARGET_OPERATIONNAME_MONTHLY_ACTRESS],
            filename="PAYLOAD_MONTHLY_ACTRESS.json"
        ),
        CaptureConfig(
            url=settings.TYPE_MONTHLY_SERIES_URL,
            operations=[constants.TARGET_OPERATIONNAME_MONTHLY_SERIES],
            filename="PAYLOAD_MONTHLY_SERIES.json"
        ),
        CaptureConfig(
            url=settings.TYPE_LATEST_RELEASE_URL,
            operations=[constants.TARGET_OPERATIONNAME_LATEST_RELEASE],
            filename="PAYLOAD_LATEST_RELEASE.json"
        ),
    ]


def _prime_age_check_in_context(browser_manager: BrowserManager, target_url: str) -> None:
    """在 BrowserManager context 内部访问一次 /age_check/=/declared=yes/?rurl=<target>.
    之后 context 内的所有 page 默认带 age_check_done cookie."""
    log = setup_logger("handlers")
    rurl = urllib.parse.quote(target_url, safe="")
    age_url = f"https://www.dmm.co.jp/age_check/=/declared=yes/?rurl={rurl}"
    log.info(f"预热 age_check: {age_url}")
    page = browser_manager.new_page()
    try:
        page.goto(age_url, wait_until="domcontentloaded", timeout=constants.PAGE_TIMEOUT)
        time.sleep(1.5)
        cookies = [c["name"] for c in browser_manager.context.cookies()]
        log.info(f"pre-prime done, cookies in context: {cookies}")
    finally:
        page.close()


def capture_with_retry(
    browser_manager: BrowserManager,
    config: CaptureConfig,
    payload_dir: str,
    logger
) -> bool:
    for attempt in range(constants.MAX_RETRY):
        logger.info(f"尝试 {attempt + 1}/{constants.MAX_RETRY} - {config.filename}")
        page = browser_manager.new_page()
        capturer = PayloadCapture(page)
        try:
            result = capturer.capture(
                url=config.url,
                operations=config.operations,
                filename=config.filename,
                payload_dir=payload_dir,
            )
            if result:
                return True
        except Exception as e:
            logger.error(f"捕获过程错误: {e}")
        finally:
            try:
                page.close()
            except Exception:
                pass

        if attempt < constants.MAX_RETRY - 1:
            logger.info(f"{constants.RETRY_INTERVAL} 秒后重试...")
            time.sleep(constants.RETRY_INTERVAL)

    logger.error(f"捕获 {config.filename} 失败")
    return False


def capture_all_ranking_payloads(payload_dir: str) -> Dict[str, bool]:
    logger = setup_logger("handlers")
    configs = get_capture_configs()
    results = {}

    with BrowserManager() as browser_manager:
        # 预热 age_check cookie (用第一个目标 URL 即可, cookie 在 context 共享)
        _prime_age_check_in_context(browser_manager, configs[0].url)

        for i, config in enumerate(configs, 1):
            logger.info(f"[{i}/{len(configs)}] 正在捕获 {config.filename}")
            success = capture_with_retry(browser_manager, config, payload_dir, logger)
            results[config.filename] = success

    return results


def cleanup_payload_files(payload_dir: str) -> None:
    if not os.path.exists(payload_dir):
        return
    for f in os.listdir(payload_dir):
        if f.startswith("PAYLOAD_") and f.endswith(".json"):
            os.remove(os.path.join(payload_dir, f))
