"""Whether a wheel or sdist should include the built web UI bundle.

Kept free of build-backend imports so it can be tested without hatchling, which
is a build-time dependency only. ``hatch_build.py`` is the thin adapter.

The bundle is a build output, not repository content: it exists only after a
build has produced it. Including it when present keeps development and Nix
installs working without pretending the files are source. Requiring it when the
release environment asks is what stops a wheel shipping with no UI and failing
only when a user sets ``UI_ENABLED=true``.
"""

import os
from pathlib import Path

#: Where the bundle lands inside the package, relative to the project root.
BUNDLE = "app/web/ui"

#: Set to a truthy value by release and container builds.
REQUIRE_ENV = "FORGETFUL_REQUIRE_UI_BUNDLE"

_TRUTHY = {"1", "true", "yes"}


def requirement_requested() -> bool:
    """Whether this build must ship the UI."""
    return os.environ.get(REQUIRE_ENV, "").strip().lower() in _TRUTHY


def bundle_present(root: Path | str) -> bool:
    """Whether a bundle with an entry point exists under ``root``."""
    return (Path(root) / BUNDLE / "index.html").is_file()


def check(root: Path | str) -> bool:
    """Return whether the bundle should be included, raising if it is required.

    Raises:
        RuntimeError: The build requires the UI and no bundle was found.
    """
    present = bundle_present(root)
    if requirement_requested() and not present:
        raise RuntimeError(
            f"{REQUIRE_ENV} is set but no web UI bundle was found at "
            f"{BUNDLE}/index.html. Build the UI first (see docs/ui.md) or unset "
            f"{REQUIRE_ENV} for a build that does not ship the UI.",
        )
    return present
