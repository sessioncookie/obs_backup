import json
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# 可識別的素材副檔名
VALID_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".mp4", ".mp3", ".mov", ".wav", ".webm", ".mkv", ".flv", ".html",
}

def setup_logging(backup_dir):
    # Ensure backup_dir exists before configuring logging
    backup_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=backup_dir / "backup_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )

def check_admin_privileges():
    import ctypes
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def backup_plugins(backup_dir):
    if not check_admin_privileges():
        logging.warning("備份外掛需要管理員權限，跳過外掛備份")
        print("⚠ 備份外掛需要管理員權限，請以管理員身份重新運行程式")
        return

    setup_logging(backup_dir)
    plugin_dirs = []
    program_files_plugins = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "obs-studio" / "obs-plugins"
    appdata_plugins = Path.home() / "AppData/Roaming/obs-studio/plugins"
    if program_files_plugins.exists():
        plugin_dirs.append(program_files_plugins)
    if appdata_plugins.exists():
        plugin_dirs.append(appdata_plugins)

    plugins_backup_dir = backup_dir / "plugins"
    plugins_backup_dir.mkdir(parents=True, exist_ok=True)

    for plugin_dir in plugin_dirs:
        dest = plugins_backup_dir / plugin_dir.name
        try:
            shutil.copytree(plugin_dir, dest, dirs_exist_ok=True)
            logging.info(f"備份外掛: {plugin_dir} -> {dest}")
            print(f"✔ 備份外掛: {plugin_dir} -> {dest}")
        except Exception as e:
            logging.error(f"備份外掛失敗: {plugin_dir}, 錯誤: {e}")
            print(f"⚠ 備份外掛失敗: {plugin_dir}, 錯誤: {e}")

def is_valid_source(path: str) -> bool:
    path = path.strip().replace("\\", "/")
    suffix = Path(path).suffix.lower()
    return suffix in VALID_EXTENSIONS and path.count("/") >= 2

def replace_paths_in_json(data, file_copy_map):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str) and v in file_copy_map:
                data[k] = file_copy_map[v]
            else:
                replace_paths_in_json(v, file_copy_map)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, str) and item in file_copy_map:
                data[i] = file_copy_map[item]
            else:
                replace_paths_in_json(item, file_copy_map)
    return data

def backup_scenes_and_sources(backup_dir):
    setup_logging(backup_dir)
    user_home = Path.home()
    possible_paths = [
        user_home / "AppData/Roaming/obs-studio/basic/scenes",
        user_home / "Library/Application Support/obs-studio/basic/scenes",  # macOS
        Path("/etc/obs-studio/basic/scenes"),  # Linux
    ]

    scene_path = next((p for p in possible_paths if p.exists()), None)
    if not scene_path:
        logging.error("找不到 OBS 場景設定路徑")
        print("❌ 找不到 OBS 場景設定路徑")
        return

    scenes_backup_dir = backup_dir / "scenes"
    sources_backup_dir = backup_dir / "sources"
    scenes_backup_dir.mkdir(parents=True, exist_ok=True)
    sources_backup_dir.mkdir(parents=True, exist_ok=True)

    file_copy_map = {}

    for file in scene_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        def collect_sources(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(v, str) and is_valid_source(v):
                        src_path = Path(v)
                        normalized_src = str(src_path).replace("\\", "/")
                        if src_path.exists():
                            if normalized_src not in file_copy_map:
                                new_name = src_path.name
                                new_path = sources_backup_dir / new_name
                                counter = 1
                                while new_path.exists() and new_path != src_path:
                                    new_name = f"{src_path.stem}_{counter}{src_path.suffix}"
                                    new_path = sources_backup_dir / new_name
                                    counter += 1

                                if new_path != src_path:
                                    shutil.copy2(src_path, new_path)
                                    logging.info(f"複製素材: {src_path} -> {new_path}")
                                    print(f"✔ 複製: {src_path} -> {new_path}")

                                normalized_dst = str(new_path).replace("\\", "/")
                                file_copy_map[normalized_src] = normalized_dst
                    else:
                        collect_sources(v)
            elif isinstance(node, list):
                for item in node:
                    collect_sources(item)

        collect_sources(data)
        new_data = replace_paths_in_json(data, file_copy_map)

        with open(scenes_backup_dir / file.name, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            logging.info(f"備份場景檔案: {file} -> {scenes_backup_dir / file.name}")

    with open(backup_dir / "source_map.json", "w", encoding="utf-8") as f:
        json.dump(file_copy_map, f, indent=2, ensure_ascii=False)
        logging.info("生成素材對應表: source_map.json")

def main():
    root = tk.Tk()
    root.withdraw()
    if not messagebox.askyesno("確認備份", "是否開始備份 OBS 場景、素材和外掛？"):
        print("❌ 備份已取消")
        return

    backup_root = Path.cwd() / "obs_backup"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"backup_{timestamp}"

    backup_scenes_and_sources(backup_dir)
    if messagebox.askyesno("外掛備份", "是否備份 OBS 外掛？（需要管理員權限）"):
        backup_plugins(backup_dir)

    messagebox.showinfo("完成", f"備份已完成，儲存於：{backup_dir}")
    print(f"\n✅ 備份完成，儲存於：{backup_dir}")

if __name__ == "__main__":
    main()
    input("按 Enter 鍵結束...")