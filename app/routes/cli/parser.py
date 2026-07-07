"""Argparse tree and dispatch for the Forgetful CLI subcommands.

main.cli() routes argv here only when argv[0] is a KNOWN subcommand; anything else
falls back to the legacy launcher so every documented pre-CLI invocation keeps working
(see docs/dev/cli_plan.md section 4.2).
"""
import argparse
import asyncio
import json

from app.version import get_version

# Tokens that route to the subcommand tree. Bare invocations and legacy flags
# (--transport, --re-embed, --version) never appear here, so they fall through
# to the legacy launcher permanently.
KNOWN = {"serve", "re-embed", "tools", "call", "auth", "memory", "project"}


def _json_object(value: str) -> dict:
    """argparse type for --args: must parse as a JSON object."""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"must be valid JSON ({exc})")
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("must be a JSON object of tool arguments")
    return parsed


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

    # Flags shared by every tool command
    output_flags = argparse.ArgumentParser(add_help=False)
    output_flags.add_argument(
        "--json",
        action="store_true",
        help='Emit machine-readable JSON (errors become {"error": ...} on stderr)',
    )
    output_flags.add_argument(
        "--server",
        metavar="URL",
        help="Execute against a remote Forgetful deployment (beats FORGETFUL_SERVER)",
    )
    output_flags.add_argument(
        "--local",
        action="store_true",
        help="Force local mode even when FORGETFUL_SERVER is configured",
    )

    tools = subparsers.add_parser("tools", help="Inspect the available Forgetful tools")
    tools_sub = tools.add_subparsers(dest="tools_command", required=True)
    tools_list = tools_sub.add_parser(
        "list",
        parents=[output_flags],
        help="List available tools grouped by category",
    )
    tools_list.add_argument(
        "--category",
        help="Filter by tool category (e.g. memory, project, entity)",
    )
    tools_info = tools_sub.add_parser(
        "info",
        parents=[output_flags],
        help="Show detailed documentation and schema for a tool",
    )
    tools_info.add_argument("tool", help="Tool name")

    call = subparsers.add_parser(
        "call",
        parents=[output_flags],
        help="Execute any Forgetful tool by name",
    )
    call.add_argument("tool", help="Tool name")
    call.add_argument(
        "--args",
        type=_json_object,
        default={},
        help="Tool arguments as a JSON object",
    )

    auth = subparsers.add_parser("auth", help="Authenticate against a remote deployment")
    auth_sub = auth.add_subparsers(dest="auth_command", required=True)
    auth_login = auth_sub.add_parser(
        "login",
        help="Browser OAuth login; saves FORGETFUL_SERVER to the user config",
    )
    auth_login.add_argument("--server", metavar="URL", required=True, help="Server URL")
    auth_sub.add_parser("status", help="Show the active server and authenticated user")
    auth_sub.add_parser("logout", help="Clear the local OAuth token cache")

    return parser


async def _build_executor(args):
    """Construct the ToolExecutor: --local > --server > FORGETFUL_SERVER > local default.

    FORGETFUL_SERVER merges shell env and ~/.config/forgetful/.env with the right
    precedence via pydantic-settings; FORGETFUL_TOKEN (headless/CI bearer) is shell
    env only, deliberately kept out of config files.
    """
    import os

    from app.config.settings import settings

    if not getattr(args, "local", False):
        server_url = getattr(args, "server", None) or settings.FORGETFUL_SERVER
        if server_url:
            from app.routes.cli.remote_executor import RemoteExecutor

            return RemoteExecutor(server_url, token=os.environ.get("FORGETFUL_TOKEN") or None)

    from app.routes.cli.local_executor import LocalExecutor

    return await LocalExecutor.create()


async def _run_tool_command(args) -> int:
    """Execute a tools/call command and map failures onto exit code 1."""
    from app.routes.cli.render import emit_error, render_result

    as_json = getattr(args, "json", False)
    try:
        executor = await _build_executor(args)
    except Exception as exc:
        emit_error(str(exc), as_json)
        return 1

    try:
        if args.command == "tools" and args.tools_command == "list":
            result = await executor.list_tools(category=args.category)
        elif args.command == "tools":
            result = await executor.tool_info(args.tool)
        else:
            result = await executor.execute(args.tool, args.args)
        print(render_result(result, as_json))
        return 0
    except Exception as exc:
        emit_error(str(exc), as_json)
        return 1
    finally:
        await executor.close()


def dispatch(argv, *, serve_runner, reembed_runner):
    """Parse a KNOWN-subcommand argv and route it to the injected runners."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        return serve_runner(transport=args.transport, host=args.host, port=args.port)
    if args.command == "re-embed":
        return asyncio.run(reembed_runner(args))
    if args.command in {"tools", "call"}:
        return asyncio.run(_run_tool_command(args))
    if args.command == "auth":
        return asyncio.run(_run_auth_command(args))

    parser.error(f"Subcommand '{args.command}' is not implemented yet")


async def _run_auth_command(args) -> int:
    from app.routes.cli import auth_commands

    if args.auth_command == "login":
        return await auth_commands.login(args.server)
    if args.auth_command == "status":
        return await auth_commands.status()
    return auth_commands.logout()
