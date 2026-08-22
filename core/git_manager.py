import os
import sys
import subprocess
import datetime
import time
import time
from typing import Tuple, Dict, Any, List
from .ai_generator import generate_commit_message_with_ai

class GitManager:
    @classmethod
    def normalize_repo_path(cls, path: str) -> str:
        """Normalise le chemin en résolvant la racine du dépôt Git (ex: si l'utilisateur choisit le dossier .git)."""
        if not path:
            return ""
        path = path.strip().strip('"').strip("'")
        
        if os.path.basename(path).lower() == ".git":
            path = os.path.dirname(path)

        path = os.path.abspath(path)

        ok, root_out = cls.run_git_command(path, ["rev-parse", "--show-toplevel"])
        if ok and root_out.strip():
            return os.path.abspath(root_out.strip())
        return path

    @staticmethod
    def run_git_command(repo_path: str, args: list) -> Tuple[bool, str]:
        """Exécute une commande git de manière 100% silencieuse sans aucun clignotement de fenêtre console."""
        if not os.path.exists(repo_path):
            return False, f"Le chemin '{repo_path}' n'existe pas."

        cmd = ["git"] + args
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        try:
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=creation_flags
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip() or result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "La commande Git a expiré (Timeout 30s)."
        except Exception as e:
            return False, f"Erreur lors de l'exécution de Git: {str(e)}"

    @classmethod
    def is_git_repo(cls, repo_path: str) -> bool:
        norm_path = cls.normalize_repo_path(repo_path)
        ok, out = cls.run_git_command(norm_path, ["rev-parse", "--show-toplevel"])
        if ok and out.strip():
            return True
        git_dir = os.path.join(norm_path, ".git")
        return os.path.exists(git_dir)

    @classmethod
    def get_current_branch(cls, repo_path: str) -> str:
        norm_path = cls.normalize_repo_path(repo_path)
        
        ok, out = cls.run_git_command(norm_path, ["branch", "--show-current"])
        if ok and out.strip() and out.strip() != "HEAD":
            return out.strip()

        ok, out = cls.run_git_command(norm_path, ["symbolic-ref", "--short", "HEAD"])
        if ok and out.strip() and out.strip() != "HEAD":
            return out.strip()

        ok, out = cls.run_git_command(norm_path, ["rev-parse", "--abbrev-ref", "HEAD"])
        if ok and out.strip() and out.strip() != "HEAD":
            return out.strip()

        return "main"

    @classmethod
    def get_diff_stats(cls, repo_path: str) -> Dict[str, int]:
        norm_path = cls.normalize_repo_path(repo_path)
        ok, out = cls.run_git_command(norm_path, ["diff", "--shortstat"])
        lines_added = 0
        lines_deleted = 0
        files_changed = 0

        if ok and out:
            parts = out.split(",")
            for p in parts:
                p_str = p.strip()
                if "file" in p_str:
                    try: files_changed = int(p_str.split()[0])
                    except: pass
                elif "insertion" in p_str:
                    try: lines_added = int(p_str.split()[0])
                    except: pass
                elif "deletion" in p_str:
                    try: lines_deleted = int(p_str.split()[0])
                    except: pass

        return {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted
        }

    _heatmap_cache = {}
    _heatmap_cache_expiry = 300  # 5 minutes

    @classmethod
    def get_commit_heatmap_data(cls, repo_paths: List[str]) -> Dict[str, int]:
        cache_key = tuple(sorted(repo_paths))
        now = time.time()
        
        if cache_key in cls._heatmap_cache:
            cache_time, data = cls._heatmap_cache[cache_key]
            if now - cache_time < cls._heatmap_cache_expiry:
                return data

        heatmap_map = {}
        for r_path in repo_paths:
            norm_path = cls.normalize_repo_path(r_path)
            if not cls.is_git_repo(norm_path):
                continue
            ok, out = cls.run_git_command(norm_path, ["log", "--format=%ad", "--date=short", "--since=1 year ago"])
            if ok and out.strip():
                lines = out.strip().split("\n")
                for date_str in lines:
                    date_str = date_str.strip()
                    if date_str:
                        heatmap_map[date_str] = heatmap_map.get(date_str, 0) + 1
        cls._heatmap_cache[cache_key] = (now, heatmap_map)
        return heatmap_map

    @classmethod
    def generate_smart_commit_message(
        cls, 
        repo_path: str, 
        style: str = "smart_conventional", 
        fallback_template: str = "",
        ai_provider: str = "none",
        ai_api_key: str = "",
        ai_model: str = "gpt-4o-mini"
    ) -> str:
        norm_path = cls.normalize_repo_path(repo_path)
        ok, out = cls.run_git_command(norm_path, ["status", "--porcelain"])
        
        repo_name = os.path.basename(norm_path)
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        if not ok or not out.strip():
            if style == "smart_emoji":
                return f"📝 docs(auto): update activity log - {date_str} {time_str}"
            return f"docs(auto): sync activity log - {date_str} {time_str}"

        modified_files = []
        for line in out.strip().split("\n"):
            parts = line.strip().split(maxsplit=1)
            if len(parts) >= 2:
                modified_files.append(parts[1].replace('"', ''))

        has_readme = any("readme" in f.lower() for f in modified_files)
        has_docs = any(f.endswith(".md") or f.endswith(".txt") for f in modified_files)
        has_src = any(f.endswith((".cpp", ".c", ".h", ".hpp", ".cs", ".py", ".js", ".ts", ".go", ".rs")) for f in modified_files)
        has_ui = any(f.endswith((".css", ".html", ".scss", ".vue", ".jsx")) for f in modified_files)
        has_config = any(f.endswith((".json", ".yml", ".yaml", ".bat", ".sh", ".toml")) or "config" in f.lower() for f in modified_files)

        primary_file = modified_files[0] if len(modified_files) == 1 else None

        if style == "smart_ai" and ai_provider != "none" and ai_api_key:
            ok_diff, diff_out = cls.run_git_command(norm_path, ["diff", "--cached"])
            if not ok_diff or not diff_out.strip():
                ok_diff, diff_out = cls.run_git_command(norm_path, ["diff"])
            if ok_diff and diff_out.strip():
                ai_msg = generate_commit_message_with_ai(diff_out, ai_provider, ai_api_key, ai_model)
                if ai_msg:
                    return ai_msg
            # Fallback to smart_conventional if AI fails
            style = "smart_conventional"

        if style == "smart_emoji":
            if has_readme:
                return f"📝 docs(readme): update README.md documentation"
            elif has_src:
                filename = os.path.basename(primary_file) if primary_file else f"{len(modified_files)} files"
                return f"✨ feat(core): update source logic ({filename})"
            elif has_ui:
                return f"🎨 style(ui): adjust interface styling & layout"
            elif has_config:
                return f"🔧 chore(config): update build & configuration settings"
            elif has_docs:
                return f"📚 docs: update documentation files"
            else:
                return f"⚡ update: sync {len(modified_files)} modified file(s)"
        
        elif style == "smart_conventional":
            if has_readme:
                return f"docs(readme): update README documentation"
            elif has_src:
                filename = os.path.basename(primary_file) if primary_file else f"{len(modified_files)} files"
                return f"feat(src): update code implementation ({filename})"
            elif has_ui:
                return f"style(ui): update styling and assets"
            elif has_config:
                return f"chore(config): update configuration files"
            elif has_docs:
                return f"docs: update documentation"
            else:
                return f"refactor: update {len(modified_files)} file(s)"

        else:
            if fallback_template:
                return fallback_template.format(date=date_str, time=time_str, repo=repo_name)
            return f"docs(auto): sync repo activity log - {date_str} {time_str}"

    @classmethod
    def get_status_info(cls, repo_path: str) -> Dict[str, Any]:
        norm_path = cls.normalize_repo_path(repo_path)
        if not cls.is_git_repo(norm_path):
            return {"is_repo": False, "error": "Pas un dépôt Git valide."}

        branch = cls.get_current_branch(norm_path)
        ok_status, status_out = cls.run_git_command(norm_path, ["status", "--porcelain"])
        is_dirty = bool(status_out.strip()) if ok_status else False

        ok_sb, sb_out = cls.run_git_command(norm_path, ["status", "-sb"])
        is_ahead = "ahead" in sb_out if ok_sb else False

        diff_stats = cls.get_diff_stats(norm_path)

        ok_last, last_log = cls.run_git_command(norm_path, ["log", "-1", "--format=%h|%s|%cr|%an"])
        last_commit = {}
        if ok_last and last_log:
            parts = last_log.split("|")
            if len(parts) >= 4:
                last_commit = {
                    "hash": parts[0],
                    "message": parts[1],
                    "relative_date": parts[2],
                    "author": parts[3]
                }

        return {
            "is_repo": True,
            "branch": branch,
            "is_dirty": is_dirty,
            "is_ahead": is_ahead,
            "diff_stats": diff_stats,
            "modified_files_count": len(status_out.strip().split("\n")) if status_out.strip() else 0,
            "last_commit": last_commit
        }

    @classmethod
    def append_activity_log(cls, repo_path: str, filename: str = "ACTIVITY.md") -> str:
        norm_path = cls.normalize_repo_path(repo_path)
        file_path = os.path.join(norm_path, filename)
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        entry = f"- **{date_str}** — Sync d'activité automatique via Git Auto-Push Bot.\n"

        if not os.path.exists(file_path):
            header = f"# Journal d'Activité Git ({os.path.basename(norm_path)})\n\nFichier d'activité généré automatiquement par **Git Auto-Push Bot**.\n\n## Historique\n\n"
            content = header + entry
        else:
            content = entry

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)

        return file_path

    @classmethod
    def process_auto_commit_push(
        cls,
        repo_path: str,
        mode: str = "hybrid",
        commit_template: str = "docs(auto): sync activity log - {date} {time}",
        commit_style: str = "smart_conventional",
        activity_filename: str = "ACTIVITY.md",
        dry_run: bool = False,
        ai_provider: str = "none",
        ai_api_key: str = "",
        ai_model: str = "gpt-4o-mini"
    ) -> Tuple[bool, str, str]:
        norm_path = cls.normalize_repo_path(repo_path)
        if not cls.is_git_repo(norm_path):
            return False, "Error", f"Le chemin '{norm_path}' n'est pas un dépôt Git."

        branch = cls.get_current_branch(norm_path)
        ok_status, status_out = cls.run_git_command(norm_path, ["status", "--porcelain"])
        has_local_changes = bool(status_out.strip()) if ok_status else False

        ok_sb, sb_out = cls.run_git_command(norm_path, ["status", "-sb"])
        is_ahead = "ahead" in sb_out if ok_sb else False

        staged_anything = False

        if mode == "changes_only":
            if not has_local_changes and not is_ahead:
                return True, "Skipped", "Aucun changement local et aucun commit en attente de push."
            if has_local_changes:
                ok_add, err_add = cls.run_git_command(norm_path, ["add", "-A"])
                if not ok_add:
                    return False, "Error", f"Échec de 'git add -A': {err_add}"
                staged_anything = True

        elif mode == "activity_only":
            act_file = cls.append_activity_log(norm_path, activity_filename)
            rel_act_file = os.path.relpath(act_file, norm_path)
            ok_add, err_add = cls.run_git_command(norm_path, ["add", rel_act_file])
            if not ok_add:
                return False, "Error", f"Échec de 'git add {rel_act_file}': {err_add}"
            staged_anything = True

        else:  # 'hybrid'
            if has_local_changes:
                ok_add, err_add = cls.run_git_command(norm_path, ["add", "-A"])
                if not ok_add:
                    return False, "Error", f"Échec de 'git add -A': {err_add}"
                staged_anything = True
            elif not is_ahead:
                act_file = cls.append_activity_log(norm_path, activity_filename)
                rel_act_file = os.path.relpath(act_file, norm_path)
                ok_add, err_add = cls.run_git_command(norm_path, ["add", rel_act_file])
                if not ok_add:
                    return False, "Error", f"Échec de 'git add {rel_act_file}': {err_add}"
                staged_anything = True

        commit_msg = cls.generate_smart_commit_message(
            repo_path=norm_path,
            style=commit_style,
            fallback_template=commit_template,
            ai_provider=ai_provider,
            ai_api_key=ai_api_key,
            ai_model=ai_model
        )

        if dry_run:
            return True, "Dry-Run", f"[DRY-RUN] Prêt à pousser sur '{branch}' (Message: '{commit_msg}'). Aucun push effectué."

        if staged_anything or has_local_changes:
            ok_commit, commit_res = cls.run_git_command(norm_path, ["commit", "-m", commit_msg])
            if not ok_commit and "nothing to commit" not in commit_res.lower():
                return False, "Error", f"Échec de 'git commit': {commit_res}"

        ok_push, push_res = cls.run_git_command(norm_path, ["push", "origin", branch])
        if not ok_push:
            return False, "Error", f"Échec de 'git push origin {branch}': {push_res}"

        return True, "Success", f"Commit & Push réussis sur 'origin/{branch}' ('{commit_msg}') !"
