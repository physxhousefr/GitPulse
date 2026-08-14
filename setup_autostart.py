import os
import sys
import subprocess

def add_to_startup():
    startup_dir = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable

    main_py_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
    working_dir = os.path.dirname(main_py_path)
    shortcut_path = os.path.join(startup_dir, "GitPulse.lnk")
    
    ps_cmd = f'$Wsh = New-Object -ComObject WScript.Shell; $S = $Wsh.CreateShortcut("{shortcut_path}"); $S.TargetPath = "{pythonw_path}"; $S.Arguments = "`"{main_py_path}`""; $S.WorkingDirectory = "{working_dir}"; $S.WindowStyle = 7; $S.Save()'
    subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)

    print("[-] gitpulse : Raccourci GitPulse ajouté au démarrage automatique de Windows avec succès !")

if __name__ == "__main__":
    add_to_startup()
