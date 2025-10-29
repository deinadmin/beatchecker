"""Utility helpers for the BeatChecker application."""

from __future__ import annotations

import pathlib
import re
import shutil
import sys
import unicodedata
from urllib.parse import urlparse


__all__ = [
    "is_valid_youtube_url",
    "sanitize_filename",
    "ensure_directory",
    "find_ffmpeg_binary",
    "clean_directory",
]


def find_ffmpeg_binary() -> pathlib.Path | None:
    """Locate an ffmpeg executable bundled with the app or on PATH."""

    candidates: list[pathlib.Path] = []

    bundle_base = getattr(sys, "_MEIPASS", None)
    if bundle_base:
        base_path = pathlib.Path(bundle_base)
        candidates.append(base_path / "ffmpeg")
        candidates.append(base_path / "ffmpeg.exe")

    executable_dir = pathlib.Path(sys.executable).resolve().parent
    candidates.append(executable_dir / "ffmpeg")
    candidates.append(executable_dir / "ffmpeg.exe")

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        candidates.append(pathlib.Path(system_ffmpeg))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


YOUTUBE_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def is_valid_youtube_url(url: str) -> bool:
    """Return ``True`` when *url* looks like a valid YouTube link."""
    if not url:
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc.lower() not in YOUTUBE_HOSTS:
        return False
    if not parsed.path:
        return False
    return True


INVALID_FILENAME_PATTERN = re.compile(r"[^\w\-\. ]", re.UNICODE)
CONSECUTIVE_DOTS_PATTERN = re.compile(r"\.\.+")
WHITESPACE_PATTERN = re.compile(r"\s+")


def sanitize_filename(name: str, default: str = "audio") -> str:
    """Create a filesystem-safe filename derived from *name*.

    The resulting string omits illegal characters and normalizes unicode so the
    filename is portable across operating systems. If the sanitized result would
    be empty, *default* is returned instead.
    """
    if not name:
        return default

    normalized = unicodedata.normalize("NFKD", name)
    without_invalid = INVALID_FILENAME_PATTERN.sub("", normalized)
    without_dots = CONSECUTIVE_DOTS_PATTERN.sub(".", without_invalid)
    collapsed = WHITESPACE_PATTERN.sub(" ", without_dots).strip()

    return collapsed or default


def ensure_directory(directory: pathlib.Path) -> pathlib.Path:
    """Ensure *directory* exists and return the ``Path`` instance."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def clean_directory(directory: pathlib.Path) -> None:
    """Remove all files and subdirectories within *directory* if it exists."""

    if not directory.exists():
        return

    for entry in directory.iterdir():
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
        except OSError:
            # If removal fails, continue with best-effort cleanup.
            continue
