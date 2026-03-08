# USB Camera Integration Test

## Purpose

Verify that USB cameras connected to Windows/WSL environments are properly recognized and can capture images through the Universal Vision MCP server.

---

## Prerequisites

- USB camera connected to the system
- Python 3.11+ with `uv` installed
- Universal Vision MCP installed (`uv sync`)

---

## Test Procedure

### Step 1: Camera Detection

```bash
uv run universal-vision-mcp doctor
```

**Expected Output**:
```
Local USB Cameras
┌───────┬──────────────┬────────────────────────┬─────────────────────┐
│ Index │ Sanitized    │ Status                 │ Body Definition     │
│       │ Name         │                        │                     │
├───────┼──────────────┼────────────────────────┼─────────────────────┤
│ 0     │ usb_eye_0    │ AVAILABLE (640x480)    │ (body :id ...)      │
│ 1     │ -            │ NOT FOUND              │ -                   │
└───────┴──────────────┴────────────────────────┴─────────────────────┘
```

**Pass Criteria**:
- Camera is detected at an index (typically 0)
- Status shows "AVAILABLE" with resolution

---

### Step 2: Test Capture

```bash
uv run universal-vision-mcp test-capture --name usb_eye_0 --count 3 --interval 1.0
```

**Expected Output**:
```
Started camera: usb_eye_0
Settings: 1024p, JPEG 95%
Saving to: var/test_captures/

Capture 1/3...
OK Saved: var/test_captures/usb_eye_0_test_20260308_123456.jpg

Capture 2/3...
OK Saved: var/test_captures/usb_eye_0_test_20260308_123457.jpg

Capture 3/3...
OK Saved: var/test_captures/usb_eye_0_test_20260308_123458.jpg

Test complete! 3 capture(s) saved.
```

**Pass Criteria**:
- At least 2 out of 3 captures succeed
- Images are saved to `var/test_captures/`
- Image files are valid JPEGs

---

## Troubleshooting

### Issue: Camera not detected

**Symptoms**:
```
Index 0: - NOT FOUND
```

**Solutions**:
1. Check camera connection
2. Verify camera is not in use by another application
3. Restart the system

---

### Issue: Capture fails with error -1072875772

**Symptoms**:
```
[WARN] videoio(MSMF): can't grab frame. Error: -1072875772
```

**Solutions**:
1. Close other applications using the camera (Zoom, Teams, browser)
2. Kill Python processes: `taskkill /F /IM python.exe`
3. Reduce `target_height` in config to match camera's native resolution

---

### Issue: First capture fails

**Symptoms**:
- Capture 1/3: Fail
- Capture 2/3: OK
- Capture 3/3: OK

**Solution**:
- Increase initialization sleep time in `cli.py::test_capture()`:
  ```python
  time.sleep(0.5) → time.sleep(1.0)
  ```

---

## Configuration

### Camera Settings

Edit `~/.universal-vision-mcp/config.json`:

```json
{
  "cameras": [
    {
      "name": "usb_eye_0",
      "type": "local",
      "index": 0,
      "target_height": 480,
      "jpeg_quality": 95
    }
  ]
}
```

**Note**: Set `target_height` to match your camera's native resolution (e.g., 480 for 640x480 cameras).

---

## Test Report Template

| Item | Result |
|------|--------|
| **Date** | YYYY-MM-DD |
| **Tester** | Name |
| **Camera Model** | Model name |
| **Resolution** | e.g., 640x480 |
| **Detection** | ✅ Pass / ❌ Fail |
| **Capture (1/3)** | ✅ / ❌ |
| **Capture (2/3)** | ✅ / ❌ |
| **Capture (3/3)** | ✅ / ❌ |
| **Notes** | Any observations |

---

## Related Documents

- [Test Results 2026-03-08](./test-results-2026-03-08.md)
- [Recording OSD Test](./recording-osd-test.md)
