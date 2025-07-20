import os
import requests
from config.settings import settings

class NotionExporter:
    def __init__(self):
        self.api_key = settings["NOTION_API_KEY"]
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1/pages"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def export_decision(self, decision):
        if not self.api_key or not self.database_id:
            print("Notion API key or database ID not set.")
            return
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Title": {"title": [{"text": {"content": decision.get("title", "Unknown Product")}}]},
                "Price": {"rich_text": [{"text": {"content": str(decision.get("price", ""))}}]},
                "Rating": {"rich_text": [{"text": {"content": str(decision.get("rating", ""))}}]},
                "Verdict": {"select": {"name": decision.get("verdict", {}).get("verdict", "Unknown")}},
                "Checked At": {"date": {"start": decision.get("verdict", {}).get("timestamp", "")}}
            },
            "url": decision.get("url", "")
        }
        try:
            response = requests.post(self.base_url, headers=self.headers, json=data)
            response.raise_for_status()
            print(f"Exported to Notion: {decision.get('title')}")
        except Exception as e:
            print(f"Failed to export to Notion: {e}") 