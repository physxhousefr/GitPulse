import os
import sys
import time
import shutil
import socket
import threading
import subprocess
import webbrowser
from datetime import datetime

try:
    import customtkinter as ctk
except ImportError:
    # Fallback d'installation automatique si customtkinter n'est pas encore installé
    subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter"], capture_output=True)
    import customtkinter as ctk

# Configuration Globale de l'Apparence
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(BASE_DIR, "main.py")
REQUIREMENTS_FILE = os.path.join(BASE_DIR, "requirements.txt")
STARTUP_DIR = os.path.join(os.getenv("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
SHORTCUT_STARTUP = os.path.join(STARTUP_DIR, "GitPulse.lnk")
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
SHORTCUT_DESKTOP = os.path.join(DESKTOP_DIR, "GitPulse Dashboard.lnk")

def find_best_pythonw():
    """Détecte l'exécutable pythonw.exe approprié avec les dépendances installées."""
    candidates = []
    
    # 1. Python 3.13 Local AppData
    user_appdata = os.getenv("LOCALAPPDATA", "")
    if user_appdata:
        candidates.append(os.path.join(user_appdata, r"Programs\Python\Python313\pythonw.exe"))
        candidates.append(os.path.join(user_appdata, r"Programs\Python\Python312\pythonw.exe"))
        candidates.append(os.path.join(user_appdata, r"Programs\Python\Python311\pythonw.exe"))

    # 2. Dossier de l'exécutable courant
    py_dir = os.path.dirname(sys.executable)
    candidates.append(os.path.join(py_dir, "pythonw.exe"))
    
    # 3. PATH système
    pythonw_in_path = shutil.which("pythonw.exe")
    if pythonw_in_path:
        candidates.append(pythonw_in_path)

    for cand in candidates:
        if cand and os.path.exists(cand):
            py_exec = cand.replace("pythonw.exe", "python.exe")
            if not os.path.exists(py_exec):
                py_exec = cand
            try:
                res = subprocess.run([py_exec, "-c", "import flask, pystray; print('OK')"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0 and "OK" in res.stdout:
                    return cand
            except Exception:
                pass

    pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return pythonw_path if os.path.exists(pythonw_path) else sys.executable

class GitPulseSetupApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GitPulse — Setup & Service Manager")
        self.geometry("900, 680")
        self.minsize(820, 600)

        # Couleurs
        self.c_bg = "#0f172a"
        self.c_card = "#1e293b"
        self.c_accent = "#00f2fe"
        self.c_green = "#10b981"
        self.c_red = "#ef4444"
        self.c_text_muted = "#94a3b8"

        self.configure(fg_color=self.c_bg)

        self._build_ui()
        self.log("[-] gitpulse : Interface de gestion GitPulse initialisée.")
        
        # Démarrer la boucle de rafraîchissement du statut
        self.refresh_status()
        self._start_status_watcher()

    def _build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(18, 12))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="⚡ GitPulse — Setup & Contrôle",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#ffffff"
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            header_frame,
            text="Configuration de l'Autostart Windows, des dépendances et gestion du service en arrière-plan",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.c_text_muted
        )
        subtitle_lbl.pack(anchor="w")

        # Conteneur Principal (2 colonnes)
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=24, pady=6)
        main_content.grid_columnconfigure((0, 1), weight=1, uniform="col")
        main_content.grid_rowconfigure(0, weight=1)

        # Colonne Gauche (Statut + Dépendances)
        left_col = ctk.CTkFrame(main_content, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Colonne Droite (Autostart + Contrôles)
        right_col = ctk.CTkFrame(main_content, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # --- CARTE 1 : Statut du Service & Environnement ---
        card_status = ctk.CTkFrame(left_col, fg_color=self.c_card, corner_radius=12)
        card_status.pack(fill="x", pady=(0, 12))

        lbl_s_title = ctk.CTkLabel(card_status, text="📊 Statut du Service", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"))
        lbl_s_title.pack(anchor="w", padx=16, pady=(12, 8))

        self.lbl_bot_status = ctk.CTkLabel(
            card_status,
            text="● Service GitPulse : Vérification...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.c_text_muted
        )
        self.lbl_bot_status.pack(anchor="w", padx=16, pady=2)

        self.lbl_autostart_status = ctk.CTkLabel(
            card_status,
            text="● Démarrage Windows : Vérification...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.c_text_muted
        )
        self.lbl_autostart_status.pack(anchor="w", padx=16, pady=2)

        python_path_short = find_best_pythonw()
        self.lbl_py_info = ctk.CTkLabel(
            card_status,
            text=f"● Pythonw : {os.path.basename(python_path_short)} ({python_path_short})",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.c_text_muted,
            wraplength=380,
            justify="left"
        )
        self.lbl_py_info.pack(anchor="w", padx=16, pady=(2, 12))

        # --- CARTE 2 : Dépendances Python ---
        card_deps = ctk.CTkFrame(left_col, fg_color=self.c_card, corner_radius=12)
        card_deps.pack(fill="x", pady=(0, 12))

        lbl_d_title = ctk.CTkLabel(card_deps, text="📦 Dépendances du Projet", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"))
        lbl_d_title.pack(anchor="w", padx=16, pady=(12, 6))

        self.lbl_deps_status = ctk.CTkLabel(
            card_deps,
            text="Modules : Flask, Pystray, Pillow, CustomTkinter",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.c_text_muted
        )
        self.lbl_deps_status.pack(anchor="w", padx=16, pady=2)

        self.btn_install_deps = ctk.CTkButton(
            card_deps,
            text="⚡ Installer / Réparer Dépendances (pip)",
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_install_deps_async
        )
        self.btn_install_deps.pack(fill="x", padx=16, pady=(8, 12))

        # --- CARTE 3 : Configuration Autostart Windows ---
        card_auto = ctk.CTkFrame(right_col, fg_color=self.c_card, corner_radius=12)
        card_auto.pack(fill="x", pady=(0, 12))

        lbl_a_title = ctk.CTkLabel(card_auto, text="🚀 Démarrage Automatique (Windows)", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"))
        lbl_a_title.pack(anchor="w", padx=16, pady=(12, 6))

        btn_grid = ctk.CTkFrame(card_auto, fg_color="transparent")
        btn_grid.pack(fill="x", padx=16, pady=(0, 12))
        btn_grid.grid_columnconfigure((0, 1), weight=1)

        self.btn_enable_auto = ctk.CTkButton(
            btn_grid,
            text="Activer l'Autostart",
            fg_color=self.c_green,
            hover_color="#059669",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_enable_autostart
        )
        self.btn_enable_auto.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.btn_disable_auto = ctk.CTkButton(
            btn_grid,
            text="Désactiver l'Autostart",
            fg_color="#475569",
            hover_color=self.c_red,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_disable_autostart
        )
        self.btn_disable_auto.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="ew")

        self.btn_desktop_shortcut = ctk.CTkButton(
            card_auto,
            text="📌 Créer un Raccourci sur le Bureau",
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.on_create_desktop_shortcut
        )
        self.btn_desktop_shortcut.pack(fill="x", padx=16, pady=(0, 12))

        # --- CARTE 4 : Contrôles d'Exécution du Bot ---
        card_ctrl = ctk.CTkFrame(right_col, fg_color=self.c_card, corner_radius=12)
        card_ctrl.pack(fill="x", pady=(0, 12))

        lbl_c_title = ctk.CTkLabel(card_ctrl, text="🎮 Contrôles du Service GitPulse", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"))
        lbl_c_title.pack(anchor="w", padx=16, pady=(12, 6))

        ctrl_grid = ctk.CTkFrame(card_ctrl, fg_color="transparent")
        ctrl_grid.pack(fill="x", padx=16, pady=(0, 12))
        ctrl_grid.grid_columnconfigure((0, 1), weight=1)

        self.btn_start_tray = ctk.CTkButton(
            ctrl_grid,
            text="▶ Lancer (Arrière-plan)",
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=lambda: self.on_start_bot(autostart=True)
        )
        self.btn_start_tray.grid(row=0, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.btn_start_gui = ctk.CTkButton(
            ctrl_grid,
            text="▶ Lancer (avec Dashboard)",
            fg_color="#0d9488",
            hover_color="#0f766e",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=lambda: self.on_start_bot(autostart=False)
        )
        self.btn_start_gui.grid(row=0, column=1, padx=(4, 0), pady=4, sticky="ew")

        self.btn_open_web = ctk.CTkButton(
            ctrl_grid,
            text="🌐 Ouvrir Dashboard Web",
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.on_open_browser
        )
        self.btn_open_web.grid(row=1, column=0, padx=(0, 4), pady=4, sticky="ew")

        self.btn_stop_bot = ctk.CTkButton(
            ctrl_grid,
            text="⏹ Arrêter GitPulse",
            fg_color="#dc2626",
            hover_color="#b91c1c",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.on_stop_bot
        )
        self.btn_stop_bot.grid(row=1, column=1, padx=(4, 0), pady=4, sticky="ew")

        # --- SECTION INFÉRIEURE : Console de Logs Intégrée ---
        logs_frame = ctk.CTkFrame(self, fg_color=self.c_card, corner_radius=12)
        logs_frame.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        log_top_bar = ctk.CTkFrame(logs_frame, fg_color="transparent")
        log_top_bar.pack(fill="x", padx=16, pady=(10, 4))

        lbl_l_title = ctk.CTkLabel(log_top_bar, text="📋 Console d'Installation & Logs", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        lbl_l_title.pack(side="left")

        btn_clear_logs = ctk.CTkButton(
            log_top_bar,
            text="Effacer",
            width=65,
            height=24,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self.on_clear_logs
        )
        btn_clear_logs.pack(side="right")

        self.txt_logs = ctk.CTkTextbox(
            logs_frame,
            fg_color="#0b0f19",
            text_color="#e2e8f0",
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=8
        )
        self.txt_logs.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def log(self, message, level="info"):
        now_str = datetime.now().strftime("%H:%M:%S")
        prefix = "[-] gitpulse" if level == "info" else "[!] gitpulse"
        line = f"{prefix} : [{now_str}] {message}\n"
        
        self.txt_logs.insert("end", line)
        self.txt_logs.see("end")

    def on_clear_logs(self):
        self.txt_logs.delete("1.0", "end")
        self.log("[-] gitpulse : Console nettoyée.")

    def is_port_open(self, host="127.0.0.1", port=5050):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0

    def is_autostart_configured(self):
        reg_check = subprocess.run(
            ["powershell", "-Command", "Get-ItemPropertyValue -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' -Name 'GitPulse' -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True
        )
        return bool(reg_check.stdout.strip())

    def refresh_status(self):
        # Statut du bot
        is_running = self.is_port_open(port=5050)
        if is_running:
            self.lbl_bot_status.configure(
                text="● Service GitPulse : EN LIGNE (Port 5050)",
                text_color=self.c_green
            )
        else:
            self.lbl_bot_status.configure(
                text="● Service GitPulse : ARRÊTÉ",
                text_color=self.c_red
            )

        # Statut autostart
        if self.is_autostart_configured():
            self.lbl_autostart_status.configure(
                text="● Démarrage Windows : ACTIF (Registre Windows)",
                text_color=self.c_green
            )
        else:
            self.lbl_autostart_status.configure(
                text="● Démarrage Windows : DÉSACTIVÉ",
                text_color=self.c_text_muted
            )

    def _start_status_watcher(self):
        def watcher_loop():
            while True:
                time.sleep(2.5)
                try:
                    self.after(0, self.refresh_status)
                except Exception:
                    break
        threading.Thread(target=watcher_loop, daemon=True).start()

    def on_enable_autostart(self):
        def task():
            self.log("[-] gitpulse : Configuration du Démarrage Automatique Windows...")
            pythonw_path = find_best_pythonw()

            # 1. Nettoyer tout ancien raccourci Startup pour éviter tout double démarrage
            if os.path.exists(SHORTCUT_STARTUP):
                try:
                    os.remove(SHORTCUT_STARTUP)
                except Exception:
                    pass

            # 2. Clé Registre HKCU Run unique
            reg_value = f'"{pythonw_path}" "{MAIN_PY}" --autostart'
            reg_cmd = f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "GitPulse" -Value \'{reg_value}\''
            subprocess.run(["powershell", "-Command", reg_cmd], capture_output=True)

            self.log(f"[-] gitpulse : Démarrage automatique unique activé dans le Registre Windows avec {pythonw_path}")
            self.after(0, self.refresh_status)

        threading.Thread(target=task, daemon=True).start()

    def on_disable_autostart(self):
        def task():
            self.log("[-] gitpulse : Désactivation de l'Autostart Windows...")
            # Supprimer raccourci éventuel
            if os.path.exists(SHORTCUT_STARTUP):
                try:
                    os.remove(SHORTCUT_STARTUP)
                except Exception as e:
                    self.log(f"[!] gitpulse : Erreur lors de la suppression du raccourci : {e}", level="error")

            # Supprimer clé registre
            reg_cmd = 'Remove-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "GitPulse" -ErrorAction SilentlyContinue'
            subprocess.run(["powershell", "-Command", reg_cmd], capture_output=True)

            self.log("[-] gitpulse : Autostart désactivé avec succès.")
            self.after(0, self.refresh_status)

        threading.Thread(target=task, daemon=True).start()

    def on_create_desktop_shortcut(self):
        def task():
            self.log("[-] gitpulse : Création du raccourci sur le Bureau...")
            pythonw_path = find_best_pythonw()
            ps_cmd = (
                f'$Wsh = New-Object -ComObject WScript.Shell; '
                f'$S = $Wsh.CreateShortcut("{SHORTCUT_DESKTOP}"); '
                f'$S.TargetPath = "{pythonw_path}"; '
                f'$S.Arguments = "`"{MAIN_PY}`""; '
                f'$S.WorkingDirectory = "{BASE_DIR}"; '
                f'$S.WindowStyle = 1; '
                f'$S.Save()'
            )
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            self.log(f"[-] gitpulse : Raccourci Bureau créé : '{SHORTCUT_DESKTOP}'")

        threading.Thread(target=task, daemon=True).start()

    def on_start_bot(self, autostart=True):
        def task():
            if self.is_port_open(port=5050):
                self.log("[-] gitpulse : Le service GitPulse tourne déjà sur le port 5050.")
                if not autostart:
                    self.on_open_browser()
                return

            pythonw_path = find_best_pythonw()
            args = [pythonw_path, MAIN_PY]
            if autostart:
                args.append("--autostart")
                self.log(f"[-] gitpulse : Lancement silencieux en arrière-plan avec {pythonw_path}...")
            else:
                self.log(f"[-] gitpulse : Lancement de GitPulse avec ouverture du Dashboard...")

            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(args, cwd=BASE_DIR, creationflags=creation_flags)
            time.sleep(1.5)
            self.after(0, self.refresh_status)

        threading.Thread(target=task, daemon=True).start()

    def on_stop_bot(self):
        def task():
            self.log("[-] gitpulse : Arrêt de tous les processus GitPulse...")
            # Tue les processus python/pythonw qui exécutent main.py
            ps_kill = 'Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like "*main.py*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }'
            subprocess.run(["powershell", "-Command", ps_kill], capture_output=True)
            time.sleep(1.0)
            self.log("[-] gitpulse : Processus GitPulse arrêtés.")
            self.after(0, self.refresh_status)

        threading.Thread(target=task, daemon=True).start()

    def on_open_browser(self):
        webbrowser.open("http://127.0.0.1:5050")
        self.log("[-] gitpulse : Ouverture du Dashboard dans le navigateur : http://127.0.0.1:5050")

    def on_install_deps_async(self):
        def task():
            self.btn_install_deps.configure(state="disabled", text="⏳ Installation en cours...")
            self.log("[-] gitpulse : Lancement de 'pip install -r requirements.txt'...")
            
            py_exec = sys.executable
            cmd = [py_exec, "-m", "pip", "install", "-r", REQUIREMENTS_FILE]
            
            process = subprocess.Popen(
                cmd,
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            for line in process.stdout:
                line_str = line.strip()
                if line_str:
                    self.log(f"[-] gitpulse : {line_str}")

            process.wait()
            if process.returncode == 0:
                self.log("[-] gitpulse : Toutes les dépendances ont été installées et vérifiées avec succès !")
            else:
                self.log(f"[!] gitpulse : Échec de l'installation (Code {process.returncode})", level="error")

            self.btn_install_deps.configure(state="normal", text="⚡ Installer / Réparer Dépendances (pip)")
            self.after(0, self.refresh_status)

        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    app = GitPulseSetupApp()
    app.mainloop()
