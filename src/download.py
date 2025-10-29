"""YouTube download utilities for BeatChecker."""

from __future__ import annotations

import pathlib
import typing as t

import yt_dlp
from yt_dlp.utils import DownloadError as YTDLPDownloadError

from . import config
from .utils import (
    clean_directory,
    ensure_directory,
    find_ffmpeg_binary,
    is_valid_youtube_url,
    sanitize_filename,
)

__all__ = ["DownloadError", "download_youtube_audio"]


class DownloadError(RuntimeError):
    """Raised when downloading or converting audio fails."""

FFMPEG_BINARY = find_ffmpeg_binary()


def _build_options(output_path: pathlib.Path) -> dict[str, t.Any]:
    """Return yt-dlp configuration for saving MP3 to *output_path*."""
    output_template = f"{output_path.with_suffix('')}.%(ext)s"
    options = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": config.MP3_QUALITY,
            }
        ],
    }

    if FFMPEG_BINARY is not None:
        options["ffmpeg_location"] = str(FFMPEG_BINARY)

    return options


def _make_unique_path(directory: pathlib.Path, stem: str, suffix: str) -> pathlib.Path:
    """Return a unique path inside *directory* using *stem* and *suffix*."""
    candidate = directory / f"{stem}{suffix}"
    index = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{index}{suffix}"
        index += 1
    return candidate


def _extract_download_filepath(info: t.Any) -> pathlib.Path | None:
    """Return the first filepath reported by yt-dlp for the downloaded media."""
    if isinstance(info, dict):
        requested_downloads = info.get("requested_downloads")
        if isinstance(requested_downloads, list):
            for entry in requested_downloads:
                filepath = entry.get("filepath") if isinstance(entry, dict) else None
                if filepath:
                    return pathlib.Path(filepath)

        filename = info.get("_filename")
        if filename:
            return pathlib.Path(filename)

        entries = info.get("entries")
        if isinstance(entries, list):
            for entry in entries:
                nested = _extract_download_filepath(entry)
                if nested is not None:
                    return nested

    if isinstance(info, list):
        for entry in info:
            nested = _extract_download_filepath(entry)
            if nested is not None:
                return nested

    return None


def _unique_paths(paths: t.Iterable[pathlib.Path | None]) -> list[pathlib.Path]:
    """Return *paths* as a list with duplicates and ``None`` entries removed."""
    seen: set[str] = set()
    unique: list[pathlib.Path] = []
    for path in paths:
        if path is None:
            continue
        candidate = pathlib.Path(path)
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def download_youtube_audio(url: str, output_dir: str | pathlib.Path = config.DOWNLOAD_DIRECTORY) -> pathlib.Path:
    """Download *url* as a 320kbps MP3 and return the resulting file path.

    Args:
        url: YouTube video URL.
        output_dir: Directory that will contain the MP3 file.

    Raises:
        ValueError: If *url* is empty or not a recognizable YouTube URL.
        DownloadError: If yt-dlp fails to download or convert the audio.
    """
    if not is_valid_youtube_url(url):
        raise ValueError("Please enter a valid YouTube URL.")

    output_path = ensure_directory(pathlib.Path(output_dir)).resolve()
    clean_directory(output_path)

    try:
        base_options: dict[str, t.Any] = {"quiet": True, "no_warnings": True, "noplaylist": True}
        if FFMPEG_BINARY is not None:
            base_options["ffmpeg_location"] = str(FFMPEG_BINARY)

        with yt_dlp.YoutubeDL(base_options) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title") or info.get("id") or "audio"
            sanitized_title = sanitize_filename(title, default="audio")
            destination = _make_unique_path(output_path, sanitized_title, ".mp3")

        options = _build_options(destination)
        with yt_dlp.YoutubeDL(options) as ydl:
            result = ydl.extract_info(url, download=True)

        reported_path = _extract_download_filepath(result)
        candidate_paths = _unique_paths(
            [
                reported_path,
                destination,
                reported_path.with_suffix(".mp3") if reported_path and reported_path.suffix.lower() != ".mp3" else None,
            ]
        )

        for candidate in candidate_paths:
            if candidate.exists():
                return candidate.resolve(strict=False)

        fallback_candidates = _unique_paths(
            path
            for path in destination.parent.glob(f"{destination.stem}*")
            if path.suffix.lower() == ".mp3"
        )
        for candidate in fallback_candidates:
            if candidate.exists():
                return candidate.resolve(strict=False)

        raise DownloadError(
            "Download finished but the converted MP3 file was not found. Check FFmpeg installation and write permissions."
        )
    except YTDLPDownloadError as exc:  # pragma: no cover - depends on network
        raise DownloadError("Download failed. Check URL and internet connection.") from exc
    except FileNotFoundError as exc:  # pragma: no cover - ffmpeg missing
        raise DownloadError("FFmpeg not found. Please install FFmpeg and ensure it is on PATH.") from exc
