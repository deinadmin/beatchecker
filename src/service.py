"""FastAPI background service for BeatChecker downloads and analysis."""

from __future__ import annotations

import asyncio
import logging
import pathlib
import shutil
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator

from . import config
from .analyze import AnalysisError, AnalysisResult, analyze_audio, ensure_results_directory
from .download import FFMPEG_BINARY, DownloadError, download_youtube_audio
from .licensing import LicenseError, LicenseManager
from .utils import ensure_directory, is_valid_youtube_url

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BeatChecker Service",
    version="1.0.0",
    description="Background API for downloading and analyzing YouTube beats.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.API_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


license_manager = LicenseManager()


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Current service status")
    license_active: bool = Field(default=False, description="Whether BeatChecker is activated")
    message: str | None = Field(default=None, description="Additional status or licensing message")


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="YouTube URL to download and analyze")

    @validator("url")
    def _validate_url(cls, value: str) -> str:
        if not is_valid_youtube_url(value):
            raise ValueError("Please provide a valid YouTube URL.")
        return value


class AnalyzeResponse(BaseModel):
    url: str
    bpm: int
    key: str
    file_path: str
    filename: str


class SaveRequest(BaseModel):
    file_path: str = Field(..., description="Path to the file to save")


class SaveResponse(BaseModel):
    success: bool
    saved_path: str | None = None
    message: str


class LicenseStatusResponse(BaseModel):
    product_id: int | None = None
    active: bool
    license_key: str | None = None
    expires_at: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    max_machines: int | None = None
    allowed_machines: int | None = None
    activated_machines: int | None = None
    activated_at: str | None = None
    last_validated_at: str | None = None
    blocked: bool = False
    message: str | None = None


class LicenseActivateRequest(BaseModel):
    license_key: str = Field(..., description="License key to activate BeatChecker")


class LicenseActivateResponse(BaseModel):
    status: LicenseStatusResponse
    message: str


class LicenseDeactivateResponse(BaseModel):
    message: str


@app.on_event("startup")
async def _on_startup() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_directory(config.DOWNLOAD_DIRECTORY)
    if FFMPEG_BINARY is not None:
        logger.info("FFmpeg resolved at %s", FFMPEG_BINARY)
    else:
        logger.warning("FFmpeg binary not bundled; falling back to PATH during runtime.")
    logger.info(
        "BeatChecker service starting on %s:%s", config.API_HOST, config.API_PORT
    )
    if license_manager.is_active():
        logger.info("License active for %s", license_manager.status().get("license_key"))
    else:
        logger.warning("License inactive: %s", license_manager.inactive_reason())


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a simple health indicator for readiness probes."""

    active = license_manager.is_active()
    message = None if active else license_manager.inactive_reason()
    return HealthResponse(license_active=active, message=message)


@app.get("/license/status", response_model=LicenseStatusResponse)
async def license_status() -> LicenseStatusResponse:
    """Return the current license status."""

    try:
        status_data = await asyncio.to_thread(license_manager.status)
        return LicenseStatusResponse(**status_data)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to retrieve license status")
        # Return minimal inactive status on error
        return LicenseStatusResponse(
            active=False,
            message="Failed to retrieve license status. Please try again.",
        )


@app.post("/license/activate", response_model=LicenseActivateResponse)
async def license_activate(payload: LicenseActivateRequest) -> LicenseActivateResponse:
    """Activate BeatChecker using the provided license key."""

    try:
        await asyncio.to_thread(license_manager.activate, payload.license_key)
    except LicenseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected failure during license activation")
        raise HTTPException(status_code=500, detail="Activation failed. Please try again.") from exc

    status_data = license_manager.status()
    return LicenseActivateResponse(
        status=LicenseStatusResponse(**status_data),
        message="License activated successfully.",
    )


@app.post("/license/refresh", response_model=LicenseStatusResponse)
async def license_refresh() -> LicenseStatusResponse:
    """Force a license refresh from the licensing server."""

    try:
        await asyncio.to_thread(license_manager.refresh)
    except LicenseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected failure during license refresh")
        raise HTTPException(status_code=500, detail="Failed to refresh license. Please try again.") from exc

    status_data = license_manager.status()
    return LicenseStatusResponse(**status_data)


@app.post("/license/deactivate", response_model=LicenseDeactivateResponse)
async def license_deactivate() -> LicenseDeactivateResponse:
    """Deactivate the current license and remove from this device."""

    try:
        await asyncio.to_thread(license_manager.deactivate)
    except LicenseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected failure during license deactivation")
        raise HTTPException(status_code=500, detail="Failed to deactivate license. Please try again.") from exc

    return LicenseDeactivateResponse(message="License deactivated successfully.")


async def _perform_analysis(url: str) -> tuple[pathlib.Path, AnalysisResult]:
    def worker() -> tuple[pathlib.Path, AnalysisResult]:
        audio_path = download_youtube_audio(url)
        results = analyze_audio(audio_path)
        return audio_path, results

    return await asyncio.to_thread(worker)


@app.post("/analyze", response_model=AnalyzeResponse, status_code=202)
async def analyze_endpoint(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Download the given URL, analyze it, and return BPM/key metadata."""

    if not license_manager.is_active():
        raise HTTPException(status_code=403, detail=license_manager.inactive_reason())

    try:
        audio_path, results = await _perform_analysis(payload.url)
    except ValueError as exc:
        logger.warning("Validation failed for URL %s: %s", payload.url, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DownloadError as exc:
        logger.error("DownloadError for URL %s: %s", payload.url, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except AnalysisError as exc:
        logger.error("AnalysisError for URL %s: %s", payload.url, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected failure while processing %s", payload.url)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error occurred during analysis. Check service logs.",
        ) from exc

    result = AnalyzeResponse(
        url=payload.url,
        bpm=int(results.bpm),
        key=results.key,
        file_path=str(results.file_path.resolve()),
        filename=results.file_path.name,
    )
    logger.info(
        "Analysis completed for %s -> BPM %s, Key %s", payload.url, result.bpm, result.key
    )
    return result


@app.post("/save", response_model=SaveResponse)
async def save_endpoint(payload: SaveRequest) -> SaveResponse:
    """Copy the analyzed file to the user's Documents/BeatChecker directory."""

    if not license_manager.is_active():
        raise HTTPException(status_code=403, detail=license_manager.inactive_reason())

    try:
        source = pathlib.Path(payload.file_path)
        if not source.exists():
            raise HTTPException(status_code=404, detail="Source file not found.")

        save_dir = ensure_results_directory()
        destination = save_dir / source.name

        # Handle duplicate names
        if destination.exists():
            stem = destination.stem
            suffix = destination.suffix
            counter = 1
            while destination.exists():
                destination = save_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        await asyncio.to_thread(shutil.copy2, source, destination)
        logger.info("Saved %s to %s", source.name, destination)

        return SaveResponse(
            success=True,
            saved_path=str(destination.resolve()),
            message=f"Saved to {destination.resolve()}",
        )
    except Exception as exc:
        logger.exception("Failed to save file %s", payload.file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {exc}",
        ) from exc


@app.get("/download")
async def download_endpoint(file: str = Query(..., description="Absolute path to file within downloads directory")) -> FileResponse:
    """Return the requested audio file as a downloadable attachment."""

    path = pathlib.Path(file).expanduser().resolve()
    downloads_root = config.DOWNLOAD_DIRECTORY.resolve()

    try:
        path.relative_to(downloads_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access to requested file is not allowed.")

    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Requested file not found.")

    return FileResponse(path, filename=path.name, media_type="audio/mpeg")


def run(host: str | None = None, port: int | None = None) -> None:
    """Run the FastAPI service using uvicorn."""

    import uvicorn

    host = host or config.API_HOST
    port = port or config.API_PORT

    logger.info("Starting BeatChecker service on %s:%s", host, port)
    # log_config=None prevents uvicorn from configuring logging
    # (fixes TTY detection error in PyInstaller windowless mode)
    uvicorn.run(app, host=host, port=port, log_level="info", log_config=None)


if __name__ == "__main__":  # pragma: no cover
    run()
