"""Static hosting for the built web UI.

Serving is opt-in and delegated to Starlette ``StaticFiles``. These tests use a
synthetic bundle so the chunk-resolution behaviour is deterministic, plus the
real built bundle when ``FORGETFUL_UI_DIST`` points at one.
"""

import os
import re
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette

from app.config.settings import settings
from app.routes import ui

# A bundle shaped like the real one: a shell with a relative module reference, and
# two further levels of relative dynamic import. Relative specifiers resolve
# against the importing module's URL, so a wrong prefix shows up at the second
# level, not the first.
ENTRY = 'import("./screen-bbb.js");'
SCREEN = 'import("./canvas-ccc.js");'
CANVAS = "export const canvasLoaded = true;"


@pytest.fixture
def bundle(tmp_path) -> Path:
    # Laid out as package data so the packaging test can use the same fixture.
    root = tmp_path / "app" / "web" / "ui"
    assets = root / "assets"
    assets.mkdir(parents=True)
    (root / "index.html").write_text(
        '<!doctype html><html><body><div id="root"></div>'
        '<script type="module" src="./assets/entry-aaa.js"></script></body></html>',
        encoding="utf-8",
    )
    (assets / "entry-aaa.js").write_text(ENTRY, encoding="utf-8")
    (assets / "screen-bbb.js").write_text(SCREEN, encoding="utf-8")
    (assets / "canvas-ccc.js").write_text(CANVAS, encoding="utf-8")
    brand = root / "brand"
    brand.mkdir()
    (brand / "favicon.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    return root


def _app() -> Starlette:
    return Starlette()


async def _client(app: Starlette) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=False,
    )


@pytest.fixture
def enabled(monkeypatch, bundle):
    monkeypatch.setattr(settings, "UI_ENABLED", True)
    monkeypatch.setattr(settings, "UI_DIST_DIR", str(bundle))
    return bundle


def test_flag_defaults_off_in_a_fresh_settings_instance():
    """UI_ENABLED is a feature flag like the other optional domains: false."""
    from app.config.settings import Settings

    fresh = Settings()
    assert fresh.UI_ENABLED is False
    assert fresh.UI_DIST_DIR == ""


async def test_disabled_registers_nothing(monkeypatch):
    """Default is off: no mount, and the prefix is not served at all."""
    monkeypatch.setattr(settings, "UI_ENABLED", False)
    app = _app()

    assert ui.mount(app) is False
    assert not any(getattr(route, "name", None) == "ui" for route in app.routes)

    async with await _client(app) as http:
        assert (await http.get("/ui/")).status_code == 404
        assert (await http.get("/ui/assets/entry-aaa.js")).status_code == 404


async def test_enabled_without_a_bundle_does_not_mount(monkeypatch, tmp_path):
    """Enabled with no bundle warns and mounts nothing, rather than serving 404s."""
    import logging

    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Capture(level=logging.WARNING)
    logger = logging.getLogger("app.routes.ui")
    # Alembic's logging config disables pre-existing loggers, so this test cannot
    # assume the logger is live depending on what ran before it.
    was_disabled, was_level = logger.disabled, logger.level
    logger.disabled = False
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    monkeypatch.setattr(settings, "UI_ENABLED", True)
    monkeypatch.setattr(settings, "UI_DIST_DIR", str(tmp_path / "absent"))
    try:
        app = _app()
        assert ui.mount(app) is False
    finally:
        logger.removeHandler(handler)
        logger.disabled, logger.level = was_disabled, was_level

    assert any("no bundle was found" in record.getMessage() for record in records)

    async with await _client(app) as http:
        assert (await http.get("/ui/")).status_code == 404


async def test_prefix_redirects_to_the_trailing_slash(enabled):
    """A relative shell base needs the document under a trailing slash."""
    app = _app()
    assert ui.mount(app) is True

    async with await _client(app) as http:
        response = await http.get("/ui")
        assert response.status_code == 307
        assert response.headers["location"].endswith("/ui/")


async def test_shell_and_assets_are_served(enabled):
    app = _app()
    ui.mount(app)

    async with await _client(app) as http:
        shell = await http.get("/ui/")
        assert shell.status_code == 200
        assert shell.headers["content-type"].startswith("text/html")
        assert "./assets/entry-aaa.js" in shell.text

        asset = await http.get("/ui/assets/entry-aaa.js")
        assert asset.status_code == 200
        assert asset.text == ENTRY

        brand = await http.get("/ui/brand/favicon.png")
        assert brand.status_code == 200
        assert brand.content.startswith(b"\x89PNG")


async def test_lazy_chunk_chain_resolves_over_http(enabled):
    """Walk shell -> entry -> screen -> canvas, resolving each relative import.

    Fetching only the first chunk would pass with a broken base. The second and
    third levels are the ones that expose it.
    """
    app = _app()
    ui.mount(app)

    async with await _client(app) as http:
        shell = await http.get("/ui/")
        assert shell.status_code == 200

        entry_path = re.search(r'src="\./(assets/entry-[^"]+\.js)"', shell.text)
        assert entry_path, "the shell must reference the entry chunk relatively"
        entry = await http.get(f"/ui/{entry_path.group(1)}")
        assert entry.status_code == 200

        screen_path = re.search(r'"\./(screen-[^"]+\.js)"', entry.text)
        assert screen_path, "the entry chunk must import its screen chunk relatively"
        screen = await http.get(f"/ui/assets/{screen_path.group(1)}")
        assert screen.status_code == 200

        canvas_path = re.search(r'"\./(canvas-[^"]+\.js)"', screen.text)
        assert canvas_path, "the screen chunk must import its canvas chunk relatively"
        canvas = await http.get(f"/ui/assets/{canvas_path.group(1)}")
        assert canvas.status_code == 200
        assert canvas.text == CANVAS


async def test_missing_and_traversing_paths_are_refused(enabled):
    app = _app()
    ui.mount(app)

    async with await _client(app) as http:
        assert (await http.get("/ui/assets/nope.js")).status_code == 404
        # StaticFiles resolves and contains paths itself; nothing escapes the bundle.
        traversal = await http.get("/ui/../config/settings.py")
        assert traversal.status_code in (404, 400)
        assert "SKILL_TAGS_MAX_COUNT" not in traversal.text


async def test_unknown_deep_paths_are_not_the_shell(enabled):
    """Routing lives in the fragment, so the server sees no screen paths.

    A deep path is therefore a plain 404, not a fallback to index.html. A client
    that needs the shell asks for /ui/ and puts the rest in the fragment.
    """
    app = _app()
    ui.mount(app)

    async with await _client(app) as http:
        # A screen path sent as a real path is a plain 404, not the shell.
        assert (await http.get("/ui/graph")).status_code == 404
        # The same screen addressed in the fragment is just the shell, because the
        # fragment never reaches the server.
        assert (await http.get("/ui/#/graph")).status_code == 200


REAL_BUNDLE = os.environ.get("FORGETFUL_UI_DIST", "")


@pytest.mark.skipif(
    not REAL_BUNDLE or not (Path(REAL_BUNDLE) / "index.html").is_file(),
    reason="set FORGETFUL_UI_DIST to a built forgetful-ui dist/ to walk the real chunks",
)
async def test_real_bundle_chain_resolves_over_http(monkeypatch):
    """The same walk against the real build: shell, entry, GraphScreen, GraphCanvas."""
    monkeypatch.setattr(settings, "UI_ENABLED", True)
    monkeypatch.setattr(settings, "UI_DIST_DIR", REAL_BUNDLE)
    app = _app()
    assert ui.mount(app) is True

    async with await _client(app) as http:
        shell = await http.get("/ui/")
        assert shell.status_code == 200
        entry = re.search(r'src="\./(assets/index-[^"]+\.js)"', shell.text).group(1)
        assert (await http.get(f"/ui/{entry}")).status_code == 200

        entry_body = (await http.get(f"/ui/{entry}")).text
        screen = re.search(r'"\./(GraphScreen-[^"]+\.js)"', entry_body).group(1)
        screen_response = await http.get(f"/ui/assets/{screen}")
        assert screen_response.status_code == 200

        canvas = re.search(r'"\./(GraphCanvas-[^"]+\.js)"', screen_response.text).group(1)
        canvas_response = await http.get(f"/ui/assets/{canvas}")
        assert canvas_response.status_code == 200
        assert len(canvas_response.content) > 100_000


class TestBundlePackaging:
    """A required build must fail rather than ship a wheel with no UI."""

    def test_required_build_fails_without_a_bundle(self, tmp_path, monkeypatch):
        import ui_bundle

        monkeypatch.setenv(ui_bundle.REQUIRE_ENV, "1")
        with pytest.raises(RuntimeError, match="no web UI bundle was found"):
            ui_bundle.check(tmp_path)

    def test_optional_build_tolerates_a_missing_bundle(self, tmp_path, monkeypatch):
        import ui_bundle

        monkeypatch.delenv(ui_bundle.REQUIRE_ENV, raising=False)
        assert ui_bundle.check(tmp_path) is False

    def test_present_bundle_satisfies_a_required_build(self, bundle, monkeypatch):
        import ui_bundle

        monkeypatch.setenv(ui_bundle.REQUIRE_ENV, "1")
        assert ui_bundle.check(bundle.parents[2]) is True

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", " yes "])
    def test_truthy_values_require_the_bundle(self, tmp_path, monkeypatch, value):
        import ui_bundle

        monkeypatch.setenv(ui_bundle.REQUIRE_ENV, value)
        assert ui_bundle.requirement_requested() is True

    @pytest.mark.parametrize("value", ["", "0", "no", "off"])
    def test_other_values_do_not(self, tmp_path, monkeypatch, value):
        import ui_bundle

        monkeypatch.setenv(ui_bundle.REQUIRE_ENV, value)
        assert ui_bundle.requirement_requested() is False


class TestTransportScope:
    """The UI is supported only when Forgetful runs as an HTTP server."""

    def test_stdio_never_mounts_even_when_enabled(self, monkeypatch):
        """STDIO is unchanged: no HTTP app, no mount, nothing to reach."""
        import main
        from app.routes import ui as ui_module

        mounted = []
        monkeypatch.setattr(settings, "UI_ENABLED", True)
        monkeypatch.setattr(ui_module, "mount", lambda app: mounted.append(app) or True)
        monkeypatch.setattr(main.mcp, "run", lambda *args, **kwargs: None)

        main._serve("stdio", "127.0.0.1", 8020)

        assert mounted == [], "a stdio run must never mount the UI"

    def test_http_mounts_when_enabled(self, monkeypatch):
        import uvicorn

        import main
        from app.routes import ui as ui_module

        mounted = []
        monkeypatch.setattr(settings, "UI_ENABLED", True)
        monkeypatch.setattr(settings, "CORS_ENABLED", False)
        monkeypatch.setattr(ui_module, "mount", lambda app: mounted.append(app) or True)
        monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: None)

        main._serve("http", "127.0.0.1", 8020)

        assert len(mounted) == 1, "an enabled HTTP run mounts exactly once"

    def test_http_does_not_mount_when_disabled(self, monkeypatch):
        import uvicorn

        import main
        from app.routes import ui as ui_module

        mounted = []
        recorded = {}
        monkeypatch.setattr(settings, "UI_ENABLED", False)
        monkeypatch.setattr(settings, "CORS_ENABLED", False)
        monkeypatch.setattr(ui_module, "mount", lambda app: mounted.append(app) or True)
        monkeypatch.setattr(main.mcp, "run", lambda *args, **kwargs: recorded.setdefault("run", kwargs))
        monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: recorded.setdefault("uvicorn", True))

        main._serve("http", "127.0.0.1", 8020)

        assert mounted == []
        assert "run" in recorded, "the default path still uses mcp.run"
        assert "uvicorn" not in recorded
