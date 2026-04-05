"""Development server command."""

import click
import uvicorn


@click.command()
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload on file changes")
@click.option("--log-level", default="info", help="Log level (debug, info, warning, error)")
def serve(host: str, port: int, reload: bool, log_level: str):
    """Start the jClaw development server."""
    click.echo(click.style("🚀 Starting jClaw server...", bold=True))

    uvicorn.run(
        "jclaw.server.app:create_app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        factory=True,
    )
