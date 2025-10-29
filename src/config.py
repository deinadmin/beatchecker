"""Application configuration constants for BeatChecker."""

from __future__ import annotations

import os
import pathlib

# Window configuration
WINDOW_TITLE: str = "BeatChecker"
WINDOW_WIDTH: int = 700
WINDOW_HEIGHT: int = 500

# Download configuration
MP3_QUALITY: str = "320"
DOWNLOAD_TIMEOUT: int = 300  # seconds
DOWNLOAD_DIRECTORY: pathlib.Path = pathlib.Path.home() / "BeatChecker" / "downloads"
SAVE_DIRECTORY: pathlib.Path = pathlib.Path.home() / "Documents" / "BeatChecker"
LICENSE_STORAGE_PATH: pathlib.Path = pathlib.Path.home() / "BeatChecker" / "license.json"

# Analysis configuration
MIN_KEY_CONFIDENCE: int = 50  # percentage
TARGET_SAMPLING_RATE: int = 22_050

# UI configuration
PRIMARY_COLOR: str = "#1F6AA5"
SUCCESS_COLOR: str = "#2CC985"
WARNING_COLOR: str = "#FF9500"
ERROR_COLOR: str = "#FF3B30"

# API configuration
API_HOST: str = os.environ.get("BEATCHECKER_HOST", "127.0.0.1")
API_PORT: int = int(os.environ.get("BEATCHECKER_PORT", "8765"))

_raw_origins = os.environ.get("BEATCHECKER_ALLOWED_ORIGINS")
if _raw_origins:
    API_ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]
else:
    API_ALLOWED_ORIGINS = ["*"]

# Licensing configuration
LICENSE_PRODUCT_ID: int = int(os.environ.get("BEATCHECKER_LICENSE_PRODUCT_ID", "31405"))
LICENSE_ACCESS_TOKEN: str | None = os.environ.get(
    "BEATCHECKER_LICENSE_TOKEN",
    "WyIxMTQwNDAzNTYiLCJaUTBQMXlGWnM1WGRDV0U3MzcyMmEycUpoYTd6MEpiZzRxMFVlbGFKIl0=",
)
# RSA Public Key from https://app.cryptolens.io/User/Security
LICENSE_RSA_PUBLIC_KEY: str | None = os.environ.get(
    "BEATCHECKER_LICENSE_RSA_KEY",
    "<RSAKeyValue><Modulus>qK3K5OtMRQQGqd1yCbf/0Gyeul+2zhqhAhAiD8BMKrzJf8afMXC7AAQek7y+fYfL/2FgE6dLfPZypo4VoGAlkvx0djDMmyMXQUHPJpo03rpxDRs1LWvQ05LX+E8AYf49uSU2R+6ZFW704iI/dpufHoS3e4xWV71MMkk9UxCIvJ9ikAkuzvaG0+iwUvDToDwB6DFGkqc6ZQZFOTP2k97gtL7ffe2qPiaN1ePAoseHcnVLjBrmzS2iZkRfDH+qLtk2kdl96Uorsf3oS1Ir28ReAZSgnD76fi7wVi7nSucd2CJiGYU3vgKoSGsCO8UZXPMCyyhknhePbpbR8pMNbArnCw==</Modulus><Exponent>AQAB</Exponent></RSAKeyValue>",
)
