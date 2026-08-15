import os
import sys
import subprocess
import shutil

def find_working_pythonw():
    candidates = []
    
    # 1. Tester d'abord Python 3.13 où sont installées les dépendances
    user_appdata = os.getenv('LOCALAPPDATA', '')
    if user_appdata:
        candidates.append(os.path.join(user_appdata, r"Programs\Python\Python313\pythonw.exe"))

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
                res = subprocess.run([py_exec, "-c", "import flask, pystray; print('OK')"], capture_output=True, text=True, timeout=5)
                if res.returncode == 0 and "OK" in res.stdout:
                    return cand
            except Exception:
                pass

    pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return pythonw_path if os.path.exists(pythonw_path) else sys.executable

def add_to_startup():
    startup_dir = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    pythonw_path = find_working_pythonw()

    main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    working_dir = os.path.dirname(main_py_path)
    shortcut_path = os.path.join(startup_dir, "GitPulse.lnk")
    
    # 1. Nettoyer tout ancien raccourci Startup pour éviter les doublons
    if os.path.exists(shortcut_path):
        try:
            os.remove(shortcut_path)
        except Exception:
            pass

    # 2. Enregistrement unique via le Registre Windows HKCU Run
    reg_value = f'"{pythonw_path}" "{main_py_path}" --autostart'
    reg_cmd = f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "GitPulse" -Value \'{reg_value}\''
    subprocess.run(["powershell", "-Command", reg_cmd], capture_output=True)

    print(f"[-] gitpulse : Démarrage automatique unique configuré via le Registre Windows avec : {pythonw_path}")

if __name__ == "__main__":
    add_to_startup()
