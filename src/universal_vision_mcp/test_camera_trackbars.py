"""Tests for real-time parameter adjustment via OpenCV trackbars."""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestCameraTrackbars:
    """Test suite for trackbar-based parameter adjustment."""

    def test_trackbar_callback_resolution(self):
        """Test that resolution trackbar updates target_height."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        initial_height = cam.target_height
        
        # Simulate trackbar callback
        cam.on_target_height_change(768)
        
        assert cam.target_height == 768

    def test_trackbar_callback_quality(self):
        """Test that quality trackbar updates jpeg_quality."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        initial_quality = cam.jpeg_quality
        
        # Simulate trackbar callback
        cam.on_jpeg_quality_change(80)
        
        assert cam.jpeg_quality == 80

    def test_osd_shows_updated_params(self):
        """Test that OSD displays updated parameter values."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam", target_height=1024, jpeg_quality=95)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Update parameters
        cam.target_height = 768
        cam.jpeg_quality = 80
        
        result = cam.render_osd(frame)
        
        # OSD should contain updated values
        # We can't easily check text content, but we can verify frame is modified
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)

    def test_trackbar_ranges(self):
        """Test that trackbar ranges are correctly defined."""
        from universal_vision_mcp.camera import BaseCamera
        
        # Check class constants for trackbar ranges
        assert hasattr(BaseCamera, 'MIN_TARGET_HEIGHT')
        assert hasattr(BaseCamera, 'MAX_TARGET_HEIGHT')
        assert hasattr(BaseCamera, 'MIN_JPEG_QUALITY')
        assert hasattr(BaseCamera, 'MAX_JPEG_QUALITY')
        
        assert BaseCamera.MIN_TARGET_HEIGHT == 512
        assert BaseCamera.MAX_TARGET_HEIGHT == 1568
        assert BaseCamera.MIN_JPEG_QUALITY == 50
        assert BaseCamera.MAX_JPEG_QUALITY == 98

    def test_create_trackbars(self):
        """Test that trackbars can be created without errors."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Mock cv2 functions to avoid actual window creation
        with patch('universal_vision_mcp.camera.cv2.createTrackbar') as mock_create:
            cam.create_trackbars("test_window")
            
            # Should create 2 trackbars
            assert mock_create.call_count == 2

    def test_trackbar_values_persist(self):
        """Test that trackbar values persist across multiple changes."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Multiple changes
        cam.on_target_height_change(640)
        cam.on_jpeg_quality_change(70)
        cam.on_target_height_change(1280)
        cam.on_jpeg_quality_change(90)
        
        # Final values should persist
        assert cam.target_height == 1280
        assert cam.jpeg_quality == 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
