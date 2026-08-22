import time
import threading
import datetime
import random
from queue import Queue, Empty
from typing import Generator
from .config_manager import ConfigManager
from .git_manager import GitManager

from .logger import log_streamer

class BotScheduler:
    def __init__(self, config_mgr: ConfigManager):
        self.config_mgr = config_mgr
        self._thread = None
        self._running = False
        self._last_run_map = {}

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        log_streamer.log("Bot d'Auto-Push démarré en arrière-plan.", level="info")

    def stop(self):
        self._running = False
        log_streamer.log("Bot d'Auto-Push mis en pause.", level="info")

    def is_running(self) -> bool:
        return self._running

    def trigger_single_repo(self, repo_id: str) -> dict:
        cfg = self.config_mgr.get_all()
        repo = next((r for r in cfg["repos"] if r["id"] == repo_id), None)
        if not repo:
            log_streamer.log(f"Dépôt introuvable : {repo_id}", level="error")
            return {"success": False, "error": "Repo not found"}

        log_streamer.log(f"Action manuelle déclenchée sur '{repo['name']}'...", level="info")
        return self._process_repo(repo, cfg)

    def _process_repo(self, repo: dict, cfg: dict) -> dict:
        repo_name = repo["name"]
        repo_path = repo["path"]
        mode = repo.get("mode", "hybrid")
        dry_run = cfg.get("dry_run", False)
        commit_style = cfg.get("commit_style", "smart_conventional")
        commit_template = cfg.get("commit_message_template", "docs(auto): sync activity log - {date} {time}")
        activity_filename = cfg.get("activity_file_name", "ACTIVITY.md")
        ai_provider = cfg.get("ai_provider", "none")
        ai_api_key = cfg.get("ai_api_key", "")
        ai_model = cfg.get("ai_model", "gpt-4o-mini")

        log_streamer.log(f"Analyse du dépôt '{repo_name}' ({mode}, style={commit_style}, dry_run={dry_run})...", level="info")

        success, status, details = GitManager.process_auto_commit_push(
            repo_path=repo_path,
            mode=mode,
            commit_template=commit_template,
            commit_style=commit_style,
            activity_filename=activity_filename,
            dry_run=dry_run,
            ai_provider=ai_provider,
            ai_api_key=ai_api_key,
            ai_model=ai_model
        )

        if success:
            log_streamer.log(f"'{repo_name}' : {status} - {details}", level="info")
        else:
            log_streamer.log(f"'{repo_name}' : Échec ({status}) - {details}", level="error")

        self.config_mgr.record_commit(
            repo_id=repo["id"],
            repo_name=repo_name,
            commit_msg=details,
            status=status,
            details=details
        )
        
        from .notifier import Notifier
        if status in ["Success", "Error"]:
            if cfg.get("discord_notifications", False):
                webhook = cfg.get("discord_webhook_url", "")
                if webhook:
                    Notifier.send_discord_notification(webhook, repo_name, details, status)
            if cfg.get("windows_notifications", True):
                Notifier.send_windows_notification(f"GitPulse: {status}", f"{repo_name} - {details}")

        self._last_run_map[repo["id"]] = time.time()
        return {"success": success, "status": status, "details": details}

    def _run_loop(self):
        while self._running:
            try:
                cfg = self.config_mgr.get_all()
                if not cfg.get("bot_active", False):
                    time.sleep(3)
                    continue

                repos = cfg.get("repos", [])
                enabled_repos = [r for r in repos if r.get("enabled", True)]

                if not enabled_repos:
                    time.sleep(5)
                    continue

                now = time.time()
                for repo in enabled_repos:
                    if not self._running:
                        break

                    repo_id = repo["id"]
                    interval_mins = repo.get("interval_minutes", cfg.get("global_interval_minutes", 30))
                    
                    if cfg.get("randomize_schedule", False):
                        jitter = random.randint(
                            cfg.get("min_random_delay_mins", 1), 
                            cfg.get("max_random_delay_mins", 10)
                        )
                        interval_secs = (interval_mins + jitter) * 60
                    else:
                        interval_secs = interval_mins * 60

                    last_run = self._last_run_map.get(repo_id, 0)
                    if now - last_run >= interval_secs:
                        self._process_repo(repo, cfg)

            except Exception as e:
                log_streamer.log(f"Erreur dans la boucle du planificateur : {str(e)}", level="error")

            time.sleep(5)
