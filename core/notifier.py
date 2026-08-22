import urllib.request
import json
import threading
from .logger import log_streamer
from .tray_manager import SystemTrayManager

class Notifier:
    @staticmethod
    def send_discord_notification(webhook_url: str, repo_name: str, message: str, status: str):
        if not webhook_url or not webhook_url.strip():
            return

        def _send():
            try:
                color = 3066993 if status.lower() == "success" else 15158332
                title = f"✅ Push Réussi : {repo_name}" if status.lower() == "success" else f"❌ Erreur Push : {repo_name}"
                
                payload = {
                    "username": "GitPulse",
                    "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
                    "embeds": [{
                        "title": title,
                        "description": f"**Message :**\n```\n{message}\n```",
                        "color": color,
                        "footer": {"text": "GitPulse Auto-Push Bot"}
                    }]
                }
                
                req = urllib.request.Request(
                    webhook_url.strip(),
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "GitPulseBot/1.0"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=5):
                    pass
            except Exception as e:
                log_streamer.log(f"Erreur notification Discord : {e}", level="error")

        threading.Thread(target=_send, daemon=True).start()

    @staticmethod
    def send_windows_notification(title: str, message: str):
        def _send():
            try:
                tray = SystemTrayManager.instance
                if tray and tray.icon and hasattr(tray.icon, 'notify'):
                    safe_msg = message if len(message) < 200 else message[:197] + "..."
                    tray.icon.notify(safe_msg, title)
            except Exception as e:
                log_streamer.log(f"Erreur notification Windows : {e}", level="error")
                
        threading.Thread(target=_send, daemon=True).start()
