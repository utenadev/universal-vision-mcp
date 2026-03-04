"""Network scanning and camera discovery for Universal Vision MCP."""

from __future__ import annotations

import asyncio
import logging
import socket
from typing import List, Dict, Any, Optional

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

logger = logging.getLogger(__name__)

# Common ONVIF/RTSP ports to scan
CAMERA_PORTS = [2020, 8000, 80, 8899, 554]


class CameraListener(ServiceListener):
    """ZeroConf listener to discover network cameras."""
    def __init__(self):
        self.found: List[Dict[str, Any]] = []

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            self.found.append({
                "name": name,
                "type": type_,
                "addresses": addresses,
                "port": info.port,
                "properties": {k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in info.properties.items()}
            })


async def check_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a specific port is open at the given IP."""
    try:
        conn = asyncio.open_connection(ip, port)
        await asyncio.wait_for(conn, timeout=timeout)
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


async def scan_network_mdns(timeout: float = 3.0) -> List[Dict[str, Any]]:
    """Scan for cameras using ZeroConf (mDNS)."""
    zeroconf = Zeroconf()
    listener = CameraListener()
    # Common camera service types
    services = ["_onvif._tcp.local.", "_axis-video._tcp.local.", "_rtsp._tcp.local."]
    
    browser = ServiceBrowser(zeroconf, services, listener)
    await asyncio.sleep(timeout)
    zeroconf.close()
    
    return listener.found


async def scan_ip_range(base_ip: str = "192.168.1", start: int = 1, end: int = 254) -> List[Dict[str, Any]]:
    """Quickly scan an IP range for common camera ports."""
    found = []
    
    async def probe(ip: str):
        for port in CAMERA_PORTS:
            if await check_port(ip, port):
                found.append({"ip": ip, "port": port})
                break

    # Parallel scan for speed
    tasks = [probe(f"{base_ip}.{i}") for i in range(start, end + 1)]
    await asyncio.gather(*tasks)
    return found


async def discover_cameras() -> List[Dict[str, Any]]:
    """Perform a comprehensive camera discovery."""
    logger.info("Starting camera discovery...")
    
    # Run mDNS and port scan in parallel
    mdns_task = scan_network_mdns()
    
    # For port scan, we need the local network prefix
    # Defaulting to 192.168.1 for now, but in a real app we'd detect the local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        prefix = ".".join(local_ip.split(".")[:-1])
        ip_task = scan_ip_range(prefix)
    except Exception:
        ip_task = asyncio.sleep(0, result=[])

    mdns_results, ip_results = await asyncio.gather(mdns_task, ip_task)
    
    # Merge and deduplicate
    all_found = []
    seen_ips = set()
    
    for res in mdns_results:
        for ip in res["addresses"]:
            if ip not in seen_ips:
                all_found.append({"ip": ip, "name": res["name"], "source": "mDNS", "port": res["port"]})
                seen_ips.add(ip)
                
    for res in ip_results:
        if res["ip"] not in seen_ips:
            all_found.append({"ip": res["ip"], "name": f"Camera at {res['ip']}", "source": "PortScan", "port": res["port"]})
            seen_ips.add(res["ip"])
            
    return all_found
