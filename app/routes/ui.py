"""Serve the built web UI at ``/ui/``.

The bundle is built by the separate ``forgetful-ui`` project and shipped as
package data in ``app/web/ui``. ``UI_ENABLED`` is the master feature flag and
defaults to False: nothing is mounted unless it is set, so an installation that
has not opted in has no ``/ui`` route at all. Mounting happens in the HTTP
serving path only, so a STDIO run never serves the UI.

Navigation lives in the URL fragment, so the server never sees a screen path.
``/ui/`` serves the application shell, everything else under the prefix is a
static file, and no per-screen server rules exist or are needed.

Serving is delegated to ``starlette.staticfiles.StaticFiles`` rather than a
hand-written file handler. It performs its own path resolution and containment
checks, sets ``ETag``/``Last-Modified`` and range headers, and is the component
a reviewer can audit instead of reading bespoke traversal logic.

The bundle's asset URLs are relative (``./assets/index-<hash>.js``), so the same
files work at ``/ui/`` and under any reverse-proxy prefix that ends in ``/ui``.
That also means the shell must be served at a path ending in ``/ui/``; a mount
that redirects ``/ui`` to ``/ui/`` keeps the relative base correct.
"""

import logging
from pathlib import Path

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles

from app.config.settings import settings

logger = logging.getLogger(__name__)

#: URL prefix the bundle is mounted at. The trailing segment is load-bearing:
#: the UI derives its API prefix by stripping a trailing ``/ui`` from the path,
#: so serving it somewhere else changes which API it calls.
UI_PREFIX = "/ui"

#: Fallback bundle location: package data inside the installed package. In the
#: Nix package this resolves inside the store, so no built ``dist/`` is needed.
_PACKAGE_BUNDLE = Path(__file__).resolve().parent.parent / "web" / "ui"


def dist_dir() -> Path:
    """Directory holding the bundle: the override when set, else package data."""
    override = settings.UI_DIST_DIR.strip()
    if override:
        return Path(override).expanduser().resolve()
    return _PACKAGE_BUNDLE


def mount(app: Starlette) -> bool:
    """Mount the bundle on ``app``. Returns False when disabled or unavailable.

    A missing bundle is reported and not mounted, rather than mounting an empty
    directory that turns every request into a confusing 404.
    """
    if not settings.UI_ENABLED:
        return False

    directory = dist_dir()
    if not (directory / "index.html").is_file():
        logger.warning(
            "UI_ENABLED is set but no bundle was found; /ui is not served",
            extra={"ui_dist_dir": str(directory)},
        )
        return False

    # html=True serves index.html for the mount root and for directory requests.
    app.mount(UI_PREFIX, StaticFiles(directory=directory, html=True), name="ui")
    logger.info("Serving the web UI", extra={"ui_prefix": UI_PREFIX, "ui_dist_dir": str(directory)})
    return True
