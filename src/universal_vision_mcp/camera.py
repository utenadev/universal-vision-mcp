"""Camera abstraction and implementations for Universal Vision MCP."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple, Optional
from urllib.parse import urlparse

import cv2
import numpy as np
import onvif
from onvif import ONVIFCamera

import re

logger = logging.getLogger(__name__)

# Directory to save captured images
CAPTURE_DIR = Path.home() / ".universal-vision-mcp" / "captures"


def sanitize_name(name: str) -> str:
    """Sanitize a name to be a valid MCP tool name component.
    
    Allowed pattern: ^[a-zA-Z0-9_-]{1,64}$
    We replace spaces and hyphens with underscores, and remove other invalid characters.
    """
    # Replace spaces and hyphens with underscores
    name = name.replace(" ", "_").replace("-", "_")
    # Remove any other characters that are not alphanumeric, underscore, or hyphen
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
    # Ensure it's not empty and not too long
    if not name:
        name = "camera"
    return name[:64]


class BaseCamera(ABC):
    """Abstract base class for all cameras."""

    def __init__(self, name: str):
        self.name = name
        self.sanitized_name = sanitize_name(name)
        self.preview_enabled = False
        self._last_frame: Any = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._cap: cv2.VideoCapture | None = None

    @abstractmethod
    def get_body_description(self) -> str:
        """Return the Lisp-style S-expression describing this camera's capabilities."""
        pass

    @abstractmethod
    def _get_stream_source(self) -> str | int:
        """Return the source for cv2.VideoCapture."""
        pass

    def start(self):
        """Start the background capture thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def close(self):
        """Stop capture and release resources."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._cap:
            self._cap.release()
        cv2.destroyAllWindows()
        logger.info(f"Camera {self.name} resources released.")

    def set_preview(self, enabled: bool):
        """Enable or disable live preview window."""
        self.preview_enabled = enabled
        if not enabled:
            # We can't easily close specific windows from a thread in some OS, 
            # so we let the loop handle it or just clear it.
            pass

    def _capture_loop(self):
        """Background thread to keep camera buffer fresh."""
        source = self._get_stream_source()
        if source is None:
            self._running = False
            return

        self._cap = cv2.VideoCapture(source)
        window_name = f"Universal Vision: {self.name}"

        if not self._cap.isOpened():
            logger.error(f"Failed to open camera source for {self.name}: {source}")
            self._running = False
            return

        logger.info(f"Camera {self.name} capture thread started.")

        try:
            while self._running:
                ret, frame = self._cap.read()
                if not ret:
                    logger.warning(f"Camera {self.name} failed to read frame, retrying...")
                    time.sleep(2.0)
                    self._cap.open(source)
                    continue

                with self._lock:
                    self._last_frame = frame.copy()

                if self.preview_enabled:
                    cv2.imshow(window_name, frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.preview_enabled = False
                else:
                    # Try to close window if it was open
                    try:
                        cv2.destroyWindow(window_name)
                    except cv2.error:
                        pass
        finally:
            if self._cap:
                self._cap.release()
            cv2.destroyAllWindows()

    async def capture(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the latest frame. Returns (base64_jpeg, saved_path)."""
        frame = None
        with self._lock:
            if self._last_frame is not None:
                frame = self._last_frame.copy()

        if frame is None:
            return None, None

        def _process():
            h, w = frame.shape[:2]
            # Increase resolution for better AI vision (1024px height)
            target_h = 1024
            if h > target_h:
                scale = target_h / h
                # Use INTER_AREA for better downsampling quality
                resized = cv2.resize(frame, (int(w * scale), target_h), interpolation=cv2.INTER_AREA)
            else:
                resized = frame

            # Higher JPEG quality (95) to preserve fine details like fingers
            success, buffer = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if not success:
                return None, None

            data = buffer.tobytes()
            b64 = base64.b64encode(data).decode()

            CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = CAPTURE_DIR / f"{self.sanitized_name}_{timestamp}.jpg"
            save_path.write_bytes(data)
            return b64, str(save_path)

        return await asyncio.to_thread(_process)


    async def move(self, direction: str, degrees: int = 30) -> str:
        """Move the camera (PTZ). Default implementation does nothing."""
        return f"Camera {self.name} does not support movement."


class LocalCamera(BaseCamera):
    """USB or Built-in camera implementation."""

    def __init__(self, index: int, name: str = ""):
        name = name or f"usb_cam_{index}"
        super().__init__(name)
        self.index = index

    def _get_stream_source(self) -> int:
        return self.index

    def get_body_description(self) -> str:
        return (
            f'(body :id {self.sanitized_name}_system :role "Primary Visual Organ")\n'
            f'(part :id {self.sanitized_name} :type builtin :tool see_{self.sanitized_name}\n'
            f'  :desc "Your physical eye. Use this tool to OBSERVE the world.")\n'
            f'(part :id neck_{self.sanitized_name} :status fixed\n'
            f'  :desc "Fixed neck. You cannot move this camera.")\n'
            f'(feature :id {self.sanitized_name}_monitor :tool preview_{self.sanitized_name}\n'
            f'  :desc "Display your live feed on the human\'s host monitor.")'
        )


class NetworkCamera(BaseCamera):
    """IP Camera implementation with RTSP and ONVIF (PTZ)."""

    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        port: int = 2020,
        name: str = "network_cam",
    ):
        super().__init__(name)
        self.host = host
        self.username = username
        self.password = password
        self.port = port

        self._cam_onvif: Any = None
        self._ptz: Any = None
        self._profile_token: str | None = None

    def _get_stream_source(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username and self.password else ""
        if "://" in self.host:
            return self.host
        return f"rtsp://{auth}{self.host}:554/stream1"

    def get_body_description(self) -> str:
        has_ptz = "ptz" if self._ptz or self.host else "fixed"
        movement_desc = "You can pan/tilt this eye." if has_ptz == "ptz" else "Fixed neck."
        return (
            f'(body :id {self.sanitized_name}_system :role "Remote Visual Organ")\n'
            f'(part :id {self.sanitized_name} :type network :tool see_{self.sanitized_name}\n'
            f'  :desc "Your remote eye. Use this to OBSERVE the target area.")\n'
            f'(part :id neck_{self.sanitized_name} :type {has_ptz} :tool look_{self.sanitized_name}\n'
            f'  :desc "{movement_desc} Use look_{self.sanitized_name} to aim before you see.")\n'
            f'(feature :id {self.sanitized_name}_monitor :tool preview_{self.sanitized_name}\n'
            f'  :desc "Display your live feed on the human\'s host monitor.")'
        )

    async def _ensure_onvif(self) -> bool:
        if self._ptz:
            return True
        try:
            onvif_dir = os.path.dirname(onvif.__file__)
            wsdl_dir = os.path.join(onvif_dir, "wsdl")
            if not os.path.isdir(wsdl_dir):
                wsdl_dir = os.path.join(os.path.dirname(onvif_dir), "wsdl")

            hostname = self.host
            if "://" in hostname:
                hostname = urlparse(hostname).hostname or self.host

            self._cam_onvif = ONVIFCamera(
                hostname, self.port, self.username, self.password, wsdl_dir=wsdl_dir
            )
            await self._cam_onvif.update_xaddrs()
            media = await self._cam_onvif.create_media_service()
            profiles = await media.GetProfiles()
            self._profile_token = profiles[0].token if profiles else "Profile_1"
            self._ptz = await self._cam_onvif.create_ptz_service()
            logger.info(f"Connected to PTZ service for {self.name} at {hostname}")
            return True
        except Exception as e:
            logger.debug(f"ONVIF PTZ not available for {self.name}: {e}")
            return False

    async def move(self, direction: str, degrees: int = 30) -> str:
        if not await self._ensure_onvif():
            return f"PTZ movement not available for {self.name}."
        try:
            pan, tilt = 0.0, 0.0
            if direction == "left": pan = degrees / 180.0
            elif direction == "right": pan = -degrees / 180.0
            elif direction == "up": tilt = -degrees / 90.0
            elif direction == "down": tilt = degrees / 90.0

            await self._ptz.RelativeMove({
                "ProfileToken": self._profile_token,
                "Translation": {"PanTilt": {"x": pan, "y": tilt}},
            })
            await asyncio.sleep(0.4)
            return f"Looked {direction} using {self.name}."
        except Exception as e:
            logger.warning(f"Move failed for {self.name}: {e}")
            self._ptz = None
            return f"Move failed for {self.name}: {e}"


class MockCamera(BaseCamera):
    """A virtual camera that generates 'NO SIGNAL' images. Useful for testing."""

    def __init__(self, name: str = "mock_cam"):
        super().__init__(name)

    def _get_stream_source(self) -> Any:
        return None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._generate_loop, daemon=True)
        self._thread.start()

    def _generate_loop(self):
        window_name = f"Universal Vision: {self.name}"
        # Mock state for visual feedback
        pan, tilt = 0, 0

        while self._running:
            # Create a dark grid background
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            for i in range(0, 640, 80):
                cv2.line(frame, (i, 0), (i, 480), (30, 30, 30), 1)
            for i in range(0, 480, 60):
                cv2.line(frame, (0, i), (640, i), (30, 30, 30), 1)

            font = cv2.FONT_HERSHEY_SIMPLEX

            # --- Draw HUD ---
            # Center Crosshair
            cv2.line(frame, (310, 240), (330, 240), (0, 255, 0), 1)
            cv2.line(frame, (320, 230), (320, 250), (0, 255, 0), 1)

            # Status Bar (Bottom)
            cv2.rectangle(frame, (0, 440), (640, 480), (50, 50, 50), -1)
            status_text = f"MODE: PTZ_MOCK | ID: {self.name.upper()} | STATUS: CONNECTED"
            cv2.putText(frame, status_text, (10, 465), font, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

            # Timestamp (Top Right)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, ts, (420, 30), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # Navigation Indicators (Top Left)
            cv2.putText(frame, "  ^  ", (30, 40), font, 0.8, (200, 200, 200), 2)
            cv2.putText(frame, "<   >", (30, 70), font, 0.8, (200, 200, 200), 2)
            cv2.putText(frame, "  v  ", (30, 100), font, 0.8, (200, 200, 200), 2)
            cv2.putText(frame, "CONTROL: ACTIVE", (30, 130), font, 0.4, (0, 255, 255), 1)

            # Main Text
            text = "MOCK VISION SYSTEM"
            cv2.putText(frame, text, (200, 200), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "SIMULATING EMBODIMENT...", (210, 240), font, 0.6, (0, 200, 255), 1, cv2.LINE_AA)

            with self._lock:
                self._last_frame = frame

            if self.preview_enabled:
                cv2.imshow(window_name, frame)
                cv2.waitKey(1)
            else:
                try:
                    cv2.destroyWindow(window_name)
                except cv2.error:
                    pass

            time.sleep(1.0)

    def get_body_description(self) -> str:
        return (
            f'(body :id {self.sanitized_name}_system :role "Virtual Visual Organ")\n'
            f'(part :id {self.sanitized_name} :type mock :tool see_{self.sanitized_name}\n'
            f'  :desc "A virtual test camera. Use this to OBSERVE virtual test patterns.")\n'
            f'(part :id neck_{self.sanitized_name} :status fixed\n'
            f'  :desc "Fixed virtual neck.")\n'
            f'(feature :id {self.sanitized_name}_monitor :tool preview_{self.sanitized_name}\n'
            f'  :desc "Display your live virtual feed on the human\'s host monitor.")'
        )

    async def move(self, direction: str, degrees: int = 30) -> str:
        return f"Mock camera {self.name} simulated looking {direction}."
