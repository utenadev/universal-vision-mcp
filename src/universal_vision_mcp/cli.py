"""CLI for Universal Vision MCP (doctor, setup, run)."""

import asyncio
import os
import sys
from typing import Optional

import cv2
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import AppConfig, CameraSettings
from .camera import LocalCamera, NetworkCamera, MockCamera
from .scanner import discover_cameras

app = typer.Typer(help="Universal Vision MCP CLI - Control your eyes and neck.")
console = Console()


@app.command()
def doctor():
    """Diagnose local hardware, network cameras, and show S-expression descriptions."""
    console.print(Panel("[bold cyan]Universal Vision Doctor[/] - Running diagnosis..."))

    # 1. Local USB Scan
    table = Table(title="Local USB Cameras")
    table.add_column("Index", style="cyan")
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
            table.add_row(str(i), f"AVAILABLE ({int(w)}x{int(h)})", s_expr)
            cap.release()
        else:
            table.add_row(str(i), "NOT FOUND", "-")

    console.print(table)

    # 2. Network Discovery
    console.print("\n[bold cyan]Scanning Network for Cameras...[/] (mDNS / PortScan)")
    found = asyncio.run(discover_cameras())
    
    if found:
        net_table = Table(title="Network Cameras (Found)")
        net_table.add_column("IP", style="cyan")
        net_table.add_column("Source", style="green")
        net_table.add_column("Body Definition (S-expression)", style="yellow")
        
        for c in found:
            # Create a temporary NetworkCamera instance for S-expression preview
            cam = NetworkCamera(host=c['ip'], name="network_eye")
            s_expr = cam.get_body_description()
            net_table.add_row(c['ip'], c['source'], s_expr)
            
        console.print(net_table)
    else:
        console.print("  [yellow]No network cameras found on the local segment.[/]")

    # 3. Virtual/Mock (Fallback)
    console.print("\n[bold cyan]Mock/Virtual (Fallback) Definition:[/]")
    mock = MockCamera("mock_eye")
    console.print(Panel(mock.get_body_description(), border_style="dim"))

    console.print("\n[bold green]Diagnosis Complete.[/]")


@app.command()
def setup():
    """Interactive setup for your cameras."""
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
def run():
    """Start the MCP Server."""
    import asyncio
    from .server import main as server_main
    asyncio.run(server_main())


def main():
    app()


if __name__ == "__main__":
    main()
