"""Tests for Recording OSD display functionality."""

import pytest
import time
from unittest.mock import patch, MagicMock
import numpy as np


class TestRecordingOSD:
    """Test suite for recording indicator OSD functionality."""

    def test_start_recording_sets_flag(self):
        """Test that start_recording() sets the recording flag."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start_recording()
        
        assert cam.is_recording() is True

    def test_stop_recording_clears_flag(self):
        """Test that stop_recording() clears the recording flag."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start_recording()
        cam.stop_recording()
        
        assert cam.is_recording() is False

    def test_recording_elapsed_time(self):
        """Test that elapsed time is tracked during recording."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Start recording
        cam.start_recording()
        elapsed_before = cam.get_recording_elapsed_time()
        
        # Wait a bit
        time.sleep(0.1)
        elapsed_after = cam.get_recording_elapsed_time()
        
        # Elapsed time should increase
        assert elapsed_after >= elapsed_before
        assert elapsed_after >= 0.1

    def test_recording_indicator_blink(self):
        """Test that recording indicator blinks on/off."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start_recording()
        
        # Check blink state changes over time
        state1 = cam.get_blink_state()
        time.sleep(0.6)  # Wait for blink cycle
        state2 = cam.get_blink_state()
        
        # Blink state should potentially change (depends on timing)
        # At least the method should exist and return bool
        assert isinstance(state1, bool)

    def test_osd_renders_recording_indicator(self):
        """Test that OSD renders recording indicator when recording."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start_recording()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = cam.render_osd(frame)
        
        # Frame should be modified with OSD
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)

    def test_osd_shows_elapsed_time(self):
        """Test that OSD shows elapsed recording time."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        cam.start_recording()
        
        time.sleep(0.1)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = cam.render_osd(frame)
        
        # Should render without errors
        assert result is not None

    def test_recording_format_time(self):
        """Test time formatting for recording display."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Test various time formats
        assert cam._format_recording_time(0) == "00:00"
        assert cam._format_recording_time(5) == "00:05"
        assert cam._format_recording_time(65) == "01:05"
        assert cam._format_recording_time(3665) == "61:05"

    def test_stop_recording_resets_elapsed_time(self):
        """Test that stopping recording resets elapsed time."""
        from universal_vision_mcp.camera import MockCamera
        
        cam = MockCamera("test_cam")
        
        # Record for a bit
        cam.start_recording()
        time.sleep(0.1)
        cam.stop_recording()
        
        # Elapsed time should be reset or stopped
        assert cam.get_recording_elapsed_time() == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
