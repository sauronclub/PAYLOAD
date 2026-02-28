# -*- coding: utf-8 -*-
import json
import os
import time
from typing import Optional, Dict, List
from dataclasses import dataclass

from playwright.sync_api import Page

from .config import constants, settings
from .logger import setup_logger


@dataclass
class CaptureConfig:
    url: str
    operations: List[str]
    filename: str


class PayloadCapture:
    def __init__(self, page: Page):
        self.logger = setup_logger("capture")
        self.page = page
        self.payload_request: Optional[Dict] = None
        self._current_operations: List[str] = []

    def _replace_placeholders(self, payload: dict) -> dict:
        s = json.dumps(payload, ensure_ascii=False)
        s = s.replace(f'"{settings.cid}"', '""')
        s = s.replace(f'"{settings.actress_id}"', '""')
        return json.loads(s)

    def _save_payload(self, payload: dict, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        self.logger.info(f"已保存: {os.path.basename(filepath)}")

    def _handle_age_check(self) -> bool:
        if "age_check" in self.page.url.lower() or "年齢認証" in self.page.content():
            self.logger.info("检测到年龄验证页面")
            btn = self.page.locator('a[href*="declared=yes"]')
            if btn.count() > 0:
                btn.first.click()
                self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                self.logger.info("年龄验证通过 → reload 页面")
                self.page.reload(wait_until="domcontentloaded", timeout=constants.PAGE_TIMEOUT)
                return True
            self.logger.warning("未找到年龄验证按钮")
        return False

    def _create_request_handler(self, filepath: str):
        def handler(request):
            if request.method != "POST":
                return
            if settings.GRAPHQL_API_URL not in request.url:
                return
            if not request.post_data:
                return

            try:
                post_data = json.loads(request.post_data)
                op = post_data.get("operationName")

                if op in self._current_operations and self.payload_request is None:
                    self.payload_request = {
                        "operationName": op,
                        "query": post_data.get("query"),
                        "variables": post_data.get("variables")
                    }
                    self.logger.info(f"捕获到目标请求: {op}")
                    cleaned = self._replace_placeholders(self.payload_request)
                    self._save_payload(cleaned, filepath)
            except Exception as e:
                self.logger.debug(f"请求解析失败: {e}")

        return handler

    def capture(
        self,
        url: str,
        operations: List[str],
        filename: str,
        payload_dir: str
    ) -> Optional[dict]:
        self.payload_request = None
        self._current_operations = operations
        filepath = os.path.join(payload_dir, filename)

        handler = self._create_request_handler(filepath)
        self.page.on("request", handler)

        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=constants.PAGE_TIMEOUT)
            self.logger.info(f"导航完成: {url}")

            self._handle_age_check()

            return self._wait_for_payload(filepath)
        except Exception as e:
            self.logger.error(f"捕获错误: {e.__class__.__name__}: {e}")
            return None
        finally:
            self.page.remove_listener("request", handler)

    def _wait_for_payload(self, filepath: str) -> Optional[dict]:
        if self.payload_request:
            return self._replace_placeholders(self.payload_request)

        try:
            self.page.wait_for_selector(
                "h1, [class*='title'], [class*='name']",
                state="visible",
                timeout=constants.SELECTOR_TIMEOUT
            )
        except:
            self.logger.warning("标题元素未出现，使用 networkidle")
            try:
                self.page.wait_for_load_state("networkidle", timeout=constants.NETWORK_IDLE_TIMEOUT)
            except:
                pass

        time.sleep(3)

        if self.payload_request:
            return self._replace_placeholders(self.payload_request)

        start = time.time()
        while self.payload_request is None and (time.time() - start) < constants.WAIT_GRAPHQL:
            time.sleep(0.5)

        if self.payload_request:
            return self._replace_placeholders(self.payload_request)

        return None
