# ClickerRecord
## Description
ClickerRecord is a Windows application that records mouse movements, clicks, and keyboard inputs, then plays them back. It features a modern, user-friendly, and multi-language interface.
## Key Features
- **Action Recording**: Records mouse movements, clicks, and key presses.
- **Action Playback**: Simulates recorded mouse and keyboard actions.
- **Repeat Last**: Quickly repeats the last recorded sequence (now used for Language selection).
- **Language Selection**: Supports multiple interface languages (English, Russian, German, French, Spanish, Italian, Chinese, Japanese, Turkish, Polish, Hebrew). Remembers the last used language.
- **Scheduling**: Set a schedule for automatic playback (run once, run at intervals, run at a specific time).
- **Repetition**: Specify the number of times to repeat the playback.
- **Save & Load**: Save recorded actions to `.clk` files and load them later.
- **Speed Adjustment**: Change the playback speed (faster/slower).
- **Stop Playback**: Interrupt playback at any time using the "Stop Playback" button or the Esc key.
## Installation
1. Download the latest release archive (e.g., `ClickerRecord_vX.X.zip`) from the [Releases page](link-to-your-releases-page-later).
2. Extract the archive to a convenient folder.
3. Run the `ClickerRecord.exe` file.
## Usage
### Recording Actions
1. Click the "Start Recording" button or press F6.
2. Perform the actions you want to record (mouse movements, clicks, key presses).
3. Click the "Stop Recording" button or press F6 again to finish recording.
### Playback
1. Set the desired repeat count.
2. Choose the schedule type:
   - "Run once" - Starts immediately.
   - "Run every X minutes" - Starts periodically after the specified interval.
   - "Run at" - Starts at the specified time.
3. Adjust the playback speed using the slider.
4. Click the "Play" button or press F7.
### Stopping Playback
- Click the "Stop Playback" button or press Esc at any time to interrupt playback.
### Language
- Click the "Language" button (or press F8) to open a dialog and select your preferred interface language. The selection will be saved for future sessions.
### Saving and Loading
- Click "Save Recording" (or Ctrl+S) to save the recorded actions to a `.clk` file.
- Click "Load Recording" (or Ctrl+O) to load previously saved actions.
## Hotkeys
- F6 - Start/Stop recording
- F7 - Start playback
- F8 - Open Language selection dialog
- Esc - Stop current playback
- Ctrl+S - Save recording
- Ctrl+O - Load recording
## System Requirements
- Windows 7/8/10/11
- Approx. 50-100 MB free disk space (for the application and recordings)
- Minimum 2 GB RAM
## Precautions
- Use the application cautiously, as it simulates mouse and keyboard input.
- Do not start playback if it could lead to unintended actions on your system.
- Always test recorded actions before scheduling automatic playback.
- Use the "Stop Playback" button or Esc key if playback needs to be interrupted immediately.
## Development Files
- `main.py` - Main application file with the GUI (using PyQt5).
- `recorder.py` - Module for recording user actions (using `pynput`).
- `player.py` - Module for playing back recorded actions (using `pynput`).
- `build_exe.py` - Script used to build the executable (using PyInstaller).
- `config.json` - Stores the last selected language (created automatically).
- `LICENSE` - Contains the software license.
- `README.md` - This file.
## Feedback
If you have suggestions for improving the program or find a bug, please report it (e.g., by creating an Issue on the GitHub repository page).
![image](https://github.com/user-attachments/assets/0b05c271-b565-4ca2-8d11-985ec25abcdd)
