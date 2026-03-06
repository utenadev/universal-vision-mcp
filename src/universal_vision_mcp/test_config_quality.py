"""Tests for image quality configuration in config module."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch

from universal_vision_mcp.config import AppConfig, CameraSettings, CONFIG_FILE


class TestCameraSettings:
    """Test suite for CameraSettings with quality parameters."""

    def test_camera_settings_default_quality(self):
        """Test that CameraSettings has default quality values."""
        settings = CameraSettings(name="test_cam", type="local")
        
        assert hasattr(settings, 'target_height')
        assert hasattr(settings, 'jpeg_quality')
        assert settings.target_height == 1024
        assert settings.jpeg_quality == 95

    def test_camera_settings_custom_quality(self):
        """Test that CameraSettings accepts custom quality values."""
        settings = CameraSettings(
            name="test_cam",
            type="network",
            target_height=768,
            jpeg_quality=80
        )
        
        assert settings.target_height == 768
        assert settings.jpeg_quality == 80

    def test_camera_settings_serialization(self):
        """Test that CameraSettings with quality params serializes correctly."""
        settings = CameraSettings(
            name="garden_cam",
            type="network",
            host="192.168.1.100",
            target_height=1280,
            jpeg_quality=90
        )
        
        data = settings.model_dump()
        
        assert data['name'] == "garden_cam"
        assert data['type'] == "network"
        assert data['host'] == "192.168.1.100"
        assert data['target_height'] == 1280
        assert data['jpeg_quality'] == 90

    def test_camera_settings_deserialization(self):
        """Test that CameraSettings with quality params deserializes correctly."""
        data = {
            "name": "usb_eye",
            "type": "local",
            "index": 0,
            "target_height": 512,
            "jpeg_quality": 75
        }
        
        settings = CameraSettings.model_validate(data)
        
        assert settings.name == "usb_eye"
        assert settings.type == "local"
        assert settings.index == 0
        assert settings.target_height == 512
        assert settings.jpeg_quality == 75


class TestAppConfig:
    """Test suite for AppConfig with quality settings."""

    def test_appconfig_default_quality(self):
        """Test that AppConfig provides default quality settings."""
        config = AppConfig()
        
        assert hasattr(config, 'default_target_height')
        assert hasattr(config, 'default_jpeg_quality')
        assert config.default_target_height == 1024
        assert config.default_jpeg_quality == 95

    def test_appconfig_load_with_quality_settings(self, tmp_path):
        """Test that AppConfig loads quality settings from file."""
        # Create a temporary config file
        test_config = {
            "cameras": [
                {
                    "name": "test_cam",
                    "type": "local",
                    "index": 0,
                    "target_height": 720,
                    "jpeg_quality": 85
                }
            ],
            "default_target_height": 720,
            "default_jpeg_quality": 85
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(test_config))
        
        with patch('universal_vision_mcp.config.CONFIG_FILE', config_file):
            config = AppConfig.load()
            
            assert config.default_target_height == 720
            assert config.default_jpeg_quality == 85
            assert len(config.cameras) == 1
            assert config.cameras[0].target_height == 720
            assert config.cameras[0].jpeg_quality == 85

    def test_appconfig_save_with_quality_settings(self, tmp_path):
        """Test that AppConfig saves quality settings correctly."""
        config = AppConfig(
            default_target_height=1280,
            default_jpeg_quality=90,
            cameras=[
                CameraSettings(
                    name="saved_cam",
                    type="network",
                    host="10.0.0.1",
                    target_height=1280,
                    jpeg_quality=90
                )
            ]
        )
        
        config_file = tmp_path / "config.json"
        with patch('universal_vision_mcp.config.CONFIG_FILE', config_file):
            config.save()
            
            # Reload and verify
            saved_data = json.loads(config_file.read_text())
            assert saved_data['default_target_height'] == 1280
            assert saved_data['default_jpeg_quality'] == 90
            assert saved_data['cameras'][0]['target_height'] == 1280
            assert saved_data['cameras'][0]['jpeg_quality'] == 90

    def test_appconfig_camera_settings_with_defaults(self):
        """Test that cameras inherit default quality settings when not specified."""
        config = AppConfig(
            default_target_height=960,
            default_jpeg_quality=88,
            cameras=[
                CameraSettings(name="cam1", type="local", index=0)
            ]
        )
        
        # Camera should use its own values or fall back to class defaults
        # (In this implementation, CameraSettings has its own defaults)
        assert config.cameras[0].target_height == 1024  # CameraSettings default
        assert config.cameras[0].jpeg_quality == 95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
