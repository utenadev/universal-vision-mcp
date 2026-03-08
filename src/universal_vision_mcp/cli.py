"""CLI for Universal Vision MCP (doctor, setup, run)."""

import asyncio
import os
import shutil
import sys
import time
from typing import Optional

import cv2
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import AppConfig, CameraSettings
from .camera import LocalCamera, NetworkCamera, MockCamera, sanitize_name, TEST_CAPTURE_DIR
from .scanner import discover_cameras

app = typer.Typer(help="Universal Vision MCP CLI - Control your eyes and neck.")
console = Console()

GITHUB_URL = "https://github.com/utenadev/universal-vision-mcp"


@app.command()
def doctor(
    enable_netscan: bool = typer.Option(False, "--enable-netscan", help="Enable network camera scanning (may take a few seconds)")
):
    """Diagnose local hardware, network cameras, and show S-expression descriptions."""
    console.print(Panel("[bold cyan]Universal Vision Doctor[/] - Running diagnosis..."))

    # 1. Local USB Scan
    table = Table(title="Local USB Cameras")
    table.add_column("Index", style="cyan")
    table.add_column("Sanitized Name", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Body Definition (S-expression)", style="yellow")

    for i in range(4):  # Scan first 4 indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            name = f"usb_eye_{i}"
            cam = LocalCamera(index=i, name=name)
            s_expr = cam.get_body_description()
            
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            table.add_row(str(i), cam.sanitized_name, f"AVAILABLE ({int(w)}x{int(h)})", s_expr)
            cap.release()
        else:
            table.add_row(str(i), "-", "NOT FOUND", "-")

    console.print(table)

    # 2. Network Discovery
    if enable_netscan:
        console.print("\n[bold cyan]Scanning Network for Cameras...[/] (mDNS / PortScan)")
        found = asyncio.run(discover_cameras())
        
        if found:
            net_table = Table(title="Network Cameras (Found)")
            net_table.add_column("IP", style="cyan")
            net_table.add_column("Source", style="green")
            net_table.add_column("Sanitized Name", style="magenta")
            net_table.add_column("Body Definition (S-expression)", style="yellow")
            
            for c in found:
                # Create a temporary NetworkCamera instance for S-expression preview
                cam = NetworkCamera(host=c['ip'], name=c.get('name', 'network_eye'))
                s_expr = cam.get_body_description()
                net_table.add_row(c['ip'], c['source'], cam.sanitized_name, s_expr)
                
            console.print(net_table)
        else:
            console.print("  [yellow]No network cameras found on the local segment.[/]")
    else:
        console.print("\n[dim]Network scan skipped. Use --enable-netscan to scan network cameras.[/]")

    # 3. Virtual/Mock (Fallback)
    console.print("\n[bold cyan]Mock/Virtual (Fallback) Definition:[/]")
    mock = MockCamera("mock_eye")
    console.print(Panel(mock.get_body_description(), border_style="dim"))

    console.print("\n[bold green]Diagnosis Complete.[/]")


@app.command()
def setup(
    cmd_cd: bool = typer.Option(False, "--setup-cmd-cd", help="Show Claude Desktop registration JSON"),
    cmd_cc: bool = typer.Option(False, "--setup-cmd-cc", help="Show Claude Code registration command"),
    cmd_gemini: bool = typer.Option(False, "--setup-cmd-gemini", help="Show Gemini registration instruction"),
    export_setup: bool = typer.Option(False, "--export-setup", help="Export current configuration to setup.json in the current directory"),
):
    """Interactive setup for your cameras or show registration commands."""
    
    # Try to find the full path of uv for maximum reliability
    uv_raw = shutil.which("uv") or "uv"
    # For JSON backslashes need to be escaped
    uv_path = uv_raw.replace("\\", "\\\\")
    
    # Point to the current fix branch for verification
    branch_suffix = "@fix/tool-name-validation-and-features"
    current_git_url = f"{GITHUB_URL}{branch_suffix}"

    if cmd_cd:
        console.print("\n[bold cyan]Claude Desktop Configuration (JSON snippet):[/]")
        console.print("Add this to your `claude_desktop_config.json`:")
        
        config_json = f"""
{{
  "mcpServers": {{
    "universal-vision": {{
      "command": "{uv_path}",
      "args": [
        "tool",
        "run",
        "--from",
        "git+{current_git_url}",
        "universal-vision-mcp",
        "run"
      ],
      "env": {{
        "CAMERA_INDEX": "0"
      }}
    }}
  }}
}}
"""
        console.print(config_json.strip())
        if "\\" in uv_raw:
            console.print("\n[dim]Tip: Full path to 'uv' used for Windows compatibility.[/]")
        return

    if cmd_cc:
        console.print("\n[bold cyan]Claude Code Registration Command:[/]")
        console.print(f"Run this command in your terminal:")
        console.print(f"\nclaude mcp add universal-vision {uv_raw} tool run --from git+{current_git_url} universal-vision-mcp run\n")
        return

    if cmd_gemini:
        console.print("\n[bold cyan]Gemini Registration (gemini-cli):[/]")
        console.print("If you are using Gemini CLI, you can register it using your environment setup:")
        console.print(f"\n{uv_raw} tool run --from git+{current_git_url} universal-vision-mcp run\n")
        return

    if export_setup:
        config = AppConfig.load()
        export_path = os.path.join(os.getcwd(), "setup.json")
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))
        console.print(f"\n[bold green]Configuration exported to {export_path}[/]")
        return

    config = AppConfig.load()
    console.print(Panel("[bold green]Interactive Setup[/] - Let's configure your eyes!"))

    # Auto-detect local cams
    auto_detect = typer.confirm("Do you want to auto-detect and add local USB cameras?")
    if auto_detect:
        for i in range(4):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                name = f"usb_eye_{i}"
                if not any(c.index == i and c.type == "local" for c in config.cameras):
                    config.cameras.append(CameraSettings(name=name, type="local", index=i))
                    console.print(f"Added [cyan]{name}[/] (Local Camera {i})")
                cap.release()

    # Manual Network Add
    add_net = typer.confirm("Do you want to add a Network (IP) Camera?")
    if add_net:
        name = typer.prompt("Camera name (e.g. garden_cam)", default="network_cam")
        host = typer.prompt("Camera IP or Hostname")
        username = typer.prompt("Username (optional)", default="")
        password = typer.prompt("Password (optional)", default="", hide_input=True)
        port = int(typer.prompt("ONVIF Port", default="2020"))

        config.cameras.append(CameraSettings(
            name=name,
            type="network",
            host=host,
            username=username if username else None,
            password=password if password else None,
            port=port
        ))
        console.print(f"Added [cyan]{name}[/] (Network Camera at {host})")

    config.save()
    console.print("\n[bold green]Configuration saved![/]")


@app.command()
def test_capture(
    camera_name: str = typer.Option("mock_eye", "--name", "-n", help="Camera name to test"),
    count: int = typer.Option(1, "--count", "-c", help="Number of test captures"),
    interval: float = typer.Option(1.0, "--interval", "-i", help="Interval between captures in seconds"),
):
    """Take test captures and save to var/test_captures/."""
    console.print(Panel(f"[bold cyan]Test Capture[/] - Testing {camera_name}"))
    
    # Create camera instance
    cam: MockCamera | LocalCamera | NetworkCamera
    if camera_name == "mock_eye" or camera_name.startswith("mock"):
        cam = MockCamera(camera_name)
    else:
        # Try to find in config
        config = AppConfig.load()
        settings = next((c for c in config.cameras if sanitize_name(c.name) == sanitize_name(camera_name)), None)
        if settings is None:
            console.print(f"[red]Camera '{camera_name}' not found in config.[/]")
            console.print("Use 'mock_eye' for test capture without hardware.")
            raise typer.Exit(1)
        
        if settings.type == "local":
            cam = LocalCamera(index=settings.index, name=settings.name, target_height=settings.target_height, jpeg_quality=settings.jpeg_quality)
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
    console.print(f"Started camera: {cam.name}")
    console.print(f"Settings: {cam.target_height}p, JPEG {cam.jpeg_quality}%")
    console.print(f"Saving to: {TEST_CAPTURE_DIR}")
    
    try:
        # Wait for camera to initialize
        console.print("\nInitializing camera...")
        time.sleep(0.5)
        
        for i in range(count):
            if count > 1:
                console.print(f"\nCapture {i+1}/{count}...")
            
            result = cam.test_capture()
            
            if result:
                console.print(f"[green]OK Saved:[/] {result}")
            else:
                console.print("[red]NG Failed to capture[/]")
            
            if i < count - 1:
                time.sleep(interval)
        
        console.print(f"\n[bold green]Test complete![/] {count} capture(s) saved.")
        
    finally:
        cam.close()
        console.print("\nCamera resources released.")


@app.command()
def run():
    """Start the MCP Server."""
    import asyncio
    from .server import main as server_main
    asyncio.run(server_main())


def main():
    app()


if __name__ == "__main__":
    main()
