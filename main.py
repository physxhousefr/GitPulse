import os
import sys
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, Response
import tkinter as tk
from tkinter import filedialog

from core import ConfigManager, GitManager, BotScheduler, log_streamer, SystemTrayManager

app = Flask(__name__)
config_mgr = ConfigManager()
bot_scheduler = BotScheduler(config_mgr)

if config_mgr.get_all().get("bot_active", False):
    bot_scheduler.start()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = config_mgr.get_all()
    enriched_repos = []
    repo_paths = []
    total_added = 0
    total_deleted = 0
    
    for r in cfg.get("repos", []):
        repo_data = r.copy()
        git_info = GitManager.get_status_info(r["path"])
        repo_data["git_info"] = git_info
        enriched_repos.append(repo_data)
        if git_info.get("is_repo"):
            repo_paths.append(r["path"])
            d_stats = git_info.get("diff_stats", {})
            total_added += d_stats.get("lines_added", 0)
            total_deleted += d_stats.get("lines_deleted", 0)
    
    cfg_copy = cfg.copy()
    cfg_copy["repos"] = enriched_repos
    cfg_copy["bot_running"] = bot_scheduler.is_running()
    cfg_copy["heatmap_data"] = GitManager.get_commit_heatmap_data(repo_paths)
    cfg_copy["diff_totals"] = {"lines_added": total_added, "lines_deleted": total_deleted}
    return jsonify(cfg_copy)

@app.route("/api/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    prev_active = config_mgr.get_all().get("bot_active", False)
    new_config = config_mgr.update_settings(data)
    
    curr_active = new_config.get("bot_active", False)
    if curr_active and not prev_active:
        bot_scheduler.start()
    elif not curr_active and prev_active:
        bot_scheduler.stop()

    return jsonify({"success": True, "config": new_config})

@app.route("/api/select_folder", methods=["GET"])
def select_folder():
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Sélectionner le dossier du Dépôt Git")
    root.destroy()
    if folder_path:
        norm_path = GitManager.normalize_repo_path(folder_path)
        is_git = GitManager.is_git_repo(norm_path)
        return jsonify({"success": True, "path": norm_path, "is_git_repo": is_git})
    return jsonify({"success": False, "path": ""})

@app.route("/api/repos", methods=["POST"])
def add_repo():
    data = request.json or {}
    raw_path = data.get("path", "").strip()
    if not raw_path:
        return jsonify({"success": False, "error": "Chemin de dossier valide requis."}), 400

    norm_path = GitManager.normalize_repo_path(raw_path)
    if not os.path.exists(norm_path):
        return jsonify({"success": False, "error": f"Le dossier '{norm_path}' n'existe pas sur le système."}), 400

    if not GitManager.is_git_repo(norm_path):
        return jsonify({"success": False, "error": f"Le dossier '{norm_path}' n'est pas un dépôt Git valide (aucun dépôt Git détecté)."}), 400

    name = data.get("name", "").strip()
    if not name or name.lower() == ".git":
        name = os.path.basename(norm_path) or "Unnamed Repo"

    mode = data.get("mode", "hybrid")
    interval = int(data.get("interval_minutes", 30))

    repo = config_mgr.add_repo(norm_path, name=name, mode=mode, interval_minutes=interval)
    log_streamer.log(f"Nouveau dépôt ajouté au suivi : '{repo['name']}' ({norm_path})", level="info")
    return jsonify({"success": True, "repo": repo})

@app.route("/api/repos/<repo_id>", methods=["DELETE"])
def remove_repo(repo_id):
    success = config_mgr.remove_repo(repo_id)
    if success:
        log_streamer.log(f"Dépôt ID {repo_id} retiré du suivi.", level="info")
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Dépôt non trouvé."}), 404

@app.route("/api/repos/<repo_id>", methods=["PUT"])
def update_repo(repo_id):
    data = request.json or {}
    updated = config_mgr.update_repo(repo_id, data)
    if updated:
        return jsonify({"success": True, "repo": updated})
    return jsonify({"success": False, "error": "Dépôt non trouvé."}), 404

@app.route("/api/repos/<repo_id>/trigger", methods=["POST"])
def trigger_repo(repo_id):
    res = bot_scheduler.trigger_single_repo(repo_id)
    return jsonify(res)

@app.route("/api/logs/stream")
def stream_logs():
    def event_stream():
        q = log_streamer.subscribe()
        try:
            yield f"data: [-] gitpulse : Connexion établie avec la console de logs.\n\n"
            while True:
                log_msg = q.get()
                yield f"data: {log_msg}\n\n"
        except GeneratorExit:
            log_streamer.unsubscribe(q)

    return Response(event_stream(), mimetype="text/event-stream")

def run_flask_server():
    PORT = 5050
    print(f"[-] gitpulse : Lancement du serveur Web Bot Git sur http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5050")).start()

    tray = SystemTrayManager(config_mgr, bot_scheduler)
    tray.run()
