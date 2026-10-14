# -*- coding: utf-8 -*-
"""
Patched browser.py — minimal targeted fix.

ROOT CAUSE:
  Original code did `page.set_extra_http_headers({X-Forwarded-For: ...})` on
  every page. That sets XFF on ALL requests the page issues, including
  fetch() / XHR POSTs to https://api.video.dmm.co.jp/graphql.

  DMM's CORS policy for that endpoint does NOT include `x-forwarded-for`
  in `Access-Control-Allow-Headers`. So the browser rejects every graphql
  POST at preflight (OPTIONS), and Playwright's `on("response")` never
  fires. SPA hydration stalls, no ContentRankingPage fires, handler
  captures nothing except the unrelated LegacyGuestId / Root / Maintenance
  calls that go through Apollo's slightly different code path.

FIX:
  Use `context.route(..., handler)` to inject XFF only on non-graphql
  requests. This bypasses the CORS rejection while still using XFF to
  get past DMM's regional gate on the *page* navigation.

  We drop `set_extra_http_headers(...)` entirely.

Patched from upstream sauronclub/PAYLOAD @ 51c29ff.
"""
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright
import urllib.parse

from .config import constants, settings
from .logger import setup_logger


class BrowserManager:
    def __init__(self, headless: bool = True):
        self.logger = setup_logger("browser")
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def start(self) -> None:
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        self.context = self.browser.new_context(
            viewport=constants.BROWSER_VIEWPORT,
            user_agent=constants.BROWSER_USER_AGENT,
        )

        # 关键修复: 用 route() 拦截, 只在非 graphql 请求上加 XFF
        # graphql fetch 必须没有 XFF 才能过 CORS 预检
        xff_value = settings.HEADER_VALUE if settings.HEADER_KEY.lower() == "x-forwarded-for" else None
        if xff_value:
            def route_handler(route):
                if "graphql" in route.request.url:
                    route.continue_()
                else:
                    headers = dict(route.request.headers)
                    headers["x-forwarded-for"] = xff_value
                    route.continue_(headers=headers)
            self.context.route("**/*", route_handler)
            self.logger.info("XFF 已挂到 route (graphql 跳过)")
        self.logger.info("浏览器已启动")

    def close(self) -> None:
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        self.logger.info("浏览器已关闭")

    def new_page(self) -> Page:
        page = self.context.new_page()
        return page

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
