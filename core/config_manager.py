import os
import json
import uuid
import datetime
from typing import Dict, List, Any
from .logger import log_streamer

# Root directory of project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

DEFAULT_CONFIG = {
    "bot_active": False,
    "dry_run": False,
    "commit_style": "smart_conventional",
    "commit_message_template": "docs(auto): sync repo activity log - {date} {time}",
    "activity_file_name": "ACTIVITY.md",
    "global_interval_minutes": 30,
    "randomize_schedule": True,
    "min_random_delay_mins": 5,
    "max_random_delay_mins": 45,
    "ai_provider": "none",
    "ai_api_key": "",
    "ai_model": "gpt-4o-mini",
    "repos": [],
    "history": []
}

class ConfigManager:
    def __init__(self, filepath: str = CONFIG_FILE):
        self.filepath = filepath
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            self._save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            log_streamer.log(f"Erreur de chargement config.json : {e}", level="error")
            return DEFAULT_CONFIG.copy()

    def _save(self, data: Dict[str, Any] = None):
        if data is None:
            data = self.config
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_all(self) -> Dict[str, Any]:
        return self.config

    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        for key in ["bot_active", "dry_run", "commit_style", "commit_message_template", "activity_file_name", 
                    "global_interval_minutes", "randomize_schedule", "min_random_delay_mins", "max_random_delay_mins",
                    "ai_provider", "ai_api_key", "ai_model"]:
            if key in settings:
                self.config[key] = settings[key]
        self._save()
        return self.config

    def add_repo(self, path: str, name: str = None, mode: str = "hybrid", interval_minutes: int = 30) -> Dict[str, Any]:
        path = os.path.abspath(path)
        if not name:
            name = os.path.basename(path) or "Unnamed Repo"
        
        for repo in self.config["repos"]:
            if repo["path"] == path:
                return repo

        repo_item = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "path": path,
            "enabled": True,
            "mode": mode,
            "interval_minutes": interval_minutes,
            "last_run": None,
            "last_status": "Idle",
            "commit_count": 0
        }
        self.config["repos"].append(repo_item)
        self._save()
        return repo_item

    def remove_repo(self, repo_id: str) -> bool:
        initial_len = len(self.config["repos"])
        self.config["repos"] = [r for r in self.config["repos"] if r["id"] != repo_id]
        if len(self.config["repos"]) < initial_len:
            self._save()
            return True
        return False

    def update_repo(self, repo_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        for repo in self.config["repos"]:
            if repo["id"] == repo_id:
                for k, v in updates.items():
                    if k in repo:
                        repo[k] = v
                self._save()
                return repo
        return None

    def record_commit(self, repo_id: str, repo_name: str, commit_msg: str, status: str, details: str = ""):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for repo in self.config["repos"]:
            if repo["id"] == repo_id:
                repo["last_run"] = now_str
                repo["last_status"] = status
                if status == "Success":
                    repo["commit_count"] += 1

        history_entry = {
            "id": str(uuid.uuid4())[:8],
            "repo_id": repo_id,
            "repo_name": repo_name,
            "timestamp": now_str,
            "commit_msg": commit_msg,
            "status": status,
            "details": details
        }
        
        self.config["history"].insert(0, history_entry)
        self.config["history"] = self.config["history"][:100]
        self._save()
