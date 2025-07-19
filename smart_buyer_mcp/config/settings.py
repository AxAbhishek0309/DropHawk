import os
from dotenv import load_dotenv

load_dotenv()

settings = {
    "NOTION_API_KEY": os.getenv("NOTION_API_KEY"),
    "LLM_API_KEY": os.getenv("LLM_API_KEY"),
    "PRICE_CHECK_INTERVAL_MIN": int(os.getenv("PRICE_CHECK_INTERVAL_MIN", "60")),
    "FEATURE_SUMMARIZE_REVIEWS": os.getenv("FEATURE_SUMMARIZE_REVIEWS", "1") == "1",
    "FEATURE_AUTO_BUY": os.getenv("FEATURE_AUTO_BUY", "0") == "1",
} 