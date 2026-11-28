"""Hatch build hook: include the built web UI bundle, or fail when it is required.

The decision logic lives in ``ui_bundle.py`` so it can be tested without hatchling.
Set ``FORGETFUL_REQUIRE_UI_BUNDLE=1`` (release and container builds do) and a
wheel built with no ``app/web/ui/index.html`` fails here, at build time, instead
of producing an artifact that only reveals the problem when a user enables the UI.
"""

import importlib.util
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def _load_ui_bundle():
    """Load the sibling module by path: the project root is not on sys.path here."""
    path = Path(__file__).with_name("ui_bundle.py")
    spec = importlib.util.spec_from_file_location("ui_bundle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ui_bundle = _load_ui_bundle()


class UIBundleBuildHook(BuildHookInterface):
    """Include the web UI bundle in the wheel and sdist when it exists."""

    PLUGIN_NAME = "ui-bundle"

    def initialize(self, version, build_data):
        if not ui_bundle.check(Path(self.root)):
            return

        build_data.setdefault("artifacts", []).append(ui_bundle.BUNDLE)

        if self.target_name == "sdist":
            include = build_data.setdefault("include", [])
            if ui_bundle.BUNDLE not in include:
                include.append(ui_bundle.BUNDLE)
