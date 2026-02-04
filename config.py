import os
from dotenv import load_dotenv

load_dotenv()

TYPE_ID_URL = os.getenv("TYPE_ID_URL", "")
TYPE_ACTRESS_URL = os.getenv("TYPE_ACTRESS_URL", "")
GRAPHQL_API_URL = os.getenv("GRAPHQL_API_URL", "")

HEADER_KEY = os.getenv("HEADER_KEY", "")
HEADER_VALUE = os.getenv("HEADER_VALUE", "")

if not TYPE_ID_URL or not TYPE_ACTRESS_URL or not GRAPHQL_API_URL:
    missing = []
    if not TYPE_ID_URL:
        missing.append("TYPE_ID_URL")
    if not TYPE_ACTRESS_URL:
        missing.append("TYPE_ACTRESS_URL")
    if not GRAPHQL_API_URL:
        missing.append("GRAPHQL_API_URL")
    raise EnvironmentError(f"缺少必要的环境变量: {', '.join(missing)}")

TARGET_OPERATION_ID = "ContentPageData"
TARGET_OPERATION_ACTRESS = "AvSearch"

MAX_RETRY = 10
RETRY_INTERVAL = 3
WAIT_GRAPHQL = 15
