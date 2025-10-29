# Product Requirements Document (PRD)
## BeatChecker - YouTube Beat Analysis Tool

---

## 1. Executive Summary

**Product Name:** BeatChecker  
**Version:** 1.0.0  
**Platform:** Desktop Application (macOS & Windows)  
**Tech Stack:** Python + CustomTkinter  
**Target Users:** Musicians, producers, rappers who work with YouTube beats

### Purpose
A local desktop application that downloads YouTube beats, analyzes their musical properties (BPM and Key), and presents the results in a user-friendly interface.

---

## 2. Goals & Objectives

### Primary Goals
- Download YouTube audio as high-quality MP3 (320kbps)
- Accurately detect BPM (Beats Per Minute)
- Detect musical key with confidence percentage
- Provide smooth, modern UI with loading states
- Run 100% locally (no server dependencies)
- Work cross-platform (macOS & Windows)

### Success Criteria
- BPM detection accuracy within ±2 BPM
- Key detection with confidence score displayed
- Download completion within 30-60 seconds for typical beats
- Clean, intuitive UI requiring no documentation
- Zero crashes on valid YouTube URLs

---

## 3. Technical Stack

### Core Framework
- **Python 3.9+** - Main programming language
- **CustomTkinter** - Modern UI framework for desktop GUI

### Key Libraries

| Library | Version | Purpose |
|:---|:---|:---|
| `customtkinter` | Latest | Modern, cross-platform GUI |
| `yt-dlp` | Latest | YouTube audio download |
| `librosa` | Latest | Audio analysis (BPM detection) |
| `essentia-tensorflow` | Latest | Key detection with ML |
| `soundfile` | Latest | Audio file I/O |
| `numpy` | Latest | Numerical operations |
| `mutagen` | Latest | Audio metadata handling |

### External Dependencies
- **FFmpeg** - Audio format conversion (required by yt-dlp)

---

## 4. Features & Requirements

### 4.1 Core Features

#### Feature 1: YouTube URL Input
**Description:** User enters YouTube URL for beat download  
**Requirements:**
- Single-line text input field
- Placeholder text: "Enter YouTube URL here..."
- Input validation (basic URL format check)
- Clear/reset button to empty field

#### Feature 2: Download & Convert
**Description:** Download audio from YouTube and convert to MP3  
**Requirements:**
- Use yt-dlp to extract audio
- Convert to MP3 format at 320kbps quality
- Save to local `downloads/` directory
- Filename: Sanitized video title + `.mp3`
- Handle errors gracefully (invalid URL, network issues, age-restricted videos)

#### Feature 3: BPM Detection
**Description:** Analyze tempo of downloaded beat  
**Requirements:**
- Use librosa's `beat_track()` function
- Display BPM rounded to 2 decimal places
- Typical range: 60-180 BPM for most beats
- Handle edge cases (no clear tempo, variable tempo)

#### Feature 4: Key Detection
**Description:** Detect musical key with confidence score  
**Requirements:**
- Use Essentia's `KeyExtractor` with EDMA algorithm
- Display key in format: `C# Minor`, `D Major`, etc.
- Show confidence as percentage (0-100%)
- If confidence < 50%, show warning icon
- Key format: Note name + Major/Minor (capitalized)

#### Feature 5: Loading States
**Description:** Visual feedback during processing  
**Requirements:**
- Loading screen/overlay when analysis starts
- Progress indicators:
  - "⏳ Downloading..." (during download)
  - "🎵 Analyzing..." (during BPM/Key detection)
  - "✅ Complete!" (when finished)
- Spinning loader animation
- Disable input during processing
- Estimated time remaining (optional, nice-to-have)

#### Feature 6: Results Display
**Description:** Show analysis results in clear format  
**Requirements:**
- BPM display: Large, bold number + "BPM" label
- Key display: Key name + confidence percentage
- Color coding:
  - Green if confidence > 80%
  - Yellow if confidence 50-80%
  - Orange if confidence < 50%
- Option to copy results to clipboard
- Option to analyze another beat (clear results)

---

## 5. Application Architecture

### 5.1 File Structure
```
beatchecker/
├── venv/                      # Virtual environment (not in git)
├── downloads/                 # Downloaded MP3 files
├── src/
│   ├── __init__.py
│   ├── app.py                 # Main application & GUI
│   ├── download.py            # YouTube download logic
│   ├── analyze.py             # BPM & Key detection
│   ├── utils.py               # Helper functions
│   └── config.py              # Configuration constants
├── assets/                    # UI assets (icons, images)
│   └── icon.png
├── requirements.txt           # Python dependencies
├── .gitignore
└── README.md
```

### 5.2 Module Breakdown

#### `app.py` - Main Application
**Responsibilities:**
- Create CustomTkinter window
- Build UI layout
- Handle button clicks
- Manage threading for async operations
- Update UI with results

**Key Classes:**
```python
class BeatCheckerApp(ctk.CTk):
    - __init__(): Setup window and widgets
    - create_widgets(): Build UI components
    - start_analysis(): Trigger download & analysis
    - update_loading_state(message): Update loading UI
    - display_results(results): Show BPM & Key
    - clear_results(): Reset for new analysis
```

#### `download.py` - YouTube Download
**Responsibilities:**
- Configure yt-dlp options
- Download audio from YouTube
- Convert to MP3
- Handle errors and exceptions

**Key Functions:**
```python
def download_youtube_audio(url: str, output_dir: str = 'downloads') -> str:
    """
    Downloads YouTube audio as MP3.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save MP3
    
    Returns:
        Absolute path to downloaded MP3 file
    
    Raises:
        ValueError: Invalid URL
        DownloadError: Download failed
    """
```

#### `analyze.py` - Audio Analysis
**Responsibilities:**
- Load audio file
- Detect BPM using librosa
- Detect key using Essentia
- Return structured results

**Key Functions:**
```python
def detect_bpm(audio_path: str) -> float:
    """Detect BPM using librosa beat tracking."""

def detect_key(audio_path: str) -> dict:
    """
    Detect musical key using Essentia.
    
    Returns:
        {
            'key': str,        # e.g., "C# Minor"
            'confidence': float  # 0-100%
        }
    """

def analyze_audio(audio_path: str) -> dict:
    """
    Full analysis: BPM + Key.
    
    Returns:
        {
            'bpm': float,
            'key': str,
            'key_confidence': float,
            'file_path': str
        }
    """
```

#### `utils.py` - Helper Functions
**Responsibilities:**
- URL validation
- File sanitization
- Error formatting
- Clipboard operations

#### `config.py` - Configuration
**Constants:**
```python
WINDOW_TITLE = "BeatChecker"
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 500
MP3_QUALITY = "320"
DOWNLOAD_TIMEOUT = 300  # seconds
MIN_KEY_CONFIDENCE = 50  # percentage
```

---

## 6. UI/UX Specifications

### 6.1 Window Configuration
- **Size:** 700x500 pixels (fixed, not resizable initially)
- **Title:** "BeatChecker"
- **Theme:** Dark mode (CustomTkinter default)
- **Colors:**
  - Primary: Blue (#1F6AA5)
  - Success: Green (#2CC985)
  - Warning: Orange (#FF9500)
  - Error: Red (#FF3B30)

### 6.2 Layout Structure

```
┌─────────────────────────────────────────────────────┐
│                   BeatChecker                      │
├─────────────────────────────────────────────────────┤
│                                                       │
│   ┌─────────────────────────────────────────────┐  │
│   │  Enter YouTube URL here...                  │  │
│   └─────────────────────────────────────────────┘  │
│                                                       │
│              [ Analyze Beat ]                        │
│                                                       │
│   ┌─────────────────────────────────────────────┐  │
│   │            Loading State Area                │  │
│   │        (shows during processing)             │  │
│   └─────────────────────────────────────────────┘  │
│                                                       │
│   ┌─────────────────────────────────────────────┐  │
│   │           RESULTS DISPLAY                    │  │
│   │                                               │  │
│   │     BPM: 140.5 BPM                           │  │
│   │                                               │  │
│   │     Key: C# Minor (87% confidence)           │  │
│   │                                               │  │
│   └─────────────────────────────────────────────┘  │
│                                                       │
│              [ Analyze Another ]                     │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 6.3 Widget Specifications

#### URL Input Field
- **Type:** CTkEntry
- **Width:** 500px
- **Height:** 40px
- **Font:** 14px
- **Padding:** 20px top margin

#### Analyze Button
- **Type:** CTkButton
- **Width:** 200px
- **Height:** 45px
- **Text:** "Analyze Beat"
- **Color:** Primary blue
- **Hover:** Slightly darker blue

#### Loading Display
- **Type:** CTkLabel with CTkProgressBar
- **Messages:**
  - "⏳ Downloading beat..."
  - "🎵 Analyzing audio..."
  - "✅ Analysis complete!"
- **Progress Bar:** Indeterminate mode

#### Results Display
- **BPM Label:**
  - Font size: 32px bold
  - Format: "{bpm} BPM"
  - Color: White
  
- **Key Label:**
  - Font size: 24px
  - Format: "{key} ({confidence}% confidence)"
  - Color: Dynamic based on confidence

---

## 7. Implementation Details

### 7.1 Download Configuration

```python
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}
```

### 7.2 BPM Detection Algorithm

```python
def detect_bpm(audio_path):
    # Load audio
    y, sr = librosa.load(audio_path, sr=22050)
    
    # Detect tempo
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    
    # Return as float
    return float(tempo)
```

### 7.3 Key Detection Algorithm

```python
def detect_key(audio_path):
    from essentia.standard import MonoLoader, KeyExtractor
    
    # Load audio
    audio = MonoLoader(filename=audio_path)()
    
    # Extract key
    key_extractor = KeyExtractor()
    key, scale, strength = key_extractor(audio)
    
    # Format output
    key_name = f"{key} {scale.capitalize()}"
    confidence = round(strength * 100, 2)
    
    return {
        'key': key_name,
        'confidence': confidence
    }
```

### 7.4 Threading for Non-Blocking UI

**Critical:** Use threading to prevent UI freeze during download/analysis

```python
import threading

def start_analysis(self):
    url = self.url_entry.get()
    
    # Run in separate thread
    thread = threading.Thread(target=self.analyze_audio, args=(url,))
    thread.daemon = True
    thread.start()

def analyze_audio(self, url):
    try:
        # Download
        self.update_ui("⏳ Downloading...")
        audio_file = download_youtube_audio(url)
        
        # Analyze
        self.update_ui("🎵 Analyzing...")
        results = analyze_audio(audio_file)
        
        # Display
        self.update_ui("✅ Complete!")
        self.show_results(results)
    except Exception as e:
        self.show_error(str(e))
```

---

## 8. Error Handling

### Error Categories

| Error Type | Handling Strategy |
|:---|:---|
| Invalid URL | Show error message: "Please enter a valid YouTube URL" |
| Network Error | "Unable to download. Check your internet connection." |
| Age-Restricted Video | "This video cannot be downloaded (age-restricted)" |
| Private/Deleted Video | "Video not found or unavailable" |
| Analysis Failed | "Could not analyze audio. File may be corrupted." |
| No FFmpeg | "FFmpeg not found. Please install FFmpeg." |

### Implementation
```python
try:
    # Download and analyze
except yt_dlp.utils.DownloadError as e:
    show_error("Download failed. Check URL and internet connection.")
except Exception as e:
    show_error(f"Unexpected error: {str(e)}")
finally:
    # Always re-enable UI
    self.enable_input()
```

---

## 9. Dependencies Installation

### requirements.txt
```
customtkinter>=5.2.0
yt-dlp>=2023.10.13
librosa>=0.10.0
essentia-tensorflow>=2.1b6
soundfile>=0.12.1
numpy>=1.24.0
mutagen>=1.47.0
```

### Installation Instructions
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg
# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

---

## 10. Testing Requirements

### Unit Tests
- `test_download.py` - Test YouTube download with various URLs
- `test_analyze.py` - Test BPM/Key detection with sample files
- `test_utils.py` - Test helper functions

### Test Cases

| Test | Input | Expected Output |
|:---|:---|:---|
| Valid YouTube URL | Standard beat video | MP3 file + BPM + Key |
| Invalid URL | "not-a-url" | Error message displayed |
| Private video | Private YouTube URL | "Video unavailable" error |
| Sample MP3 (140 BPM) | Test file | BPM: ~140 ± 2 |
| Sample MP3 (C Major) | Test file | Key: C Major, confidence > 70% |

---

## 11. Constraints & Limitations

### Technical Constraints
- Requires FFmpeg installation (not bundled)
- Key detection is probabilistic (not 100% accurate)
- Download speed depends on internet connection
- Large files (>100MB) may take longer to analyze

### Legal Constraints
- Users responsible for copyright compliance
- YouTube Terms of Service: Don't encourage violation
- Add disclaimer in app about proper usage

### Platform Constraints
- Python 3.9+ required
- macOS 10.14+ or Windows 10+
- Minimum 4GB RAM recommended
- 500MB free disk space for downloads

---

## 12. Future Enhancements (Phase 2)

**Not in initial version, but consider for later:**
- Playlist support (analyze multiple beats)
- Export results to JSON/CSV
- History of analyzed beats
- Audio waveform visualization
- Chord progression detection
- Multiple key suggestions (top 3)
- Drag & drop local audio files
- Integration with DAWs (Ableton, FL Studio)

---

## 13. Success Metrics

**Version 1.0 is successful if:**
- ✅ Successfully downloads 95%+ of valid YouTube URLs
- ✅ BPM detection within ±3 BPM of manual verification
- ✅ Key detection confidence >70% for most beats
- ✅ UI remains responsive (no freezing)
- ✅ Works on both macOS and Windows
- ✅ Zero data sent to external servers (100% local)

---

## 14. Development Timeline

| Phase | Duration | Deliverables |
|:---|:---|:---|
| Setup & Dependencies | 1 day | Virtual env, libraries installed |
| Download Module | 1 day | Working YouTube download |
| Analysis Module | 2 days | BPM + Key detection |
| UI Implementation | 2 days | Complete GUI with CustomTkinter |
| Integration & Testing | 2 days | Connect all parts, handle errors |
| Polish & Documentation | 1 day | README, comments, final testing |
| **Total** | **~9 days** | **Production-ready v1.0** |

---

## 15. Code Quality Standards

### Requirements
- Type hints for all function parameters
- Docstrings for all public functions
- PEP 8 compliance
- Error handling for all external calls
- No hardcoded paths (use config)
- Logging for debugging (optional but recommended)

### Example Function
```python
def download_youtube_audio(url: str, output_dir: str = 'downloads') -> str:
    """
    Download audio from YouTube and convert to MP3.
    
    Args:
        url: Valid YouTube video URL
        output_dir: Directory to save MP3 file (default: 'downloads')
    
    Returns:
        Absolute path to downloaded MP3 file
    
    Raises:
        ValueError: If URL is invalid or empty
        DownloadError: If download fails
        
    Example:
        >>> path = download_youtube_audio('https://youtube.com/watch?v=...')
        >>> print(path)
        '/path/to/downloads/Beat Name.mp3'
    """
    # Implementation
```

---

## 16. Deployment

### Packaging (Future)
For distribution to non-technical users:
- **PyInstaller** - Create standalone executable
- **py2app** (macOS) - Create .app bundle
- **cx_Freeze** (Windows) - Create .exe installer

### Initial Deployment (v1.0)
- GitHub repository with clear README
- Installation instructions
- Sample screenshots/GIF demo
- Troubleshooting guide

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-25  
**Status:** Ready for Development

