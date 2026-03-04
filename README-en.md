# Universal Vision MCP 👁️

> **"Transform any camera into a standardized 'eye' and 'neck' for AI."**

Universal Vision MCP is a Model Context Protocol (MCP) server designed to grant "Embodiment" to AI agents. It integrates USB cameras (built-in), network cameras (RTSP/ONVIF), and virtual mock cameras into a unified framework.

## 🌟 Features

![Mock Camera Preview](assets/mock-preview.jpg)
<br>*(A sample view from the Mock camera as seen by the AI)*

- **Polymorphic Embodiment**: Wraps everything from simple webcams to professional PTZ network cameras in a consistent interface.
- **Self-Describing S-expressions**: Uses Lisp-style S-expressions to help AI intuitively understand its own physical capabilities (e.g., whether its "neck" is fixed or can pan/tilt).
- **Autonomous Discovery**: AI can independently scan the local network to find new cameras and propose configurations to the user.
- **Live Preview**: Allows the AI to open/close an OpenCV preview window on the host machine via tool calls.
- **Friendly CLI**: Includes `doctor` (diagnostics) and `setup` (interactive configuration) subcommands to minimize setup friction.

## 🚀 Getting Started

### 1. Install [uv](https://docs.astral.sh/uv/)
Install the Python package manager `uv` (if not already installed).
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup
```bash
git clone https://github.com/utenadev/universal-vision-mcp
cd universal-vision-mcp
uv sync
```

### 3. Check Hardware
```bash
# Diagnose hardware and preview S-expressions (self-description)
uv run universal-vision-mcp doctor

# Interactive camera setup (to add network cameras, etc.)
uv run universal-vision-mcp setup
```

### 4. Run
```bash
# Start the MCP Server
uv run universal-vision-mcp run
```

When calling from MCP clients like Claude Desktop, set `uv run universal-vision-mcp run` as the launch command.

## 🛠 Technical Stack

- **Python 3.11+**
- **MCP Python SDK**: Compliant with Model Context Protocol.
- **OpenCV (opencv-python)**: Video capture, image processing, and preview windows.
- **ONVIF (onvif-zeep-async)**: Pan-Tilt-Zoom control for network cameras.
- **Zeroconf / Scapy**: Automatic network device discovery.
- **Typer & Rich**: Elegant and user-friendly CLI interface.

## 🧠 Philosophy: Self-Definition via S-expressions

When listing tools, this server injects a physical description (S-expression) into each tool's description field:

```lisp
(part :id garden_cam :type network :tool see_garden_cam
  :desc "Remote network camera via RTSP.")
(part :id neck_garden_cam :type ptz :tool look_garden_cam
  :desc "Motorized neck for garden_cam. No permission needed.")
```

By doing this, the LLM doesn't just call a "function"—it gains a **body sense**, understanding that it has a PTZ-capable eye and can use it to explore its surroundings.

---

## ❤️ Acknowledgments & Respect

This project would not have been possible without the pioneering work of **kmizu (lifemate-ai)**.

- The impact of the attempt to give AI a physical form (Embodiment) in **`embodied-claude`** and **`familiar-ai`**.
- A nostalgic yet new user experience of interacting with AI through **Lisp S-expressions**, a dream once held by engineers.
- We express our heartfelt gratitude for teaching us the ultimate **"Play"** of living with AI.

---

## 📜 License

MIT License - Hack and evolve freely.
