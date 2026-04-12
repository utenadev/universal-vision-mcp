# Universal Vision MCP 👁️

> **"Give your AI real 'eyes' and a 'neck'."**

Universal Vision MCP is a tool that allows AI agents (like Claude) to directly control the cameras connected to your computer.
With this, your AI can see the world around you, pan and tilt network cameras, and explore its surroundings.

## 🌟 What can it do?

![Mock Camera Preview](assets/mock-preview.png)
<br>*(Visual feedback from the AI's perspective using a Mock camera)*

- **Supports Various Cameras**: Whether it's a built-in webcam, a USB camera, or a professional IP camera (RTSP/ONVIF), the AI treats them all with a unified interface.
- **AI Understands Its Own "Body"**: The AI intuitively knows whether its "neck" is fixed or can pan/tilt, and acts accordingly.
- **Autonomous Discovery**: The AI can scan your local network to find new cameras and help you set them up.
- **Live Preview Window**: Ask the AI to "show the camera feed," and it can open a real-time preview window right on your monitor.

## 🚀 Getting Started

No complex programming or cloning required. You can start in just a few steps.

### 1. Install [uv](https://docs.astral.sh/uv/)
Install `uv`, the lightning-fast Python runner (one-liner).

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Register to MCP Client

#### Claude Desktop (stdio mode)

Run the following command in your terminal:

```bash
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp setup --setup-cmd-cd
```

Copy the **`mcpServers`** configuration snippet shown in the terminal, paste it into your `claude_desktop_config.json`, and restart Claude. That's it!

#### HTTP Mode (for SSE / Streamable HTTP compatible clients)

For clients that support SSE or Streamable HTTP (Claude Code, and some MCP clients), you can run the server in HTTP mode:

```bash
# Start HTTP server (default: 127.0.0.1:8000)
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http

# Custom port
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http --port 3000
```

**Endpoints:**
- SSE: `http://<server-ip>:8000/sse`
- Streamable HTTP: `http://<server-ip>:8000/mcp`

**Claude Code registration example:**
```bash
claude mcp add universal-vision --transport sse http://<server-ip>:8000/sse
```

Or add directly to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "universal-vision": {
      "url": "http://<server-ip>:8000/mcp"
    }
  }
}
```

#### LAN Access (Connecting from Other Machines)

To allow connections from other machines on the same LAN, use the `--lan` option:

```bash
# Start in LAN mode (binds to 0.0.0.0)
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http --lan
```

> ⚠️ **Important: LAN-only usage assumed**
> LAN mode has no authentication and binds to `0.0.0.0`.
> Use only within a **trusted LAN**. Do NOT expose to the internet.

#### WSL2 / Windows Cross-Connection

To run the server on Windows and connect from WSL2:

**1. Start server on Windows:**
```powershell
# Run in PowerShell (use --lan to allow LAN connections)
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp run --http --lan
```

**2. Get Windows IP address (from WSL2):**
```bash
# Run in WSL2
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

**3. Connect from WSL2 client:**
```bash
# Use the IP address obtained (e.g., 172.xx.xx.1)
claude mcp add universal-vision --transport sse http://172.xx.xx.1:8000/sse
```

## 🛠️ Handy Commands (Troubleshooting)

You can run diagnostics or re-configure settings at any time without installation.

```bash
# Check if your cameras are correctly recognized (Diagnostics)
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp doctor --enable-netscan

# Add a network camera or change settings
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp setup

# Test capture (for quality verification)
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp test-capture --name mock_eye --count 3
```

## 🆕 What's New (2026-04-11 Update)

### 🌐 HTTP Transport Support

Now supports SSE (Server-Sent Events) and Streamable HTTP transports, making it accessible from more MCP clients.

- **SSE Transport**: `/sse` endpoint
- **Streamable HTTP Transport**: `/mcp` endpoint
- **Stateless Mode**: Scalable JSON response mode

```bash
# Run in HTTP mode
uv run universal-vision-mcp run --http --port 8000
```

---

## 🆕 What's New (2026-03-07 Update)

### 📸 OSD (On-Screen Display) Features

Preview window now displays various information:

- **Capture Flash**: Green flash overlay with "Now Capturing!!" text (0.5 seconds) when using `test-capture` command
  - ⚠️ **Note**: Flash does NOT appear for AI captures (via `see_...` tools)
- **Quality Parameters**: Always shows "RES: 1024p | QUAL: 95%" at the bottom of the screen
- **Recording Indicator**: Displays "● REC ..." with elapsed time while recording (blinks every 1 second)
  - ⚠️ **Note**: No MCP tool for recording start/stop (manual operation only)

### 🎚️ Real-time Quality Adjustment

Adjust the following parameters in real-time using trackbars on the preview window:

- **Resolution**: 512px to 1568px (default: 1024px)
- **JPEG Quality**: 50% to 98% (default: 95%)

> ⚠️ **Note**: AI captures always use fixed 1024px / 95% (settings do not affect AI image quality)

### 🧪 Benchmark Tools

New tools for measuring image recognition accuracy:

```bash
# Finger counting test
uv run python src/universal_vision_mcp/benchmark_recognition.py --task finger_count --iterations 5

# Text recognition test
uv run python src/universal_vision_mcp/benchmark_recognition.py --task text_read --iterations 3
```

> ⚠️ **This tool is currently a simulator**: Does not call actual LLM APIs, returns random-based results

### 📋 Extended Configuration

Manage quality settings in `~/.universal-vision-mcp/config.json`:

```json
{
  "cameras": [
    {
      "name": "usb_eye_0",
      "type": "local",
      "index": 0,
      "target_height": 1024,
      "jpeg_quality": 95
    }
  ],
  "default_target_height": 1024,
  "default_jpeg_quality": 95
}
```

---

## 👨‍💻 For Developers

If you want to customize the code or build it yourself:

### Setup
```bash
git clone https://github.com/utenadev/universal-vision-mcp
cd universal-vision-mcp
uv sync
```

### Run/Diagnose
```bash
# stdio mode (default)
uv run universal-vision-mcp doctor
uv run universal-vision-mcp run

# HTTP mode (SSE + Streamable HTTP)
uv run universal-vision-mcp run --http --port 8000
```

## 🧠 Tech Stack & Philosophy

- **Python 3.11+ / MCP Python SDK**: Model Context Protocol compliant.
- **Multiple Transports**: Supports stdio / SSE / Streamable HTTP.
- **OpenCV**: Video capture and real-time preview windows.
- **ONVIF**: PTZ (Pan-Tilt-Zoom) control for network cameras.
- **Self-Description via S-expressions**: This server injects physical descriptions into tool descriptions:
  ```lisp
  (part :id garden_cam :type network :tool see_garden_cam :desc "...")
  ```
  This allows the LLM to gain a **"body sense" (Embodiment)**, understanding its own physical capabilities.

## ❤️ Acknowledgments

This project is deeply inspired by the pioneering work of **kmizu (lifemate-ai)** (`embodied-claude`, `familiar-ai`). We owe a great debt of gratitude for the concept of giving AI a physical form.

## 📜 License
MIT License
