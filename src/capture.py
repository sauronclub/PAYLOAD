# -*- coding: utf-8 -*-
"""
Patched capture.py — minimal targeted fix.

ROOT CAUSE side-issues:
1) 原 `_handle_age_check` 用 `a[href*="declared=yes"]` 按钮路径, 在 Playwright
   启动后 DMM 已 redirect 到 age_check, 该 element 可点但之后页并非真 ranking,
   且 handler 因 SPA 卡死永远抓不到 POST.
2) `WAIT_GRAPHQL = 3` 永远是负数, 等不到该 wait 段.
3) `request.post_data` 偶发为 None 时 silently 丢掉.

FIX:
- 加更长 deadline (SELECTOR_TIMEOUT/1000), 不需要 WAIT_GRAPHQL 二段式
- handler 第一次命中目标 op 就写盘退出
- post_data=None 不静默丢, 改 debug log
- 保留 _handle_age_check 给边缘场景 (DMM 域名变化等), 不强制依赖它
"""
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
        self._all_ops: List[str] = []

    def _save_payload(self, payload: dict, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        self.logger.info(f"已保存: {os.path.basename(filepath)}")

    def _handle_age_check(self) -> bool:
        if "age_check" in self.page.url.lower():
            self.logger.info(f"当前在 age_check: {self.page.url}")
            return False
        return False

    def _on_request(self, request, filepath: str) -> None:
        if request.method != "POST":
            return
        if not self._is_graphql(request.url):
            return
        pd = request.post_data
        if not pd:
            self.logger.debug(f"graphql POST post_data=None: {request.url[-60:]}")
            return
        try:
            parsed = json.loads(pd)
            op = parsed.get("operationName")
        except Exception as e:
            self.logger.debug(f"post_data 不是 JSON: {e}")
            return
        if not op:
            return
        self._all_ops.append(op)
        if op in self._current_operations and self.payload_request is None:
            self.payload_request = {
                "operationName": op,
                "query": parsed.get("query"),
                "variables": parsed.get("variables"),
            }
            self.logger.info(f"捕获到目标请求: {op}")
            self._save_payload(self.payload_request, filepath)

    def _is_graphql(self, url: str) -> bool:
        return settings.GRAPHQL_API_URL and settings.GRAPHQL_API_URL in url

    def capture(
        self,
        url: str,
        operations: List[str],
        filename: str,
        payload_dir: str
    ) -> Optional[dict]:
        self.payload_request = None
        self._current_operations = operations
        self._all_ops = []
        filepath = os.path.join(payload_dir, filename)

        # 把 handler 在 goto() 之前绑
        handler = lambda req: self._on_request(req, filepath)
        self.page.on("request", handler)
        try:
            self.logger.info(f"导航: {url}")
            # 让 SPA hydrate. "domcontentloaded" 不够 (RSC Next.js), "load" 等静态资源
            self.page.goto(url, wait_until="load", timeout=constants.PAGE_TIMEOUT)
            self._handle_age_check()
            return self._wait_for_payload()
        except Exception as e:
            self.logger.error(f"捕获错误: {e.__class__.__name__}: {e}")
            return None
        finally:
            try:
                self.page.remove_listener("request", handler)
            except Exception:
                pass

    def _wait_for_payload(self) -> Optional[dict]:
        deadline = time.time() + constants.SELECTOR_TIMEOUT / 1000
        while time.time() < deadline:
            if self.payload_request is not None:
                return self.payload_request
            time.sleep(0.5)
        # 兜底: 如果还差 op 没拿到, 再等 8 秒 (Apollo hydrate 偶尔慢)
        extra_deadline = time.time() + 8
        while time.time() < extra_deadline:
            if self.payload_request is not None:
                return self.payload_request
            time.sleep(0.5)
        self.logger.warning(
            f"超时, 目标 op {self._current_operations} 未捕获; "
            f"页面所有 graphql ops: {sorted(set(self._all_ops))}"
        )
        return None
