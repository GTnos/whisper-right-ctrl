# Whisper Right Ctrl

[![Tests](https://github.com/GTnos/whisper-right-ctrl/actions/workflows/test.yml/badge.svg)](https://github.com/GTnos/whisper-right-ctrl/actions/workflows/test.yml)
[![Release](https://img.shields.io/github/v/release/GTnos/whisper-right-ctrl)](https://github.com/GTnos/whisper-right-ctrl/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 用 Right Ctrl，把 Whisper 變成 Windows 本機語音輸入

Whisper Right Ctrl 是一款為 Windows 11 設計的開源「按住說話」工具。

把游標放在 LINE、瀏覽器、Word、Notion、Obsidian 或其他文字欄位，按住鍵盤右側的 **Ctrl** 說話，放開後便會使用 `faster-whisper` 在本機辨識，轉成繁體中文並貼到游標位置。

### 為什麼做這個工具？

Windows 內建的 `Win + H` 不能替換成 Whisper，也需要使用 Microsoft 的語音辨識服務。這個工具提供另一個選擇：

- 錄音在記憶體中交給本機模型處理
- 支援 NVIDIA CUDA `float16` 加速
- 按住 Right Ctrl 錄音，放開後自動貼入
- OpenCC 自動轉換為繁體中文
- 可從工作列圖示直接切換麥克風
- 依麥克風名稱自動找回裝置，不受 Windows 重排編號影響
- 若目前的 Windows 音訊介面暫時失效，會自動嘗試同一支麥克風的其他介面
- 若 Windows 休眠後所有音訊介面都失效，會自動重新啟動並重建麥克風連線
- 每次啟動會實際檢查裝置，只在選單顯示能正常開啟的麥克風
- 同一支麥克風的重複 Windows 介面會合併成一個選項
- 可設定登入 Windows 後靜默啟動
- 不會留下黑色命令視窗
- 支援瀏覽器、通訊軟體、文件編輯器及筆記工具
- 原始碼、安裝流程與測試全部公開

### 快速開始

1. 前往 [Releases](https://github.com/GTnos/whisper-right-ctrl/releases/latest) 下載最新版 ZIP。
2. 解壓縮到固定資料夾。
3. 執行 `INSTALL.cmd`。
4. 從清單選擇正確的麥克風。
5. 首次啟動等待 `turbo` 模型下載完成。
6. 按住 Right Ctrl 說話，放開後等待文字出現。

若 v0.3.0 在重新開機後顯示 Windows Script Host `800A0408 無效的資料`，請下載 v0.3.1，解壓縮後重新執行 `INSTALL.cmd`；安裝程式會覆寫成 Windows Script Host 相容的登入啟動檔。

若要更換輸入裝置，請在工作列通知區的綠色麥克風圖示按滑鼠右鍵，開啟「Microphone」選單。選擇會立即生效並保存；下次登入時，即使 Windows 改變裝置編號，程式也會依名稱找回原本的麥克風。

啟動時會短暫檢查每個輸入裝置。無法使用的介面不會出現在選單，同一支實體麥克風也只會顯示一次；檢查過程不會儲存錄音。

> 預設設定以 NVIDIA GPU 為目標。參考測試硬體為 RTX 4060 Ti 16 GB。

### 適合情境

- 快速回覆 Email、LINE 與社群訊息
- 在 ChatGPT、Codex 或其他 AI 工具中用語音輸入提示
- 會議後補充筆記與工作事項
- 工地巡檢、設計討論及施工紀錄
- 長篇 Word、Notion 或 Obsidian 草稿
- 希望錄音不送到雲端的工作環境

### 隱私說明

模型下載完成後，語音轉文字在本機執行。本工具不會把錄音上傳到 OpenAI，也不會儲存錄音或逐字稿。首次安裝套件與下載模型時仍需要網路連線。

---

## English documentation

Local push-to-talk voice input for Windows 11, powered by `faster-whisper`.

Hold the keyboard's **Right Ctrl** key to record. Release it to transcribe, convert Chinese output to Traditional Chinese, and paste the result at the active caret.

## Highlights

- Local transcription after the model has been downloaded
- NVIDIA CUDA `float16` acceleration
- Right Ctrl push-to-talk
- Traditional Chinese conversion through OpenCC
- Works in browsers, chat applications, editors, Word, Notion, and Obsidian
- Hidden startup with no command window
- Restores the previous text clipboard after pasting
- Tray icon for ready, recording, transcribing, pause, and exit states
- Runtime microphone selection from the tray menu
- Automatic recovery when Windows changes a microphone's numeric device index
- Automatic fallback to another interface for the same microphone when the current Windows audio interface fails
- Automatic application restart when sleep invalidates every Windows audio interface
- Startup validation hides input devices that cannot actually open
- Duplicate interfaces with the same microphone name are collapsed into one menu choice

## Privacy

Audio is captured in memory and passed directly to the local transcription model. This application does not upload recordings to OpenAI.

The first launch downloads the selected Whisper-compatible model from its model host. Package installation also requires internet access. Review your network and model-host policies before use.

The project does not save microphone recordings or transcripts. Diagnostic logs and configuration are stored under:

`%LOCALAPPDATA%\WhisperRightCtrl`

## Requirements

- Windows 11
- Python 3.11, or the `uv` package manager with access to Python 3.11
- NVIDIA GPU with a compatible driver for the default CUDA configuration
- A working microphone
- Internet access during installation and first model download

The tested reference hardware is an NVIDIA RTX 4060 Ti 16 GB. Other supported NVIDIA GPUs may work. CPU mode can be selected manually in the configuration file, but is not the default release target.

## Installation

1. Download and extract the release ZIP to a permanent folder.
2. Double-click `INSTALL.cmd`.
3. Select the microphone number that receives your voice.
4. Wait for installation and tests to complete.
5. On first launch, allow time for the `turbo` model to download.

The installer creates a project-local `.venv` and a per-user Windows Startup entry. Administrator rights are not required for the Startup entry.

## Usage

1. Place the caret in a text field.
2. Hold **Right Ctrl** and speak.
3. Release **Right Ctrl**.
4. Wait for the recognized text to appear.

Tray colors:

- Green: ready
- Red: recording
- Orange: transcribing
- Gray: paused

Right-click the tray icon to pause or exit.

## Change the microphone

Run `CONFIGURE_MICROPHONE.cmd`, choose another microphone number, and restart the application from the tray.

The selected device and other settings are stored in:

`%LOCALAPPDATA%\WhisperRightCtrl\config.json`

Available settings include:

```json
{
  "input_device": 2,
  "language": "zh",
  "model": "turbo",
  "device": "cuda",
  "compute_type": "float16",
  "minimum_seconds": 0.25,
  "restore_clipboard": true
}
```

Device numbers can change after audio hardware or drivers are changed. Run microphone configuration again if recordings become silent.

## Troubleshooting

### The tray icon changes color but no text appears

Open the log:

`%LOCALAPPDATA%\WhisperRightCtrl\voice-input.log`

If the VAD reports that it removed the entire recording, select the correct microphone with `CONFIGURE_MICROPHONE.cmd`.

### The app does not start

Check the log for missing CUDA libraries, an invalid microphone, or model download errors. Re-run `INSTALL.cmd` to repair project-local packages.

### Secure or elevated applications

Windows may block input injection into an elevated application when Whisper Right Ctrl is running without elevation. Run both at the same integrity level.

## Uninstall

Run `UNINSTALL.cmd`. It removes automatic startup and stops the resident process. It deliberately leaves the extracted project, model cache, and local configuration in place so removal is recoverable.

Delete those folders manually if you also want to remove downloaded files.

## Build a release ZIP

The release builder creates its own validation environment if needed, installs the project, and runs the full test suite:

```text
BUILD_RELEASE.cmd
```

This runs the tests, scans the source tree for the original developer's personal path, excludes generated environments and logs, and creates a versioned ZIP under `dist`.

## Security notes

This tool globally observes the Right Ctrl key and uses the clipboard to paste recognized text. Review the source before use. Do not download unsigned release packages from untrusted mirrors.

## License

Project source code is available under the MIT License. Dependencies and downloaded models retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
