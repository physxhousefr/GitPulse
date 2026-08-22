import os
import sys
import threading
import webbrowser
from flask import Flask
from api.routes import init_routes

from core import ConfigManager, GitManager, BotScheduler, log_streamer, SystemTrayManager

app = Flask(__name__)
config_mgr = ConfigManager()
bot_scheduler = BotScheduler(config_mgr)

if config_mgr.get_all().get("bot_active", False):
    bot_scheduler.start()

app.register_blueprint(init_routes(config_mgr, bot_scheduler))

def run_flask_server():
    PORT = 5050
    log_streamer.log(f"Lancement du serveur Web Bot Git sur http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)

def acquire_single_instance_mutex(mutex_name="Global\\GitPulse_SingleInstance_Mutex"):
    """Crée un mutex nommé Windows pour garantir une seule instance active de GitPulse."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, wintypes.BOOL(False), mutex_name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            return None
        return mutex
    except Exception as e:
        log_streamer.log(f"Erreur création mutex: {e}", level="error")
        return True

if __name__ == "__main__":
    is_autostart = "--autostart" in sys.argv
    _instance_mutex = acquire_single_instance_mutex()
    if not _instance_mutex:
        if not is_autostart:
            webbrowser.open("http://127.0.0.1:5050")
        sys.exit(0)

    try:
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()

        if not is_autostart:
            threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5050")).start()

        tray = SystemTrayManager(config_mgr, bot_scheduler)
        tray.run(delay_seconds=3 if is_autostart else 0)
    except Exception as e:
        import traceback
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gitpulse_autostart.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{sys.argv}] Exception: {str(e)}\n{traceback.format_exc()}\n")
