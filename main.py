# -*- coding: utf-8 -*-
"""
GraphQL Payload 捕获工具

模块化架构:
- src/config.py: 配置和常量管理
- src/logger.py: 日志模块
- src/browser.py: 浏览器生命周期管理
- src/capture.py: GraphQL Payload 捕获核心逻辑
- src/handlers.py: 页面处理和业务流程
"""
import os

from src import (
    settings,
    setup_logger,
    capture_all_ranking_payloads,
    cleanup_payload_files,
)


BASE_DIR = os.path.dirname(__file__)
PAYLOAD_DIR = os.path.join(BASE_DIR, "PAYLOAD")


def main():
    missing = settings.validate()
    if missing:
        raise EnvironmentError(f"缺少必要的环境变量: {', '.join(missing)}")

    cleanup_payload_files(PAYLOAD_DIR)

    logger = setup_logger()

    logger.info("=" * 60)
    logger.info("GraphQL Payload 捕获工具")
    logger.info("=" * 60)

    logger.info("开始捕获所有目标 payload...")
    results = capture_all_ranking_payloads(PAYLOAD_DIR)

    success = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"捕获完成: {success}/{total} 成功")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
