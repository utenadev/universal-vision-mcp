# Recording OSD Test

## Purpose

Verify that the Recording OSD (On-Screen Display) indicator functions correctly during camera preview.

---

## Features Tested

| Feature | Description |
|---------|-------------|
| **Recording Indicator** | "● REC ..." blinks at 1-second intervals |
| **Elapsed Time** | Recording time displays in MM:SS format |
| **API Functions** | `start_recording()`, `stop_recording()`, `is_recording()`, `get_recording_elapsed_time()` |

---

## Test Procedure

### Step 1: Start Recording

```python
from universal_vision_mcp.camera import MockCamera  # or LocalCamera

cam = MockCamera("mock_eye")
cam.start()
cam.set_preview(True)
cam.start_recording()
```

**Expected Behavior**:
- Preview window opens
- "● REC ..." appears in top-left corner (red text)
- Text blinks at 1-second intervals

---

### Step 2: Verify Elapsed Time

```python
import time

time.sleep(3)
elapsed = cam.get_recording_elapsed_time()
print(f"Elapsed: {elapsed:.2f} seconds")
# Expected: ~3.0 seconds
```

**Expected Behavior**:
- Elapsed time displays in top-right corner (e.g., "00:03")
- Time format is MM:SS

---

### Step 3: Stop Recording

```python
cam.stop_recording()
time.sleep(1)
```

**Expected Behavior**:
- "● REC ..." disappears
- Elapsed time disappears

---

### Step 4: Cleanup

```python
cam.set_preview(False)
cam.close()
```

---

## Visual Verification Checklist

| Item | Status | Notes |
|------|--------|-------|
| Preview window opens | ⬜ Pass / ⬜ Fail | |
| "● REC ..." appears | ⬜ Pass / ⬜ Fail | Red text, top-left |
| Blink at 1-second intervals | ⬜ Pass / ⬜ Fail | |
| Elapsed time displays | ⬜ Pass / ⬜ Fail | Top-right, MM:SS format |
| Recording stops cleanly | ⬜ Pass / ⬜ Fail | |

---

## API Reference

### `start_recording()`

Start recording mode with OSD indicator.

```python
cam.start_recording()
```

---

### `stop_recording()`

Stop recording mode.

```python
cam.stop_recording()
```

---

### `is_recording()`

Check if recording is currently active.

```python
if cam.is_recording():
    print("Recording...")
```

---

### `get_recording_elapsed_time()`

Get elapsed recording time in seconds.

```python
elapsed = cam.get_recording_elapsed_time()
print(f"Recording for {elapsed:.1f} seconds")
```

---

### `_format_recording_time(seconds)`

Format recording time as MM:SS (internal method).

```python
time_text = cam._format_recording_time(125)  # → "02:05"
```

---

## Troubleshooting

### Issue: "● REC ..." does not blink

**Possible Causes**:
- `BLINK_INTERVAL` constant may be incorrect
- System timer precision issues

**Solution**:
- Check `camera.py::BLINK_INTERVAL = 1.0`

---

### Issue: Elapsed time shows incorrect value

**Possible Causes**:
- Timer start time not properly recorded

**Solution**:
- Verify `start_recording()` sets `_recording_start_time`

---

## Test Report Template

| Item | Result |
|------|--------|
| **Date** | YYYY-MM-DD |
| **Tester** | Name |
| **Camera Type** | MockCamera / LocalCamera |
| **Preview Window** | ✅ Opens / ❌ Fails |
| **REC Indicator** | ✅ Blinks / ❌ Fails |
| **Elapsed Time** | ✅ Correct / ❌ Incorrect |
| **API Functions** | ✅ All work / ❌ Issues |
| **Notes** | Any observations |

---

## Related Documents

- [Test Results 2026-03-08](./test-results-2026-03-08.md)
- [USB Camera Test](./usb-camera-test.md)
