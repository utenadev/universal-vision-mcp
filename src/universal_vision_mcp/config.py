"""Configuration management for Universal Vision MCP."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".universal-vision-mcp"
CONFIG_FILE = CONFIG_DIR / "config.json"


class CameraSettings(BaseModel):
    """Individual camera configuration."""
    name: str
    type: str = "network"  # "local" or "network"
    # For local
    index: int = 0
    # For network
    host: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    port: int = 2020
    preview: bool = False


class AppConfig(BaseModel):
    """Global application configuration."""
    cameras: List[CameraSettings] = Field(default_factory=list)

    @classmethod
    def load(cls) -> AppConfig:
        """Load config from file or return default."""
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return cls.model_validate(data)
            except Exception:
                return cls()
        return cls()

    def save(self):
        """Save current config to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            self.model_dump_json(indent=2), encoding="utf-8"
        )
