# Whisper Right Ctrl

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
