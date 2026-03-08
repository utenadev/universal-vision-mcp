"""Tests for test capture functionality."""

import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile


class TestCaptureFunctionality:
    """Test suite for test capture functionality."""

    def test_test_capture_exists(self):
        """Test that test_capture method exists."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        assert hasattr(cam, 'test_capture')

    def test_test_capture_returns_path(self):
        """Test that test_capture returns a file path."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start()
        
        try:
            # Give camera time to initialize
            time.sleep(0.2)
            
            # Test capture should return a path
            result = cam.test_capture()
            
            assert result is not None
            assert isinstance(result, str)
        finally:
            cam.close()

    def test_test_capture_saves_file(self):
        """Test that test_capture actually saves a file."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start()
        
        try:
            time.sleep(0.2)
            result = cam.test_capture()
            
            # File should exist
            assert Path(result).exists()
        finally:
            cam.close()

    def test_test_capture_filename_format(self):
        """Test that test capture filename follows expected format."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start()
        
        try:
            time.sleep(0.2)
            result = cam.test_capture()
            
            # Filename should contain camera name and timestamp
            filename = Path(result).name
            assert "test_cam" in filename or "testcam" in filename
            assert filename.endswith(".jpg")
        finally:
            cam.close()

    def test_test_capture_directory(self):
        """Test that test captures are saved to var/test_captures/."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start()
        
        try:
            time.sleep(0.2)
            result = cam.test_capture()
            
            # Should be in test_captures directory
            assert "test_captures" in result
        finally:
            cam.close()

    def test_test_capture_with_osd(self):
        """Test that test_capture triggers OSD flash."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start()
        
        try:
            time.sleep(0.2)
            
            # Trigger capture
            cam.test_capture()
            
            # Should have triggered capture flag
            assert cam._capture_requested is True or cam.is_flash_active()
        finally:
            cam.close()

    def test_multiple_test_captures(self):
        """Test that multiple test captures create separate files."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start()
        
        try:
            time.sleep(0.2)
            
            # Take multiple captures (need 1+ second apart for unique timestamps)
            result1 = cam.test_capture()
            time.sleep(1.1)  # Wait for timestamp to change
            result2 = cam.test_capture()
            
            # Should be different files
            assert result1 != result2
            assert Path(result1).exists()
            assert Path(result2).exists()
        finally:
            cam.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
