# OBS Backup Tool

## 概述

**OBS Backup Tool** 是一個簡單易用的 Python 工具，用於備份 [OBS Studio](https://obsproject.com/) 的場景設定、素材檔案（圖片、音頻、視頻等）以及外掛。無論你是需要將 OBS 配置遷移到新電腦，還是想保存設定以防意外丟失，這個工具都能幫助你快速完成備份。

### 功能
- **備份場景設定**：自動備份 OBS 的場景 JSON 檔案。
- **備份素材檔案**：複製場景中使用的多媒體檔案（如圖片、音頻、視頻）。
- **備份外掛**：複製 OBS 的外掛目錄（需要管理員權限）。
- **跨平台支持**：支持 Windows、macOS 和 Linux（部分路徑需手動調整）。
- **用戶友好**：使用圖形介面（基於 Tkinter）提供確認提示和錯誤訊息。
- **日誌記錄**：記錄所有備份操作，方便排查問題。

## 系統要求
- **作業系統**：Windows 10/11、macOS 或 Linux
- **Python 版本**：Python 3.8 或更高版本（如果運行原始碼）
- **OBS Studio**：已安裝並配置過場景
- **管理員權限**：備份外掛時需要（Windows）

## 安裝

### 選項 1：運行可執行檔案
1. 從 [發布頁面](#)（或提供的下載連結）下載最新版本的 `obs_backup.exe`。
2. 將執行檔放置在你希望儲存備份的目錄。
3. 雙擊運行 `obs_backup.exe`。

**注意**：部分防毒軟體可能會誤將可執行檔案標記為威脅（詳見[防毒誤判說明](#防毒誤判說明)）。請將程式加入防毒軟體的例外清單。

### 選項 2：運行原始碼
1. 安裝 Python 3.8 或更高版本（從 [python.org](https://www.python.org/) 下載）。
2. 下載本倉庫的原始碼：
   ```bash
   git clone <倉庫地址>
   cd obs-backup-tool
   ```
3. 運行程式：
   ```bash
   python obs_backup.py
   ```

**依賴**：本程式使用 Python 標準庫（`json`, `os`, `shutil`, `pathlib`, `datetime`, `logging`, `tkinter`），無需額外安裝第三方模組。

## 使用方法

1. **啟動程式**：
   - 如果使用可執行檔案，雙擊 `obs_backup.exe`。
   - 如果使用原始碼，運行 `python obs_backup.py`。

2. **確認備份**：
   - 程式會彈出一個確認視窗，詢問是否開始備份 OBS 場景、素材和外掛。
   - 點擊「是」繼續，或「否」取消。

3. **選擇外掛備份**：
   - 如果選擇備份外掛，程式會檢查管理員權限並提示是否繼續。
   - 外掛備份需要管理員權限，否則會跳過此步驟。

4. **備份結果**：
   - 備份完成後，程式會顯示備份儲存的路徑（預設為當前目錄下的 `obs_backup/backup_YYYYMMDD_HHMMSS`）。
   - 備份內容包括：
     - `scenes/`：場景 JSON 檔案。
     - `sources/`：素材檔案。
     - `plugins/`：外掛目錄（如果選擇備份）。
     - `source_map.json`：素材路徑對應表。
     - `backup_log.txt`：備份操作日誌。

5. **檢查日誌**：
   - 打開 `backup_log.txt` 查看備份過程的詳細記錄，包括成功的操作和任何錯誤。

## 防毒誤判說明

由於本程式使用 PyInstaller 打包成可執行檔案，某些防毒軟體（例如 Windows Defender、Zillya、Bkav）可能會誤將其標記為「木馬」或「可疑檔案」。這是因為：

- PyInstaller 打包的執行檔具有壓縮和動態解壓行為，與某些惡意軟體相似。
- 可執行檔案未使用商業數位簽名（需要購買憑證）。
- 程式涉及檔案操作（複製設定和素材），可能觸發啟發式檢測。

### 解決誤判的方法
1. **驗證檔案安全**：
   - 檢查可執行檔案的 VirusTotal 報告（由作者提供，或自行上傳到 [virustotal.com](https://www.virustotal.com/)）。
   - 檢視原始碼（`obs_backup.py`），確認其安全性。

2. **添加防毒例外**：
   - **Windows Defender**：
     1. 打開「Windows 安全性」 > 「病毒與威脅防護」 > 「管理設定」 > 「排除」。
     2. 添加 `obs_backup.exe` 或其所在資料夾。
   - 其他防毒軟體：參考其官方說明添加例外。

3. **運行原始碼**：
   - 如果不信任可執行檔案，直接運行 Python 原始碼（見[安裝](#安裝)）。

4. **聯繫作者**：
   - 如果仍有疑慮，請聯繫作者（見[聯繫方式](#聯繫方式)），獲取更多資訊或誤判報告狀態。

**聲明**：本程式已由作者測試，確認無惡意行為。所有檔案操作均需用戶確認，且日誌記錄公開透明。

## 常見問題

### 1. 程式提示「找不到 OBS 場景設定路徑」
- 確保 OBS Studio 已安裝並至少配置過一個場景。
- 檢查以下路徑是否存在：
  - Windows：`%APPDATA%\obs-studio\basic\scenes`
  - macOS：`~/Library/Application Support/obs-studio/basic/scenes`
  - Linux：`/etc/obs-studio/basic/scenes`
- 如果路徑不同，請修改程式碼中的 `possible_paths` 列表。

### 2. 備份外掛失敗
- 備份外掛需要管理員權限。請右鍵點擊 `obs_backup.exe`，選擇「以管理員身份運行」。
- 確保 OBS 外掛目錄存在（例如 `C:\Program Files\obs-studio\obs-plugins` 或 `%APPDATA%\obs-studio\plugins`）。

### 3. 防毒軟體阻止程式運行
- 參考[防毒誤判說明](#防毒誤判說明)，將程式加入例外。
- 聯繫作者獲取最新的 VirusTotal 報告或誤判解決進度。

## 貢獻
歡迎提交問題或改進建議！請：
1. Fork 本倉庫。
2. 創建你的功能分支（`git checkout -b feature/YourFeature`）。
3. 提交你的更改（`git commit -m 'Add YourFeature'`）。
4. 推送到分支（`git push origin feature/YourFeature`）。
5. 開啟一個 Pull Request。

## 聯繫方式
- **作者**：Your Name
- **電子郵件**：your.email@example.com
- **GitHub**：[@yourusername](https://github.com/yourusername)
- **問題回報**：請在 GitHub 倉庫提交 [Issue](<倉庫地址>/issues)

## 授權
本程式基於 [MIT 授權](LICENSE) 發布。你可以自由使用、修改和分發，但請保留原作者資訊。

---

感謝使用 OBS Backup Tool！如果有任何問題，請隨時聯繫。
