"""License management for BeatChecker using Cryptolens."""

from __future__ import annotations

import datetime as dt
import json
import logging
import pathlib
import threading
from typing import Any, Dict, Optional

from . import config
from .utils import ensure_directory

try:
    from licensing.models import LicenseKey
    from licensing.methods import Key, Helpers
except ImportError:
    # Fallback to Python 2 version if licensing package not installed
    from .util.cryptolens_python2 import Key, Helpers, LicenseKey

logger = logging.getLogger(__name__)


def _now() -> dt.datetime:
    """Return current UTC time as naive datetime (for Cryptolens compatibility)."""
    return dt.datetime.utcnow()


def _mask_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    stripped = key.replace("-", "").replace(" ", "")
    if len(stripped) <= 4:
        return stripped
    return f"***{stripped[-4:]}"


class LicenseError(RuntimeError):
    """Raised when a licensing operation fails."""


# RSA Public Key will be loaded from config
def get_rsa_key() -> str:
    """Get RSA public key from config."""
    if config.LICENSE_RSA_PUBLIC_KEY:
        return config.LICENSE_RSA_PUBLIC_KEY
    raise LicenseError(
        "RSA public key not configured. Please set LICENSE_RSA_PUBLIC_KEY in config.py or "
        "BEATCHECKER_LICENSE_RSA_KEY environment variable. Get your key from "
        "https://app.cryptolens.io/User/Security"
    )


class LicenseManager:
    """Manage BeatChecker licensing state."""

    def __init__(self, storage_path: Optional[pathlib.Path] = None) -> None:
        self._storage_path = storage_path or config.LICENSE_STORAGE_PATH
        ensure_directory(self._storage_path.parent)
        self._machine_code = Helpers.GetMachineCode(v=2)
        self._lock = threading.Lock()
        self._license: Optional[LicenseKey] = None
        self._license_string: Optional[str] = None
        self._last_refresh: Optional[dt.datetime] = None
        self._load_state()

    def _is_active_unlocked(self) -> bool:
        """Check if license is active. Must be called with lock held."""
        if not self._license:
            return False
        if self._license.block:
            return False
        if self._license.expires and self._license.expires < _now():
            return False
        return Helpers.IsOnRightMachine(self._license, v=2)

    def _inactive_reason_unlocked(self) -> str:
        """Get inactive reason. Must be called with lock held."""
        if not self._license:
            return "BeatChecker is not activated. Please enter a license key."
        if self._license.block:
            return "Your license has been blocked. Please contact support."
        if self._license.expires and self._license.expires < _now():
            expired = self._license.expires.strftime("%Y-%m-%d")
            return f"Your license expired on {expired}."
        if not Helpers.IsOnRightMachine(self._license, v=2):
            return "This license is not activated on this machine."
        return "BeatChecker is not activated."

    def is_active(self) -> bool:
        with self._lock:
            return self._is_active_unlocked()

    def inactive_reason(self) -> str:
        with self._lock:
            return self._inactive_reason_unlocked()

    def _should_refresh(self) -> bool:
        """Check if license should be refreshed. Must be called with lock held."""
        if not self._license_string:
            return False
        # Don't auto-refresh if license is already known to be blocked
        if self._license and self._license.block:
            return False
        if not self._last_refresh:
            return True
        # Refresh if more than 1 hour has passed
        time_since_refresh = _now() - self._last_refresh
        return time_since_refresh.total_seconds() > 3600

    def _try_background_refresh(self) -> None:
        """Attempt to refresh license in background without blocking. Call without lock."""
        def _refresh_worker():
            try:
                self.refresh()
                logger.info("Background license refresh successful")
            except Exception as exc:
                logger.warning("Background license refresh failed: %s", exc)
        
        threading.Thread(target=_refresh_worker, daemon=True).start()

    def status(self) -> Dict[str, Any]:
        # Check if refresh is needed outside the lock to avoid deadlock
        should_refresh = False
        with self._lock:
            should_refresh = self._should_refresh()
        
        # Trigger background refresh if needed (without holding lock)
        if should_refresh:
            self._try_background_refresh()
        
        with self._lock:
            active = self._is_active_unlocked()
            lic = self._license
            status = {
                "product_id": lic.product_id if lic else config.LICENSE_PRODUCT_ID,
                "active": active,
                "license_key": _mask_key(lic.key) if lic else None,
                "expires_at": lic.expires.isoformat() if lic and lic.expires else None,
                "customer_name": lic.customer.Name if lic and lic.customer else None,
                "customer_email": lic.customer.Email if lic and lic.customer else None,
                "max_machines": lic.max_no_of_machines if lic else None,
                "allowed_machines": None,
                "activated_machines": len(lic.activated_machines) if lic and lic.activated_machines else 0,
                "activated_at": lic.created.isoformat() if lic and lic.created else None,
                "last_validated_at": lic.sign_date.isoformat() if lic and lic.sign_date else None,
                "blocked": lic.block if lic else False,
                "message": None if active else self._inactive_reason_unlocked(),
            }
            return status

    def activate(self, license_key: str) -> None:
        key = (license_key or "").strip()
        if not key:
            raise LicenseError("A license key is required.")
        
        if not config.LICENSE_ACCESS_TOKEN:
            raise LicenseError("Licensing is not configured. Missing access token.")
        
        result = Key.activate(
            token=config.LICENSE_ACCESS_TOKEN,
            rsa_pub_key=get_rsa_key(),
            product_id=config.LICENSE_PRODUCT_ID,
            key=key,
            machine_code=self._machine_code
        )
        
        if result[0] is None:
            error_msg = result[1] if result[1] else "License activation failed."
            raise LicenseError(error_msg)

        if not Helpers.IsOnRightMachine(result[0], v=2):
            raise LicenseError("This license cannot be activated on this machine.")

        # Prevent activating expired licenses
        expires_at = result[0].expires
        if expires_at and expires_at < _now():
            formatted = expires_at.strftime("%Y-%m-%d")
            raise LicenseError(f"This license expired on {formatted} and cannot be activated.")

        with self._lock:
            self._license = result[0]
            self._license_string = self._license.key
            self._last_refresh = _now()
            self._save_state()
        
        logger.info("License activated for %s", _mask_key(key))

    def refresh(self) -> None:
        with self._lock:
            if not self._license_string:
                raise LicenseError("No license has been activated.")
            current_key = self._license_string
            existing_license = self._license
        
        if not config.LICENSE_ACCESS_TOKEN:
            raise LicenseError("Licensing is not configured. Missing access token.")
        
        result = Key.activate(
            token=config.LICENSE_ACCESS_TOKEN,
            rsa_pub_key=get_rsa_key(),
            product_id=config.LICENSE_PRODUCT_ID,
            key=current_key,
            machine_code=self._machine_code
        )
        
        if result[0] is None:
            error_msg = result[1] if result[1] else "License refresh failed."
            
            # Check if the error indicates the key is blocked
            if "blocked" in error_msg.lower():
                # Mark the existing license as blocked
                if existing_license:
                    with self._lock:
                        # Manually set block flag on existing license
                        existing_license.block = True
                        self._license = existing_license
                        self._last_refresh = _now()
                        self._save_state()
                    logger.warning("License %s is now blocked", _mask_key(current_key))
                    return
            
            raise LicenseError(error_msg)
        
        # Save the updated license state
        with self._lock:
            self._license = result[0]
            self._last_refresh = _now()
            self._save_state()
            
        # Log the updated status
        if result[0].block:
            logger.warning("License %s is now blocked", _mask_key(current_key))
        elif result[0].expires and result[0].expires < _now():
            logger.warning("License %s has expired", _mask_key(current_key))

    def deactivate(self) -> None:
        """Deactivate the current license and clear local state."""
        with self._lock:
            if not self._license_string:
                raise LicenseError("No license has been activated.")
            
            # Clear license state
            self._license = None
            self._license_string = None
            self._last_refresh = None
            
            # Delete the license file
            if self._storage_path.exists():
                try:
                    self._storage_path.unlink()
                    logger.info("License deactivated and removed from device")
                except Exception as exc:
                    logger.warning("Failed to delete license file: %s", exc)

    def _load_state(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as fh:
                license_data = fh.read()
            if license_data.strip():
                self._license = LicenseKey.load_from_string(get_rsa_key(), license_data, 30)
                if self._license:
                    self._license_string = self._license.key
                    logger.info("Loaded cached license for %s", _mask_key(self._license_string))
        except Exception as exc:
            logger.warning("Failed to load license state: %s", exc)
            self._license = None
            self._license_string = None

    def _save_state(self) -> None:
        if not self._license:
            return
        try:
            with self._storage_path.open("w", encoding="utf-8") as fh:
                fh.write(self._license.save_as_string())
        except Exception as exc:
            logger.error("Failed to persist license state: %s", exc)
