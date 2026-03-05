# -*- coding: utf-8 -*-
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright

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
        self.browser = self._playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport=constants.BROWSER_VIEWPORT,
            user_agent=constants.BROWSER_USER_AGENT
        )
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
        if settings.HEADER_KEY and settings.HEADER_VALUE:
            page.set_extra_http_headers({settings.HEADER_KEY: settings.HEADER_VALUE})
        return page

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
