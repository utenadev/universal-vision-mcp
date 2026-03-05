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

## 🚀 Getting Started (Fastest Way)

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

### 2. Register to Claude Desktop
Run the following command in your terminal. This will help you add "eyes" to your Claude.

```bash
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp setup --setup-cmd-cd
```

Copy the **`mcpServers`** configuration snippet shown in the terminal, paste it into your `claude_desktop_config.json`, and restart Claude. That's it!

## 🛠️ Handy Commands (Troubleshooting)

You can run diagnostics or re-configure settings at any time without installation.

```bash
# Check if your cameras are correctly recognized (Diagnostics)
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp doctor --enable-netscan

# Add a network camera or change settings
uvx --from git+https://github.com/utenadev/universal-vision-mcp universal-vision-mcp setup
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
uv run universal-vision-mcp doctor
uv run universal-vision-mcp run
```

## 🧠 Tech Stack & Philosophy

- **Python 3.11+ / MCP Python SDK**: Model Context Protocol compliant.
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
