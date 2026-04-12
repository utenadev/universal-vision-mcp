"""HTTP Server module for Universal Vision MCP.

Provides SSE and Streamable HTTP transport support alongside stdio.
"""

import contextlib
import logging
from collections.abc import AsyncIterator

import uvicorn
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from .server import server, sync_cameras

logger = logging.getLogger(__name__)


def create_starlette_app(*, debug: bool = False) -> Starlette:
    """Create a Starlette application with SSE and Streamable HTTP support.

    Endpoints:
        - /sse: SSE transport endpoint
        - /mcp: Streamable HTTP transport endpoint
        - /messages/: POST message handling for SSE

    Args:
        debug: Enable debug mode for Starlette

    Returns:
        Configured Starlette application
    """
    # SSE transport for clients that prefer SSE
    sse = SseServerTransport("/messages/")

    # Streamable HTTP session manager (stateless, JSON response)
    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=None,
        json_response=True,
        stateless=True,
    )

    async def handle_sse(request: Request) -> None:
        """Handle SSE connection requests."""
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle Streamable HTTP requests."""
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Manage session manager lifecycle and camera initialization."""
        # Initialize cameras on startup
        await sync_cameras()
        logger.info("Cameras synchronized")

        async with session_manager.run():
            logger.info("StreamableHTTP session manager started")
            try:
                yield
            finally:
                logger.info("StreamableHTTP session manager shutting down")

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/mcp", app=handle_streamable_http),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )


def run_http_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the HTTP server with SSE and Streamable HTTP support.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 8000)
    """
    if host == "0.0.0.0":
        logger.warning(
            "Server bound to 0.0.0.0 (LAN mode). "
            "This allows connections from other machines. "
            "Use only in trusted networks. No authentication provided."
        )

    app = create_starlette_app(debug=True)
    logger.info(f"Starting HTTP server on {host}:{port}")
    logger.info("Endpoints:")
    logger.info("  - SSE:            http://{host}:{port}/sse")
    logger.info("  - Streamable HTTP: http://{host}:{port}/mcp")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_http_server()
