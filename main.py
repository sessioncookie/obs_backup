import json
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote


def setup_logging(backup_dir):
    backup_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=backup_dir / "backup_log.txt",
        level=logging.DEBUG,  # 使用 DEBUG 級別以記錄詳細信息
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )


def check_admin_privileges():
    import ctypes

    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def backup_plugins(backup_dir):
    """
    從同級目錄的 'obs安裝路徑.txt' 讀取 OBS 安裝根目錄，
    然後複製該路徑下的 'data' 與 'obs-plugins' 到備份目錄。
    """
    setup_logging(backup_dir)

    # 取得與腳本同一層的設定檔位置
    try:
        script_dir = Path(__file__).resolve().parent
    except NameError:
        # 在互動環境/打包環境時 __file__ 可能不存在，退而求其次用工作目錄
        script_dir = Path.cwd()

    cfg_path = script_dir / "obs安裝路徑.txt"
    if not cfg_path.exists():
        logging.error(f"找不到設定檔：{cfg_path}")
        print(f"❌ 找不到『obs安裝路徑.txt』，請把 OBS 根目錄寫在該檔案內並與程式放同一層")
        return

    # 讀取第一行非空白的路徑
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines()]
        path_str = next((ln for ln in lines if ln), "")
        # 去除可能的引號與展開 ~ 或環境變數
        path_str = path_str.strip().strip('"').strip("'")
        path_str = os.path.expanduser(os.path.expandvars(path_str))
    except Exception as e:
        logging.error(f"讀取設定檔失敗：{cfg_path}，錯誤：{e}")
        print(f"⚠ 無法讀取『obs安裝路徑.txt』：{e}")
        return

    obs_root = Path(path_str)
    if not obs_root.exists() or not obs_root.is_dir():
        logging.error(f"OBS 安裝路徑無效：{obs_root}")
        print(f"❌ OBS 安裝路徑無效或不存在：{obs_root}")
        return

    # 要複製的來源資料夾
    targets = ["data", "obs-plugins"]
    sources = []
    for name in targets:
        p = obs_root / name
        print(p)
        if p.exists() and p.is_dir():
            sources.append(p)
        else:
            logging.warning(f"找不到資料夾：{p}")
            print(f"⚠ 跳過，找不到：{p}")

    if not sources:
        print("⚠ 未找到可複製的資料夾（data / obs-plugins）")
        return

    plugins_backup_dir = backup_dir / "plugins"
    plugins_backup_dir.mkdir(parents=True, exist_ok=True)

    # 複製
    for src in sources:
        dest = plugins_backup_dir / src.name
        try:
            shutil.copytree(src, dest, dirs_exist_ok=True)
            logging.info(f"備份外掛與資料：{src} -> {dest}")
            print(f"✔ 已備份：{src} -> {dest}")
        except Exception as e:
            logging.error(f"備份失敗：{src} -> {dest}，錯誤：{e}")
            print(f"⚠ 備份失敗：{src} -> {dest}，錯誤：{e}")


def is_valid_source(path: str) -> bool:
    path = path.strip().replace("\\", "/")

    # 處理可能的 URL 格式
    if path.startswith("file://"):
        # 將 file:// URL 轉為本地路徑
        parsed = urlparse(path)
        path = unquote(parsed.path)
        if os.name == "nt" and path.startswith("/"):  # Windows 路徑修正
            path = path[1:]

    src_path = Path(path)

    # 檢查檔案是否存在且是檔案
    if src_path.exists() and src_path.is_file():
        logging.debug(f"有效資源路徑: {path}")
        return True
    else:
        logging.debug(f"無效資源路徑: {path} (不存在或非檔案)")
        return False


def replace_paths_in_json(data, file_copy_map):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str):
                # 處理可能的 file:// URL
                original_v = v
                if v.startswith("file://"):
                    parsed = urlparse(v)
                    v = unquote(parsed.path)
                    if os.name == "nt" and v.startswith("/"):
                        v = v[1:]
                if v in file_copy_map:
                    data[k] = file_copy_map[v]
                else:
                    # 恢復原始值，避免修改非本地路徑
                    data[k] = original_v
            else:
                replace_paths_in_json(v, file_copy_map)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, str):
                original_item = item
                if item.startswith("file://"):
                    parsed = urlparse(item)
                    item = unquote(parsed.path)
                    if os.name == "nt" and item.startswith("/"):
                        item = item[1:]
                if item in file_copy_map:
                    data[i] = file_copy_map[item]
                else:
                    data[i] = original_item
            else:
                replace_paths_in_json(item, file_copy_map)
    return data


def backup_scenes_and_sources(backup_dir):
    setup_logging(backup_dir)
    user_home = Path.home()
    possible_paths = [
        user_home / "AppData/Roaming/obs-studio/basic/scenes",
        user_home / "Library/Application Support/obs-studio/basic/scenes",
        Path("/etc/obs-studio/basic/scenes"),
    ]
    print("-------------------------------------------------")
    print(possible_paths)
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
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"無法讀取 JSON 檔案: {file}, 錯誤: {e}")
            print(f"⚠ 無法讀取 JSON 檔案: {file}")
            continue

        def collect_sources(node, valid_keys={"file", "path", "local_file", "url"}):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in valid_keys and isinstance(v, str):
                        logging.debug(f"檢測到資源鍵: {k}, 路徑: {v}")
                        if is_valid_source(v):
                            src_path = Path(v)
                            if v.startswith("file://"):
                                parsed = urlparse(v)
                                src_path = Path(unquote(parsed.path))
                                if os.name == "nt" and src_path.parts[0].startswith("/"):
                                    src_path = Path(*src_path.parts[1:])
                            normalized_src = str(src_path).replace("\\", "/")
                            if normalized_src not in file_copy_map:
                                new_name = src_path.name
                                new_path = sources_backup_dir / new_name
                                counter = 1
                                while new_path.exists() and new_path != src_path:
                                    new_name = f"{src_path.stem}_{counter}{src_path.suffix}"
                                    new_path = sources_backup_dir / new_name
                                    counter += 1

                                try:
                                    shutil.copy2(src_path, new_path)
                                    logging.info(f"複製素材: {src_path} -> {new_path}")
                                    print(f"✔ 複製: {src_path} -> {new_path}")
                                    normalized_dst = str(new_path).replace("\\", "/")
                                    file_copy_map[normalized_src] = normalized_dst
                                except Exception as e:
                                    logging.error(
                                        f"複製素材失敗: {src_path} -> {new_path}, 錯誤: {e}"
                                    )
                                    print(f"⚠ 複製素材失敗: {src_path}")
                    else:
                        collect_sources(v, valid_keys)
            elif isinstance(node, list):
                for item in node:
                    collect_sources(item, valid_keys)

        collect_sources(data)
        new_data = replace_paths_in_json(data, file_copy_map)

        try:
            with open(scenes_backup_dir / file.name, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
                logging.info(f"備份場景檔案: {file} -> {scenes_backup_dir / file.name}")
        except Exception as e:
            logging.error(f"寫入場景檔案失敗: {scenes_backup_dir / file.name}, 錯誤: {e}")
            print(f"⚠ 寫入場景檔案失敗: {file}")

    try:
        with open(backup_dir / "source_map.json", "w", encoding="utf-8") as f:
            json.dump(file_copy_map, f, indent=2, ensure_ascii=False)
            logging.info("生成素材對應表: source_map.json")
    except Exception as e:
        logging.error(f"寫入素材對應表失敗: source_map.json, 錯誤: {e}")
        print("⚠ 寫入素材對應表失敗")


def main():
    print("是否開始備份 OBS 場景和素材？(y/n)")
    response = input().strip().lower()
    if response != "y":
        print("❌ 備份已取消")
        return

    backup_root = Path.cwd() / "obs_backup"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"backup_{timestamp}"

    backup_scenes_and_sources(backup_dir)

    print("是否備份 OBS 外掛？（需要管理員權限）(y/n)")
    response = input().strip().lower()
    if response == "y":
        backup_plugins(backup_dir)

    print(f"\n✅ 備份完成，儲存於：{backup_dir}")


if __name__ == "__main__":
    main()
    input("按 Enter 鍵結束...")
