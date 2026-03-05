# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass, field
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    TYPE_ID_URL: str = ""
    TYPE_ACTRESS_URL: str = ""
    TYPE_REALTIME_URL: str = ""
    TYPE_REALTIME_VR_URL: str = ""
    TYPE_WEEKLY_URL: str = ""
    TYPE_DATE_URL: str = ""
    TYPE_DAILY_URL: str = ""
    TYPE_MONTHLY_URL: str = ""
    TYPE_MONTHLY_ACTRESS_URL: str = ""
    TYPE_MONTHLY_SERIES_URL: str = ""
    GRAPHQL_API_URL: str = ""
    HEADER_KEY: str = ""
    HEADER_VALUE: str = ""

    def __post_init__(self):
        self.TYPE_ID_URL = os.getenv("TYPE_ID_URL", "")
        self.TYPE_ACTRESS_URL = os.getenv("TYPE_ACTRESS_URL", "")
        self.TYPE_REALTIME_URL = os.getenv("TYPE_REALTIME_URL", "")
        self.TYPE_REALTIME_VR_URL = os.getenv("TYPE_REALTIME_VR_URL", "")
        self.TYPE_DATE_URL = os.getenv("TYPE_DATE_URL", "")
        self.TYPE_DAILY_URL = os.getenv("TYPE_DAILY_URL", "")
        self.TYPE_WEEKLY_URL = os.getenv("TYPE_WEEKLY_URL", "")
        self.TYPE_MONTHLY_URL = os.getenv("TYPE_MONTHLY_URL", "")
        self.TYPE_MONTHLY_ACTRESS_URL = os.getenv("TYPE_MONTHLY_ACTRESS_URL", "")
        self.TYPE_MONTHLY_SERIES_URL = os.getenv("TYPE_MONTHLY_SERIES_URL", "")
        self.GRAPHQL_API_URL = os.getenv("GRAPHQL_API_URL", "")
        self.HEADER_KEY = os.getenv("HEADER_KEY", "")
        self.HEADER_VALUE = os.getenv("HEADER_VALUE", "")

    def validate(self) -> List[str]:
        required = {
            "TYPE_ID_URL": self.TYPE_ID_URL,
            "TYPE_ACTRESS_URL": self.TYPE_ACTRESS_URL,
            "TYPE_REALTIME_URL": self.TYPE_REALTIME_URL,
            "TYPE_REALTIME_VR_URL": self.TYPE_REALTIME_VR_URL,
            "TYPE_DATE_URL": self.TYPE_DATE_URL,
            "TYPE_DAILY_URL": self.TYPE_DAILY_URL,
            "TYPE_WEEKLY_URL": self.TYPE_WEEKLY_URL,
            "TYPE_MONTHLY_URL": self.TYPE_MONTHLY_URL,
            "TYPE_MONTHLY_ACTRESS_URL": self.TYPE_MONTHLY_ACTRESS_URL,
            "TYPE_MONTHLY_SERIES_URL": self.TYPE_MONTHLY_SERIES_URL,
            "GRAPHQL_API_URL": self.GRAPHQL_API_URL,
        }
        return [name for name, value in required.items() if not value]


@dataclass
class Constants:
    TARGET_OPERATIONNAME_ID: str = "ContentPageData"
    TARGET_OPERATIONNAME_ACTRESS: str = "AvSearch"
    TARGET_OPERATIONNAME_REALTIME: str = "ContentRankingPage"
    TARGET_OPERATIONNAME_REALTIME_VR: str = "ContentRankingPage"
    TARGET_OPERATIONNAME_DATE: str = "AvSearch"
    TARGET_OPERATIONNAME_DAILY: str = "ContentRankingPage"
    TARGET_OPERATIONNAME_WEEKLY: str = "ContentRankingPage"
    TARGET_OPERATIONNAME_MONTHLY: str = "ContentRankingPage"
    TARGET_OPERATIONNAME_MONTHLY_ACTRESS: str = "ActressRankingPage"
    TARGET_OPERATIONNAME_MONTHLY_SERIES: str = "SeriesRankingPage"

    MAX_RETRY: int = 10
    RETRY_INTERVAL: int = 3
    WAIT_GRAPHQL: int = 30

    BROWSER_VIEWPORT: Dict = field(default_factory=lambda: {"width": 1280, "height": 800})
    BROWSER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    PAGE_TIMEOUT: int = 60000
    SELECTOR_TIMEOUT: int = 25000
    NETWORK_IDLE_TIMEOUT: int = 30000


settings = Settings()
constants = Constants()
