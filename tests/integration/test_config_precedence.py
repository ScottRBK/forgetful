"""Integration tests for configuration precedence in settings.py.

docs/configuration.md ("CLI Configuration" > "Configuration precedence") documents,
highest wins:

    1. Per-invocation flags (--server / --local)
    2. Shell environment (a real FORGETFUL_SERVER env var)
    3. User config file (~/.config/forgetful/.env, written by `forgetful auth login`)
    4. Defaults

A stray `.env` in whatever directory the CLI happens to run from is NOT on that list,
so it must never outrank the user config the user saved with `auth login`.

settings.py resolves this at import time, so each case runs in a throwaway subprocess:
a fresh interpreter imports app.config.settings under a controlled CWD, user-config
home, and shell env, then prints the resolved FORGETFUL_SERVER. The subprocess keeps
the import-time load_dotenv() side effects out of the shared test session.
"""
import os
import subprocess
import sys
import textwrap
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_forgetful_server(tmp_path, *, cwd_env, user_config_env, shell_env=None):
    """Import settings.py in a fresh interpreter and return the resolved
    FORGETFUL_SERVER for the given CWD .env / user-config .env / shell env."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    cwd_env_file = checkout / ".env"
    if cwd_env is not None:
        cwd_env_file.write_text(f"FORGETFUL_SERVER={cwd_env}\n")

    config_home = tmp_path / "config"
    (config_home / "forgetful").mkdir(parents=True)
    if user_config_env is not None:
        (config_home / "forgetful" / ".env").write_text(
            f"FORGETFUL_SERVER={user_config_env}\n",
        )

    env = dict(os.environ)
    env["PYTHONPATH"] = str(_PROJECT_ROOT)
    env["HOME"] = str(tmp_path / "home")
    env["XDG_CONFIG_HOME"] = str(config_home)
    env.pop("FORGETFUL_SERVER", None)
    if shell_env is not None:
        env["FORGETFUL_SERVER"] = shell_env

    # load_dotenv() discovers a .env by walking up from the settings.py file, not the
    # CWD; pin discovery to the run directory so the promotion bug (if present)
    # reproduces deterministically rather than depending on the runner's layout.
    discovered = str(cwd_env_file) if cwd_env is not None else ""
    code = textwrap.dedent(
        f"""
        import dotenv.main
        dotenv.main.find_dotenv = lambda *a, **k: {discovered!r}
        from app.config.settings import settings
        print(settings.FORGETFUL_SERVER)
        """,
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=checkout,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_cwd_env_does_not_override_user_config(tmp_path):
    # Arrange: a stray .env in the run directory and the user config disagree; no real
    # shell env var is set.
    # Act
    resolved = _resolve_forgetful_server(
        tmp_path,
        cwd_env="http://cwd-checkout:9/mcp",
        user_config_env="http://user-config:8/mcp",
    )

    # Assert: the user config (the file `auth login` writes) wins, per the docs.
    assert resolved == "http://user-config:8/mcp"


def test_shell_env_overrides_user_config(tmp_path):
    # Arrange: a real shell FORGETFUL_SERVER outranks the user config file.
    # Act
    resolved = _resolve_forgetful_server(
        tmp_path,
        cwd_env=None,
        user_config_env="http://user-config:8/mcp",
        shell_env="http://shell:7/mcp",
    )

    # Assert
    assert resolved == "http://shell:7/mcp"
