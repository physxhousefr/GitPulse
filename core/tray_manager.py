import os
import sys
import webbrowser
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

class SystemTrayManager:
    def __init__(self, config_mgr, bot_scheduler, on_exit_callback=None):
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
            except Exception:
                pass
        
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, 60, 60), fill=(15, 23, 42, 240), outline=(0, 242, 254, 255), width=3)
        draw.line((24, 16, 24, 48), fill=(0, 242, 254, 255), width=4)
        draw.ellipse((20, 12, 28, 20), fill=(16, 185, 129, 255))
        draw.ellipse((20, 44, 28, 52), fill=(16, 185, 129, 255))
        draw.ellipse((38, 28, 46, 36), fill=(0, 242, 254, 255))
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

    def run(self):
        menu = pystray.Menu(
            item('Ouvrir le Dashboard GitPulse', self.on_open_dashboard, default=True),
            item('Activer / Pause le Bot', self.on_toggle_bot, checked=self.is_bot_active),
            item('Forcer Commit & Push Tout', self.on_trigger_all),
            pystray.Menu.SEPARATOR,
            item('Quitter GitPulse', self.on_exit)
        )
        self.icon = pystray.Icon("GitPulseBot", self._create_image(), "GitPulse Auto-Push Bot", menu)
        self.icon.run()
