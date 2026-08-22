import datetime
from queue import Queue

LOG_NAME = "gitpulse"

class LogStreamer:
    """Gestionnaire de flux de logs SSE (Server-Sent Events) et utilitaire de logs centralise."""
    def __init__(self):
        self.listeners = []

    def subscribe(self) -> Queue:
        q = Queue()
        self.listeners.append(q)
        return q

    def unsubscribe(self, q: Queue):
        if q in self.listeners:
            self.listeners.remove(q)

    def log(self, message: str, level: str = "info"):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        if level == "info":
            prefix = f"[-] {LOG_NAME}"
        elif level == "error":
            prefix = f"[!] {LOG_NAME}"
        elif level == "debug":
            prefix = f"[?] {LOG_NAME}"
        else:
            prefix = f"[-] {LOG_NAME}"

        formatted_log = f"{prefix} : [{now_str}] {message}"
        print(formatted_log) # Affichage console aussi

        dead_queues = []
        for q in self.listeners:
            try:
                q.put_nowait(formatted_log)
            except Exception:
                dead_queues.append(q)
        for dq in dead_queues:
            self.unsubscribe(dq)

log_streamer = LogStreamer()
