"""Audio analysis utilities (BPM and key detection)."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

import librosa
import numpy as np

from . import config
from .utils import ensure_directory

__all__ = [
    "AnalysisResult",
    "AnalysisError",
    "detect_bpm",
    "detect_key",
    "analyze_audio",
]


@dataclass(slots=True)
class AnalysisResult:
    """Container for the audio analysis metrics."""

    bpm: float
    key: str
    file_path: pathlib.Path


class AnalysisError(RuntimeError):
    """Raised when analysis cannot be completed."""


def detect_bpm(audio_path: str | pathlib.Path) -> float:
    """Return tempo in BPM for the audio file located at *audio_path*."""
    path = pathlib.Path(audio_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        signal, sample_rate = librosa.load(path, sr=config.TARGET_SAMPLING_RATE)
        tempo, _ = librosa.beat.beat_track(y=signal, sr=sample_rate)
        # Use floor + 0.5 for consistent rounding (always rounds .5 up)
        return int(float(tempo) + 0.5)
    except Exception as exc:  # pragma: no cover - librosa I/O errors
        raise AnalysisError("Could not detect BPM from audio file.") from exc


def detect_key(audio_path: str | pathlib.Path) -> str:
    """Return the musical key for *audio_path*."""
    path = pathlib.Path(audio_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        signal, sample_rate = librosa.load(path, sr=config.TARGET_SAMPLING_RATE)
        chroma = librosa.feature.chroma_cqt(y=signal, sr=sample_rate)
        if chroma.size == 0:
            raise ValueError("No chroma information available")

        chroma_vector = chroma.mean(axis=1)
        if not np.any(chroma_vector):
            raise ValueError("Chroma vector is empty")

        chroma_norm = chroma_vector / np.linalg.norm(chroma_vector)

        major_profile = np.array([
            6.35,
            2.23,
            3.48,
            2.33,
            4.38,
            4.09,
            2.52,
            5.19,
            2.39,
            3.66,
            2.29,
            2.88,
        ])
        minor_profile = np.array([
            6.33,
            2.68,
            3.52,
            5.38,
            2.60,
            3.53,
            2.54,
            4.75,
            3.98,
            2.69,
            3.34,
            3.17,
        ])

        profiles = {
            "Major": major_profile / np.linalg.norm(major_profile),
            "Minor": minor_profile / np.linalg.norm(minor_profile),
        }

        note_names = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]

        scores: list[float] = []
        labels: list[tuple[int, str]] = []
        for mode, profile in profiles.items():
            for semitone in range(12):
                rotated = np.roll(profile, semitone)
                score = float(np.dot(chroma_norm, rotated))
                scores.append(score)
                labels.append((semitone, mode))

        if not scores:
            raise ValueError("No scores computed for key detection")

        scores_array = np.array(scores)
        best_index = int(scores_array.argmax())
        best_score = float(scores_array[best_index])
        sorted_scores = np.sort(scores_array)
        second_best = float(sorted_scores[-2]) if len(sorted_scores) > 1 else 0.0

        best_semitone, best_mode = labels[best_index]
        key_name = f"{note_names[best_semitone]} {best_mode}"

        return key_name
    except Exception as exc:  # pragma: no cover - analysis edge cases
        raise AnalysisError("Could not detect musical key from audio file.") from exc


def analyze_audio(audio_path: str | pathlib.Path) -> AnalysisResult:
    """Perform BPM and key analysis on *audio_path* and return results."""
    path = pathlib.Path(audio_path)
    bpm = detect_bpm(path)
    key = detect_key(path)
    return AnalysisResult(
        bpm=bpm,
        key=key,
        file_path=path,
    )


def ensure_results_directory() -> pathlib.Path:
    """Ensure the directory for saving exported results exists."""

    return ensure_directory(config.SAVE_DIRECTORY)
