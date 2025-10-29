# Browser Extension + Background Service Architecture

## Overview

This document outlines how to repurpose the BeatChecker codebase into a background Python agent that exposes an API for a Chrome extension. The client-side extension injects UI into YouTube pages while the Python service performs downloads and analysis.

## Components

### 1. Background Python Service
- **Purpose:** Provide HTTP endpoints (e.g., `/analyze`) that accept YouTube URLs and return analysis results.
- **Framework:** FastAPI (preferred) or Flask for a lightweight REST interface.
- **State:** Runs headlessly with no Tk UI; manages downloads, tempo detection, and key detection.
- **Tray Integration:**
  - macOS: `rumps` or `pystray` to expose a minimal menu-bar app.
  - Windows: `pystray` to show a system tray icon.
  - Menu options can include “Start/Stop Service”, “Open Logs”, and “Quit”.
- **Startup:** Optional login item/service so it launches automatically at boot.

### 2. Chrome Extension Frontend
- **Content Script:** Injects a "Download & Analyze" button into YouTube’s watch page DOM.
- **Modal UI:** Displays progress, success (BPM + key), or errors using the response from the backend.
- **Background Script:** Handles API calls to the local service (`http://127.0.0.1:<port>`). Ensures requests include an auth token if required.
- **Permissions:** Needs host permission for `https://www.youtube.com/*` and the backend URL (`http://127.0.0.1/*`).

### 3. Shared Protocol
- **Request:** `POST /analyze` with JSON `{ "url": "https://www.youtube.com/watch?v=..." }`.
- **Response:** JSON `{ "bpm": 120, "key": "C# Minor", "file_path": "/path/to/mp3" }`.
- **Errors:** Standardized error payloads (HTTP 400 for validation failure, 500 for internal errors).

## Backend Notes
- Reuse existing modules: `download.py`, `analyze.py`, and supporting utilities.
- Add async endpoints for non-blocking operation (`FastAPI` plays nicely with `asyncio.to_thread`).
- Logging: store logs in `~/BeatChecker/logs` for inspection via the tray menu.
- Configuration: expose port, download directory, and FFmpeg path via `config.py` or environment variables.
- Security:
  - Bind to `127.0.0.1` by default to avoid exposing the service externally.
  - Optional API token/key passed via header (`Authorization: Bearer <token>`).

## Extension Notes
- Use manifest V3.
- Content script watches for dynamic page changes (YouTube SPA behavior) and reinjects the button when needed.
- Communication: `chrome.runtime.sendMessage` or `fetch` directly to the backend.
- Handle loading states and graceful error messages matching the desktop app tones.

## Packaging & Distribution
- **Backend:**
  - Bundle with PyInstaller (macOS `.app`/Windows `.exe`).
  - Include FFmpeg and yt-dlp binaries alongside the executable.
  - Provide installers or instructions for adding the agent to login/startup items.
- **Extension:**
  - Ship via Chrome Web Store or sideloaded `.crx`/unpacked dir.
  - Extension should detect if the local backend is offline and prompt the user to launch it.

## Legal & UX Considerations
- Clearly state that downloads rely on yt-dlp and may conflict with YouTube’s Terms of Service; include disclaimers in both the service and extension UI.
- Inform users that all processing stays local unless they configure a remote backend.
- Offer an option to delete downloaded files automatically after analysis to minimize storage.

## Next Steps
1. Create a FastAPI service (`src/service.py`) wrapping `download_youtube_audio` and `analyze_audio`.
2. Implement a tray application entry point that starts/stops the FastAPI server.
3. Prototype the Chrome extension content script and modal UI.
4. Define API error formats and authentication strategy.
5. Package the backend for macOS/Windows and document installation.
6. Iterate on UX (progress feedback, accessibility) once the pipeline is functional.
