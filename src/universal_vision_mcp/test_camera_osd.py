"""Tests for OSD (On-Screen Display) functionality in camera module."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestCameraOSD:
    """Test suite for capture OSD display functionality."""

    def test_capture_flag_initial_state(self):
        """Test that capture_requested flag is False by default."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        assert hasattr(cam, '_capture_requested')
        assert cam._capture_requested is False

    def test_trigger_capture_sets_flag(self):
        """Test that trigger_capture() sets the capture request flag."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.trigger_capture()
        assert cam._capture_requested is True

    def test_capture_timestamp_updated_on_trigger(self):
        """Test that capture timestamp is updated when capture is triggered."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        before_time = time.time()
        cam.trigger_capture()
        after_time = time.time()
        
        assert hasattr(cam, '_capture_timestamp')
        assert before_time <= cam._capture_timestamp <= after_time

    def test_flash_duration_expires(self):
        """Test that flash effect expires after 0.5 seconds."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.trigger_capture()
        
        # Immediately should be in flash period
        assert cam.is_flash_active() is True
        
        # Wait for flash to expire (0.5s + buffer)
        time.sleep(0.6)
        assert cam.is_flash_active() is False

    def test_osd_text_rendering(self):
        """Test that OSD text can be rendered on frame without errors."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Should not raise any errors
        result = cam.render_osd(frame)
        
        assert result is not None
        assert result.shape == frame.shape
        assert result.dtype == np.uint8

    def test_quality_params_display(self):
        """Test that quality parameters are stored and accessible."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Default values should exist
        assert hasattr(cam, 'target_height')
        assert hasattr(cam, 'jpeg_quality')
        assert cam.target_height > 0
        assert 0 < cam.jpeg_quality <= 100

    def test_osd_includes_quality_info(self):
        """Test that OSD displays current quality settings."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam", target_height=1024, jpeg_quality=95)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = cam.render_osd(frame)
        
        # Frame should be modified (OSD rendered)
        assert not np.array_equal(result, frame)

    def test_multiple_capture_triggers(self):
        """Test that multiple rapid triggers don't cause issues."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Trigger multiple times rapidly
        cam.trigger_capture()
        cam.trigger_capture()
        cam.trigger_capture()
        
        # Should still be in valid state
        assert cam._capture_requested is True

    def test_flash_does_not_affect_performance(self):
        """Test that OSD rendering doesn't significantly slow down frame processing."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Measure rendering time
        start = time.perf_counter()
        for _ in range(100):
            cam.render_osd(frame)
        elapsed = time.perf_counter() - start
        
        # Should render 100 frames in under 0.5 seconds (5ms per frame max)
        assert elapsed < 0.5, f"OSD rendering too slow: {elapsed*1000:.2f}ms per frame"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
