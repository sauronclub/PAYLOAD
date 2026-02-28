# -*- coding: utf-8 -*-
"""
PAYLOAD 捕获工具

模块化架构:
- src/config.py: 配置和常量管理
- src/logger.py: 日志模块
- src/browser.py: 浏览器生命周期管理
- src/capture.py: GraphQL Payload 捕获核心逻辑
- src/handlers.py: 页面处理和业务流程
"""
import os
import argparse

from src import (
    settings,
    setup_logger,
    capture_all_ranking_payloads,
    cleanup_payload_files,
)


BASE_DIR = os.path.dirname(__file__)
PAYLOAD_DIR = os.path.join(BASE_DIR, "PAYLOAD")


def main():
    parser = argparse.ArgumentParser(description="FANZA GraphQL Payload 捕获工具")
    parser.add_argument("--cid", default=settings.cid, help="影片 CID")
    parser.add_argument("--actress", default=settings.actress_id, help="演员 ID")
    parser.add_argument("--offset", type=int, default=0, help="演员搜索偏移量")
    parser.add_argument("--limit", type=int, default=120, help="演员搜索每页数量")
    parser.add_argument("--ranking", action="store_true", help="仅捕获排行榜类 payload")
    args = parser.parse_args()

    missing = settings.validate()
    if missing:
        raise EnvironmentError(f"缺少必要的环境变量: {', '.join(missing)}")

    cleanup_payload_files(PAYLOAD_DIR)

    logger = setup_logger()

    logger.info("=" * 60)
    logger.info("GraphQL Payload 捕获工具")
    logger.info(f"使用 CID: {args.cid} | Actress ID: {args.actress}")
    logger.info("=" * 60)

    logger.info("开始捕获所有目标 payload...")
    results = capture_all_ranking_payloads(PAYLOAD_DIR)

    success = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"捕获完成: {success}/{total} 成功")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
