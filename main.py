# -*- coding: utf-8 -*-
"""
FANZA PAYLOAD 捕获工具

功能：
1. 捕获单影片详情页的 GraphQL PAYLOAD (ContentPageData)
2. 捕获演员搜索页的 GraphQL PAYLOAD (AvSearch)
3. 支持自定义 offset 和 limit 参数
4. 自动处理年龄验证
5. 敏感配置通过环境变量管理
6. 完整日志记录到 LOGS/ 文件夹
"""

import json
import os
import time
import argparse
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from config import (
    TYPE_ID_URL,
    TYPE_ACTRESS_URL,
    GRAPHQL_API_URL,
    HEADER_KEY,
    HEADER_VALUE,
    TARGET_OPERATION_ID,
    TARGET_OPERATION_ACTRESS,
    MAX_RETRY,
    RETRY_INTERVAL,
    WAIT_GRAPHQL,
)

BASE_DIR = os.path.dirname(__file__)
PAYLOAD_DIR = os.path.join(BASE_DIR, "PAYLOAD")
LOGS_DIR = os.path.join(BASE_DIR, "LOGS")

os.makedirs(PAYLOAD_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


def setup_logger():
    """配置日志系统"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(LOGS_DIR, f"{timestamp}.log")

    logger = logging.getLogger("fanza_payload")
    logger.setLevel(logging.INFO)

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(file_format)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger, log_file


def _handle_age_check(page, logger):
    """
    处理年龄验证页面

    Args:
        page: Playwright page 对象
        logger: 日志对象

    Returns:
        bool: True 表示无需验证或验证成功，False 表示验证失败
    """
    if "age_check" in page.url or "年齢認証" in page.content():
        logger.info("检测到年龄验证页面")
        btn = page.locator('a[href*="declared=yes"]')
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            logger.info("年龄验证通过")
            return True
        else:
            logger.warning("未找到年龄验证按钮")
            return False
    logger.info("无需年龄验证")
    return True


def capture_video_payload(cid, logger):
    """
    捕获单影片详情页的 GraphQL PAYLOAD

    Args:
        cid: 影片CID
        logger: 日志对象

    Returns:
        dict: 包含 operationName、query、variables 的 PAYLOAD，失败返回 None
    """
    start_time = time.time()
    logger.info(f"捕获单影片 PAYLOAD: {cid}")

    payload_request = None

    for attempt in range(MAX_RETRY):
        logger.info(f"尝试 {attempt + 1}/{MAX_RETRY}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # 添加自定义请求头
                if HEADER_KEY and HEADER_VALUE:
                    page.set_extra_http_headers({HEADER_KEY: HEADER_VALUE})

                # 请求监听回调
                def handle_request(request):
                    nonlocal payload_request

                    if request.method != "POST":
                        return
                    if GRAPHQL_API_URL not in request.url:
                        return

                    post_data_str = request.post_data
                    if not post_data_str:
                        return

                    try:
                        post_data = json.loads(post_data_str)
                        operation = post_data.get("operationName")
                        variables = post_data.get("variables")

                        if operation == TARGET_OPERATION_ID and payload_request is None:
                            payload_request = {
                                "operationName": operation,
                                "query": post_data.get("query"),
                                "variables": variables
                            }
                            logger.info(f"捕获到 {TARGET_OPERATION_ID}")
                    except Exception:
                        pass

                page.on("request", handle_request)

                # 访问页面
                logger.info("访问页面...")
                page.goto(TYPE_ID_URL.format(cid=cid), wait_until="domcontentloaded")
                logger.info(f"页面标题: {page.title()}")

                # 处理年龄验证
                if not _handle_age_check(page, logger):
                    browser.close()
                    continue

                # 等待 GraphQL 请求
                logger.info(f"等待 GraphQL 请求（最多 {WAIT_GRAPHQL}s）...")
                request_start = time.time()
                while payload_request is None and (time.time() - request_start) < WAIT_GRAPHQL:
                    try:
                        page.evaluate("() => document.readyState")
                    except:
                        pass
                    time.sleep(0.5)

                if payload_request:
                    # 将 id 模板化
                    if isinstance(payload_request.get("variables"), dict) and "id" in payload_request["variables"]:
                        payload_request["variables"]["id"] = ""

                    output_file = os.path.join(PAYLOAD_DIR, "PAYLOAD_ID.json")
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(payload_request, f, indent=2, ensure_ascii=False)
                    logger.info(f"保存到: PAYLOAD_ID.json")

                    elapsed = time.time() - start_time
                    logger.info(f"捕获成功 (耗时: {elapsed:.1f}s)")
                    browser.close()
                    return payload_request

                logger.warning("超时，未捕获目标请求")
                browser.close()

        except Exception as e:
            logger.error(f"错误: {e}")

        if attempt < MAX_RETRY - 1:
            logger.info(f"{RETRY_INTERVAL}s 后重试...")
            time.sleep(RETRY_INTERVAL)

    elapsed = time.time() - start_time
    logger.error(f"捕获失败 (耗时: {elapsed:.1f}s)")
    return None


def capture_actress_payload(actress_id, offset, limit, logger):
    """
    捕获演员搜索页的 GraphQL PAYLOAD

    Args:
        actress_id: 演员ID
        offset: 偏移量
        limit: 每页数量
        logger: 日志对象

    Returns:
        dict: 包含 operationName、query、variables 的 PAYLOAD，失败返回 None
    """
    start_time = time.time()
    logger.info(f"捕获演员搜索页 PAYLOAD: {actress_id}")

    payload_request = None

    for attempt in range(MAX_RETRY):
        logger.info(f"尝试 {attempt + 1}/{MAX_RETRY}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # 添加自定义请求头
                if HEADER_KEY and HEADER_VALUE:
                    page.set_extra_http_headers({HEADER_KEY: HEADER_VALUE})

                # 请求监听回调
                def handle_request(request):
                    nonlocal payload_request

                    if request.method != "POST":
                        return
                    if GRAPHQL_API_URL not in request.url:
                        return

                    post_data_str = request.post_data
                    if not post_data_str:
                        return

                    try:
                        post_data = json.loads(post_data_str)
                        operation = post_data.get("operationName")
                        variables = post_data.get("variables")

                        if operation == TARGET_OPERATION_ACTRESS and payload_request is None:
                            payload_request = {
                                "operationName": operation,
                                "query": post_data.get("query"),
                                "variables": variables
                            }
                            logger.info(f"捕获到 {TARGET_OPERATION_ACTRESS}")
                    except Exception:
                        pass

                page.on("request", handle_request)

                # 访问页面
                logger.info("访问页面...")
                page.goto(TYPE_ACTRESS_URL.format(actress_id=actress_id), wait_until="domcontentloaded")
                logger.info(f"页面标题: {page.title()}")

                # 处理年龄验证
                if not _handle_age_check(page, logger):
                    browser.close()
                    continue

                # 等待 GraphQL 请求
                logger.info(f"等待 GraphQL 请求（最多 {WAIT_GRAPHQL}s）...")
                request_start = time.time()
                while payload_request is None and (time.time() - request_start) < WAIT_GRAPHQL:
                    try:
                        page.evaluate("() => document.readyState")
                    except:
                        pass
                    time.sleep(0.5)

                if payload_request:
                    # 处理 filter 中的 id
                    if isinstance(payload_request.get("variables"), dict):
                        payload_request["variables"]["offset"] = offset
                        payload_request["variables"]["limit"] = limit
                        filter_data = payload_request["variables"].get("filter", {})
                        if isinstance(filter_data, dict):
                            actress_ids = filter_data.get("actressIds", {})
                            if isinstance(actress_ids, dict) and "ids" in actress_ids:
                                for item in actress_ids["ids"]:
                                    if isinstance(item, dict) and "id" in item:
                                        item["id"] = ""

                    output_file = os.path.join(PAYLOAD_DIR, "PAYLOAD_ACTRESS.json")
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(payload_request, f, indent=2, ensure_ascii=False)
                    logger.info(f"保存到: PAYLOAD_ACTRESS.json")

                    elapsed = time.time() - start_time
                    logger.info(f"捕获成功 (耗时: {elapsed:.1f}s)")
                    browser.close()
                    return payload_request

                logger.warning("超时，未捕获目标请求")
                browser.close()

        except Exception as e:
            logger.error(f"错误: {e}")

        if attempt < MAX_RETRY - 1:
            logger.info(f"{RETRY_INTERVAL}s 后重试...")
            time.sleep(RETRY_INTERVAL)

    elapsed = time.time() - start_time
    logger.error(f"捕获失败 (耗时: {elapsed:.1f}s)")
    return None


def main():
    parser = argparse.ArgumentParser(description='FANZA GraphQL PAYLOAD 捕获工具')
    parser.add_argument('--cid', default='ipzz00780', help='影片 CID')
    parser.add_argument('--actress', default='1044099', help='演员 ID')
    parser.add_argument('--offset', type=int, default=0, help='演员搜索偏移量')
    parser.add_argument('--limit', type=int, default=120, help='演员搜索每页数量')
    args = parser.parse_args()

    # 初始化日志
    logger, log_file = setup_logger()
    start_time = time.time()

    logger.info("=" * 50)
    logger.info("FANZA PAYLOAD 捕获工具启动")
    logger.info("=" * 50)

    # 捕获单影片 PAYLOAD
    logger.info("[1/2] 捕获单影片 PAYLOAD...")
    result1 = capture_video_payload(args.cid, logger)

    # 捕获演员搜索页 PAYLOAD
    logger.info(f"[2/2] 捕获演员搜索页 PAYLOAD...")
    result2 = capture_actress_payload(args.actress, args.offset, args.limit, logger)

    # 完成
    logger.info("=" * 50)
    logger.info("执行完成")
    logger.info(f"日志文件: {log_file}")
    logger.info("=" * 50)

    return result1 is not None and result2 is not None


if __name__ == "__main__":
    main()
