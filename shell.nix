# nix-shell entry point (flake-compat). Delegates to the flake's own
# devShells.<system>.default so there is exactly one dev shell definition;
# a second one here would silently drift from `nix develop`.
(import ./default.nix).devShells.${builtins.currentSystem}.default
