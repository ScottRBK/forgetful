"""Regression tests for upsert_env_var, the writer behind `forgetful auth login`.

The user config file (~/.config/forgetful/.env) also holds unrelated settings and
secrets, so the writer must read it as UTF-8 like settings does, leave every other
line untouched, update every duplicate assignment of the key, and never leave a
truncated file behind when a write fails.
"""
import errno
import io
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from dotenv import dotenv_values

from app.config.settings import Settings
from app.routes.cli import auth_commands

REPO_ROOT = Path(__file__).resolve().parents[2]

ORIGINAL = (
    "POSTGRES_PASSWORD=s3cret\n"
    "OPENAI_API_KEY=sk-abc\n"
    "FORGETFUL_SERVER=http://old:1/mcp\n"
)

# Characters str.splitlines() treats as line boundaries but dotenv does not.
UNICODE_SEPARATORS = {
    "U+2028": " ",
    "U+2029": " ",
    "U+0085": "\u0085",
    "VT": "\x0b",
    "FF": "\x0c",
    "FS": "\x1c",
    "GS": "\x1d",
    "RS": "\x1e",
}

# "Alvaro" with an accented capital A: UTF-8 bytes C3 81, and 0x81 is undefined in cp1252.
UTF8_CONTENT = "DEFAULT_USER_NAME=Álvaro\nLOG_LEVEL=DEBUG\n".encode()


def _leftover_temp_files(directory: Path, keep: str = ".env") -> list[str]:
    return sorted(p.name for p in directory.iterdir() if p.name != keep)


def _effective_server(dotenv_path: Path) -> str | None:
    # The real Settings class reading only this dotenv file, as the CLI does at startup.
    return Settings(_env_file=str(dotenv_path)).FORGETFUL_SERVER


class _PingOkClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def ping(self):
        return True


# =============================================================================
# Unrelated lines are preserved byte for byte
# =============================================================================


@pytest.mark.parametrize("name", sorted(UNICODE_SEPARATORS))
def test_unrelated_values_with_unicode_separators_are_preserved(tmp_path, name):
    sep = UNICODE_SEPARATORS[name]
    env_file = tmp_path / ".env"
    original = f'API_KEY="abc{sep}def"\nOTHER=1\n'
    env_file.write_bytes(original.encode())

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "https://example.test/mcp")

    after = env_file.read_bytes().decode()
    assert after == original + "FORGETFUL_SERVER=https://example.test/mcp\n"
    values = dotenv_values(env_file)
    assert values["API_KEY"] == f"abc{sep}def"
    assert values["FORGETFUL_SERVER"] == "https://example.test/mcp"


def test_crlf_line_endings_of_unrelated_and_replaced_lines_are_kept(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"A=1\r\nFORGETFUL_SERVER=http://old/mcp\r\nB=2\r\n")

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new/mcp")

    assert env_file.read_bytes() == b"A=1\r\nFORGETFUL_SERVER=http://new/mcp\r\nB=2\r\n"


def test_appended_line_follows_the_crlf_endings_of_the_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"A=1\r\nB=2\r\n")

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new/mcp")

    assert env_file.read_bytes() == b"A=1\r\nB=2\r\nFORGETFUL_SERVER=http://new/mcp\r\n"


def test_file_without_trailing_newline_gets_one(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"A=1")

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new/mcp")

    assert env_file.read_bytes() == b"A=1\nFORGETFUL_SERVER=http://new/mcp\n"


# =============================================================================
# Every duplicate assignment of the key is updated
# =============================================================================

DUPLICATED = (
    "FORGETFUL_SERVER=http://old/mcp\n"
    "FOO=1\n"
    "FORGETFUL_SERVER=http://older/mcp\n"
)


def test_upsert_updates_every_duplicate_so_the_new_value_is_effective(tmp_path, monkeypatch):
    monkeypatch.delenv("FORGETFUL_SERVER", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(DUPLICATED)
    assert _effective_server(env_file) == "http://older/mcp"  # the last duplicate wins

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:8020/mcp")

    assert env_file.read_text() == (
        "FORGETFUL_SERVER=http://new:8020/mcp\n"
        "FOO=1\n"
        "FORGETFUL_SERVER=http://new:8020/mcp\n"
    )
    assert _effective_server(env_file) == "http://new:8020/mcp"


async def test_login_with_duplicate_server_lines_makes_the_new_server_effective(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("FORGETFUL_SERVER", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(DUPLICATED)

    code = await auth_commands.login(
        "http://new:8020",
        env_file=env_file,
        token_dir=tmp_path / "tokens",
        client_factory=lambda url, token_dir: _PingOkClient(),
    )

    assert code == 0
    assert "Logged in to" in capsys.readouterr().out
    assert _effective_server(env_file) == "http://new:8020/mcp"


# =============================================================================
# The file is read and written as UTF-8 whatever the locale is
# =============================================================================


def test_utf8_dotenv_survives_upsert_under_simulated_cp1252_locale(tmp_path, monkeypatch):
    """Windows before Python 3.15 opens text files with cp1252 unless told otherwise."""
    real_open = io.open

    def windows_open(file, mode="r", buffering=-1, encoding=None, *args, **kwargs):
        if "b" not in mode and encoding in (None, "locale"):
            encoding = "cp1252"
        return real_open(file, mode, buffering, encoding, *args, **kwargs)

    monkeypatch.setattr(io, "open", windows_open)
    env_file = tmp_path / ".env"
    env_file.write_bytes(UTF8_CONTENT)

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "https://x/mcp")

    assert env_file.read_bytes() == UTF8_CONTENT + b"FORGETFUL_SERVER=https://x/mcp\n"


def _run_in_legacy_locale(code: str, *args: Path, cwd: Path) -> subprocess.CompletedProcess:
    """Run code in a child whose default text encoding is ASCII (C locale, no UTF-8 mode)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("LC_", "LANG", "PYTHON"))}
    env.update(LC_ALL="C", PYTHONUTF8="0", PYTHONCOERCECLOCALE="0")
    return subprocess.run(  # noqa: S603 - test-controlled arguments, no shell
        [sys.executable, "-c", code, str(REPO_ROOT), *map(str, args)],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
    )


def test_utf8_dotenv_and_utf8_server_survive_upsert_under_a_real_ascii_locale(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(UTF8_CONTENT)
    code = textwrap.dedent(
        """
        import sys
        from pathlib import Path

        sys.path.insert(0, sys.argv[1])
        from app.routes.cli.auth_commands import upsert_env_var

        upsert_env_var(Path(sys.argv[2]), "FORGETFUL_SERVER", "https://b\\u00fccher.example/mcp")
        """,
    )

    proc = _run_in_legacy_locale(code, env_file, cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr
    assert env_file.read_bytes() == (
        UTF8_CONTENT + "FORGETFUL_SERVER=https://bücher.example/mcp\n".encode()
    )


# =============================================================================
# A failed write never destroys the existing file
# =============================================================================


def test_unencodable_value_leaves_the_original_file_untouched(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL, encoding="utf-8")

    with pytest.raises(UnicodeEncodeError):
        # A lone surrogate (e.g. from an undecodable argv byte) cannot be encoded.
        auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://bad\udcff.example/mcp")

    assert env_file.read_text(encoding="utf-8") == ORIGINAL
    assert _leftover_temp_files(tmp_path) == []


def test_unencodable_value_does_not_create_a_missing_file(tmp_path):
    env_file = tmp_path / "config" / ".env"

    with pytest.raises(UnicodeEncodeError):
        auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://bad\udcff.example/mcp")

    assert not env_file.exists()


def test_disk_full_while_writing_leaves_original_and_no_temp_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL, encoding="utf-8")

    def disk_full(fd):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "fsync", disk_full)

    with pytest.raises(OSError, match="No space left"):
        auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert env_file.read_text(encoding="utf-8") == ORIGINAL
    assert _leftover_temp_files(tmp_path) == []


def test_failure_replacing_the_file_leaves_original_and_no_temp_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL, encoding="utf-8")

    def replace_denied(src, dst):
        raise PermissionError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(os, "replace", replace_denied)

    with pytest.raises(PermissionError):
        auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert env_file.read_text(encoding="utf-8") == ORIGINAL
    assert _leftover_temp_files(tmp_path) == []


def test_successful_write_leaves_no_temp_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL, encoding="utf-8")

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert _leftover_temp_files(tmp_path) == []


# =============================================================================
# File permissions and symlinks (POSIX)
# =============================================================================

posix_only = pytest.mark.skipif(os.name != "posix", reason="POSIX file modes and symlinks")


@posix_only
def test_new_file_is_private_to_the_user(tmp_path):
    env_file = tmp_path / "config" / ".env"

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600


@posix_only
@pytest.mark.parametrize("mode", [0o600, 0o640, 0o644])
def test_existing_file_keeps_its_permissions(tmp_path, mode):
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL, encoding="utf-8")
    env_file.chmod(mode)

    auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert stat.S_IMODE(env_file.stat().st_mode) == mode


@posix_only
@pytest.mark.skipif(os.name == "posix" and os.geteuid() == 0, reason="root ignores file modes")
def test_read_only_env_file_is_not_silently_replaced(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(ORIGINAL, encoding="utf-8")
    env_file.chmod(0o400)

    with pytest.raises(PermissionError):
        auth_commands.upsert_env_var(env_file, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert env_file.read_text(encoding="utf-8") == ORIGINAL
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o400
    assert _leftover_temp_files(tmp_path) == []


@posix_only
def test_symlinked_env_file_stays_a_symlink_and_updates_its_target(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()
    target = dotfiles / "forgetful.env"
    target.write_text(ORIGINAL, encoding="utf-8")
    config = tmp_path / "config"
    config.mkdir()
    link = config / ".env"
    link.symlink_to(target)

    auth_commands.upsert_env_var(link, "FORGETFUL_SERVER", "http://new:2/mcp")

    assert link.is_symlink()
    assert target.read_text(encoding="utf-8") == (
        "POSTGRES_PASSWORD=s3cret\nOPENAI_API_KEY=sk-abc\nFORGETFUL_SERVER=http://new:2/mcp\n"
    )
    assert sorted(p.name for p in dotfiles.iterdir()) == ["forgetful.env"]
