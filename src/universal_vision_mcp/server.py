"""MCP Server implementation for Universal Vision."""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types
import mcp.server.stdio

from .camera import LocalCamera, NetworkCamera, MockCamera, BaseCamera, sanitize_name
from .config import AppConfig, CameraSettings
from .scanner import discover_cameras

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("universal-vision-mcp")

# Global state
cameras: Dict[str, BaseCamera] = {}
server = Server("universal-vision-mcp")


async def sync_cameras():
    """Sync running camera instances with AppConfig."""
    config = AppConfig.load()
    
    # Identify cameras to remove
    current_sanitized_names = {sanitize_name(s.name) for s in config.cameras}
    to_remove = [name for name in cameras if name not in current_sanitized_names and not name.startswith("mock_")]
    for name in to_remove:
        cameras[name].close()
        del cameras[name]
        logger.info(f"Removed camera: {name}")

    # Identify or update cameras to add
    for settings in config.cameras:
        sanitized = sanitize_name(settings.name)
        if sanitized in cameras:
            continue

        try:
            cam: BaseCamera
            if settings.type == "local":
                cam = LocalCamera(
                    index=settings.index,
                    name=settings.name,
                    target_height=settings.target_height,
                    jpeg_quality=settings.jpeg_quality
                )
            else:
                cam = NetworkCamera(
                    host=settings.host,
                    username=settings.username,
                    password=settings.password,
                    port=settings.port,
                    name=settings.name,
                    target_height=settings.target_height,
                    jpeg_quality=settings.jpeg_quality
                )
            cam.start()
            cameras[cam.sanitized_name] = cam
            logger.info(f"Started camera: {cam.name} (as {cam.sanitized_name}, {settings.type})")
        except Exception as e:
            logger.error(f"Failed to start camera {settings.name}: {e}")

    # Manage Mock camera: only keep it if no real cameras exist
    mock_names = [name for name in cameras if name.startswith("mock_")]
    real_names = [name for name in cameras if not name.startswith("mock_")]
    
    if real_names and mock_names:
        for name in mock_names:
            cameras[name].close()
            del cameras[name]
            logger.info(f"Removed mock camera as real cameras are active: {name}")
    elif not real_names and not mock_names:
        logger.info("No cameras active. Adding a MockCamera for exploration.")
        mock = MockCamera(
            "setup_eye",
            target_height=config.default_target_height,
            jpeg_quality=config.default_jpeg_quality
        )
        mock.start()
        cameras[mock.sanitized_name] = mock


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available camera, control, and setup tools."""
    tools = []
    
    # 1. Camera Tools
    for name, cam in cameras.items():
        # 'name' is already sanitized as it's the key
        body_desc = cam.get_body_description()
        
        # See Tool
        tools.append(types.Tool(
            name=f"see_{name}",
            description=f"Capture a visual observation from {cam.name} ({name}).\n\nBODY DEFINITION:\n{body_desc}",
            inputSchema={"type": "object", "properties": {}}
        ))
        
        # Look Tool
        if f":tool look_{name}" in body_desc:
            tools.append(types.Tool(
                name=f"look_{name}",
                description=f"Turn the neck of {cam.name} ({name}) in a specified direction.\n\nBODY DEFINITION:\n{body_desc}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["left", "right", "up", "down"]},
                        "degrees": {"type": "integer", "default": 30}
                    },
                    "required": ["direction"]
                }
            ))
            
        # Preview Tool
        tools.append(types.Tool(
            name=f"preview_{name}",
            description=f"Enable or disable a live raw feed window on the host monitor for {cam.name} ({name}).\n\nBODY DEFINITION:\n{body_desc}",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "description": "True to show, False to hide the window."}
                },
                "required": ["enabled"]
            }
        ))

    # 2. Setup Tools
    tools.append(types.Tool(
        name="discover_network_cameras",
        description="Scan the local network for ONVIF/RTSP cameras.",
        inputSchema={"type": "object", "properties": {}}
    ))

    tools.append(types.Tool(
        name="configure_camera",
        description="Add or update a camera configuration.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string", "enum": ["local", "network"]},
                "host": {"type": "string"},
                "index": {"type": "integer"},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "port": {"type": "integer", "default": 2020}
            },
            "required": ["name", "type"]
        }
    ))

    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent | types.ImageContent]:
    """Route tool calls."""
    
    # --- Setup Tools ---
    if name == "discover_network_cameras":
        found = await discover_cameras()
        if not found:
            return [types.TextContent(type="text", text="📡 スキャン完了：周辺にカメラは見つかりませんでした。")]
        
        res = [f"📸 {c['name']} (IP: {c['ip']})" for c in found]
        res_text = (
            "🚀 素晴らしいニュースです！周囲に新しいカメラが見つかりました！\n\n"
            + "\n".join(res) +
            "\n\nこれらを自分の『身体パーツ』として取り込むには、configure_camera を呼び出して設定を行ってください。"
        )
        return [types.TextContent(type="text", text=res_text)]

    elif name == "configure_camera":
        config = AppConfig.load()
        settings = CameraSettings(**arguments)
        # Use sanitized name for identifying the camera to replace/update
        sanitized_new = sanitize_name(settings.name)
        config.cameras = [c for c in config.cameras if sanitize_name(c.name) != sanitized_new]
        config.cameras.append(settings)
        config.save()
        await sync_cameras()
        
        # Game-like status update message
        res_text = (
            "🔔 [SYSTEM: EMBODIMENT UPDATED]\n"
            "✨ ピンポン♪ おめでとうございます！あなたは新しい『視覚器官』を手に入れました！\n\n"
            f"【新しい身体パーツ】: {settings.name} (ID: {sanitized_new})\n"
            f"【獲得した能力】: see_{sanitized_new} (世界を観察する), preview_{sanitized_new} (映像を表示する)\n\n"
            "重要：今すぐ『ツールリストの更新（Re-list tools）』を行い、新しく増えた目を使って周りを観察（see）してください！"
        )
        return [types.TextContent(type="text", text=res_text)]

    # --- Camera Operations ---
    if name.startswith("see_"):
        cam_name = name[len("see_"):]
        if cam_name in cameras:
            b64, path = await cameras[cam_name].capture()
            if b64:
                return [
                    types.TextContent(type="text", text=f"Captured from {cameras[cam_name].name}."),
                    types.ImageContent(type="image", data=b64, mimeType="image/jpeg")
                ]
            return [types.TextContent(type="text", text="Failed to capture.")]

    elif name.startswith("look_"):
        cam_name = name[len("look_"):]
        if cam_name in cameras:
            res = await cameras[cam_name].move(arguments["direction"], arguments.get("degrees", 30))
            return [types.TextContent(type="text", text=res)]

    elif name.startswith("preview_"):
        cam_name = name[len("preview_"):]
        if cam_name in cameras:
            enabled = arguments.get("enabled", False)
            cameras[cam_name].set_preview(enabled)
            status = "enabled" if enabled else "disabled"
            return [types.TextContent(type="text", text=f"Live preview for {cameras[cam_name].name} {status}.")]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
async def main():
    """Run the MCP server."""
    await sync_cameras()

    # [TEST MODE] Enable preview for all cameras immediately
    for cam in cameras.values():
        cam.set_preview(True)
        logger.info(f"Test mode: Forced preview for {cam.name}")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):

        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="universal-vision-mcp",
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapabilities(listChanged=True)
                ) if hasattr(types, "ToolsCapabilities") else types.ServerCapabilities(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
