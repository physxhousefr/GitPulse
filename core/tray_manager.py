import os
import sys
import time
import webbrowser
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from .logger import log_streamer

class SystemTrayManager:
    instance = None
    
    def __init__(self, config_mgr, bot_scheduler, on_exit_callback=None):
        SystemTrayManager.instance = self
        self.config_mgr = config_mgr
        self.bot_scheduler = bot_scheduler
        self.on_exit_callback = on_exit_callback
        self.icon = None

    def _create_image(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(root_dir, "static", "images", "tray_icon.png")
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception as e:
                log_streamer.log(f"Erreur chargement icône tray : {e}", level="error")
        
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Background rounded box with cyan border
        draw.rounded_rectangle((2, 2, 62, 62), radius=14, fill=(15, 23, 42, 255), outline=(0, 242, 254, 230), width=3)
        # Git Diamond shape
        draw.polygon([(32, 14), (50, 32), (32, 50), (14, 32)], fill=(255, 255, 255, 255))
        # Git branch inner lines (dark)
        draw.line((32, 20, 32, 42), fill=(15, 23, 42, 255), width=3)
        draw.line((32, 28, 40, 22), fill=(15, 23, 42, 255), width=3)
        draw.ellipse((29, 39, 35, 45), fill=(15, 23, 42, 255))
        draw.ellipse((37, 19, 43, 25), fill=(15, 23, 42, 255))
        return img

    def on_open_dashboard(self, icon=None, item=None):
        webbrowser.open("http://127.0.0.1:5050")

    def on_toggle_bot(self, icon=None, item=None):
        cfg = self.config_mgr.get_all()
        curr_active = cfg.get("bot_active", False)
        new_state = not curr_active
        self.config_mgr.update_settings({"bot_active": new_state})
        if new_state:
            self.bot_scheduler.start()
        else:
            self.bot_scheduler.stop()

    def is_bot_active(self, item=None):
        cfg = self.config_mgr.get_all()
        return cfg.get("bot_active", False)

    def on_trigger_all(self, icon=None, item=None):
        cfg = self.config_mgr.get_all()
        repos = cfg.get("repos", [])
        for r in repos:
            self.bot_scheduler.trigger_single_repo(r["id"])

    def on_exit(self, icon=None, item=None):
        print("[-] gitpulse : Arrêt complet de GitPulse via la System Tray...")
        self.bot_scheduler.stop()
        if self.icon:
            self.icon.stop()
        if self.on_exit_callback:
            self.on_exit_callback()
        os._exit(0)

    def run(self, delay_seconds=0):
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        menu = pystray.Menu(
            item('Ouvrir le Dashboard GitPulse', self.on_open_dashboard, default=True),
            item('Activer / Pause le Bot', self.on_toggle_bot, checked=self.is_bot_active),
            item('Forcer Commit & Push Tout', self.on_trigger_all),
            pystray.Menu.SEPARATOR,
            item('Quitter GitPulse', self.on_exit)
        )

        for attempt in range(5):
            try:
                self.icon = pystray.Icon("GitPulseBot", self._create_image(), "GitPulse Auto-Push Bot", menu)
                self.icon.run()
                break
            except Exception as e:
                time.sleep(3)
