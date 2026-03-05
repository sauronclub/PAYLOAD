# -*- coding: utf-8 -*-
import os
import time
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
    ]


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
                payload_dir=payload_dir
            )

            if result:
                return True

        except Exception as e:
            logger.error(f"捕获过程错误: {e}")
        finally:
            page.close()

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
