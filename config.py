import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    
    # Bot info
    BOT_NAME = "XORANYX"
    BOT_VERSION = "1.0"
    
    # Reward settings
    REWARDS = {
        "ad_watch": 10,
        "micro_task": 5,
        "invite": 50,
        "daily_login": 20
    }
    
    # Limit settings
    LIMITS = {
        "max_ads_per_day": 10,
        "max_tasks_per_day": 5,
        "max_invites": 20
    }
    
    # Web App URL (بعداً پر می‌کنیم)
    WEB_APP_URL = "https://your-webapp-url.here"
    
    # Database file
    DB_FILE = "data.json"