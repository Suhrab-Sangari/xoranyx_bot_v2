import json
import os
from datetime import datetime

class SimpleDB:
    def __init__(self, filename="data.json"):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"users": {}, "ads": {}, "tasks": {}}
        return {"users": {}, "ads": {}, "tasks": {}}
    
    def save_data(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "id": user_id,
                "coins": 0,
                "invites": [],
                "invited_by": None,
                "daily_stats": {
                    "ads_watched": 0,
                    "tasks_completed": 0,
                    "last_login": None
                },
                "total_earned": 0
            }
            self.save_data()
        return self.data["users"][user_id]
    
    def update_user(self, user_id, updates):
        user = self.get_user(user_id)
        user.update(updates)
        self.save_data()
        return user
    
    def add_coins(self, user_id, amount, reason=""):
        user = self.get_user(user_id)
        user["coins"] += amount
        user["total_earned"] += amount
        
        if "transactions" not in user:
            user["transactions"] = []
        
        user["transactions"].append({
            "amount": amount,
            "reason": reason,
            "date": datetime.now().isoformat()
        })
        
        self.save_data()
        return user["coins"]
    
    def reset_daily_stats(self, user_id):
        user = self.get_user(user_id)
        user["daily_stats"] = {
            "ads_watched": 0,
            "tasks_completed": 0,
            "last_login": datetime.now().isoformat()
        }
        self.save_data()