"""Argparse tree and dispatch for the Forgetful CLI subcommands.

main.cli() routes argv here only when argv[0] is a KNOWN subcommand; anything else
falls back to the legacy launcher so every documented pre-CLI invocation keeps working
(see docs/dev/cli_plan.md section 4.2).
"""
import argparse
import asyncio

from app.version import get_version

# Tokens that route to the subcommand tree. Bare invocations and legacy flags
# (--transport, --re-embed, --version) never appear here, so they fall through
# to the legacy launcher permanently.
KNOWN = {"serve", "re-embed", "tools", "call", "auth", "memory", "project"}


def build_parser() -> argparse.ArgumentParser:
    from app.config.settings import settings

    parser = argparse.ArgumentParser(
        prog="forgetful",
        description="Forgetful - MCP server and memory CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the Forgetful MCP server")
    serve.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport method (default: stdio for MCP clients)",
    )
    serve.add_argument(
        "--host",
        default=settings.SERVER_HOST,
        help=f"HTTP host (default: {settings.SERVER_HOST})",
    )
    serve.add_argument(
        "--port",
        type=int,
        default=settings.SERVER_PORT,
        help=f"HTTP port (default: {settings.SERVER_PORT})",
    )

    reembed = subparsers.add_parser(
        "re-embed",
        help="Re-embed all memories with the currently configured provider",
    )
    reembed.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Batch size for re-embedding (default: 20)",
    )
    reembed.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    return parser


def dispatch(argv, *, serve_runner, reembed_runner):
    """Parse a KNOWN-subcommand argv and route it to the injected runners."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        return serve_runner(transport=args.transport, host=args.host, port=args.port)
    if args.command == "re-embed":
        return asyncio.run(reembed_runner(args))

    parser.error(f"Subcommand '{args.command}' is not implemented yet")
