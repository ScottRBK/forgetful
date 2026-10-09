# Nix Guide

Run and develop Forgetful with [Nix flakes](https://nixos.wiki/wiki/Flakes).
`uv.lock` stays the single source of truth for exact dependency versions —
Nix builds the locked environment reproducibly. The Docker setup under
`docker/` is untouched; this is an alternative, not a replacement.

## Prerequisites

- Nix with flakes enabled (`experimental-features = nix-command flakes` in
  `~/.config/nix/nix.conf`, or NixOS / nix-installer which set it up for you)
- Supported systems: `x86_64-linux`, `aarch64-linux`, `aarch64-darwin`
  (`x86_64-darwin` is intentionally omitted)

## Dev shell

```bash
nix develop
```

You get the locked Python environment plus `uv`, `ruff` and `pytest`, with
`PYTHONPATH` pointed at the repo. First entry installs the pre-commit hooks
automatically.

Use `uv` for lock operations only (`uv add …`, `uv lock`) — never
`uv sync`/`uv run` inside the shell; Nix owns the environment.

```bash
uv lock --check
pytest tests/integration/ -q
```

## Run

```bash
nix run .#forgetful-ai -- --transport http --port 8020
```

(`nix run .` works too — `forgetful-ai` is the default app.) Anything after
`--` is passed to Forgetful; see `forgetful --help` for transports and flags.
For MCP clients, point a stdio server at `nix run .#forgetful-ai`.

## Build

```bash
nix build .#forgetful-ai -o result-forgetful   # wrapped app package
nix build .#docker -o forgetful.tar.gz         # OCI image (~195M)
```

The image repo is `forgetful` — same as `ghcr.io/<owner>/forgetful` in
`.github/workflows/build.yml` and the `forgetful:latest` default in
`docker/docker-compose.yml` (package name stays `forgetful-ai`). The tag is the
sanitized version (`+` → `-`, since `+` is invalid in Docker tags): local builds
give `forgetful:0.0.0-dev`; release builds inject the real tag:

```bash
FORGETFUL_VERSION=$(git describe --tags) nix build --impure .#docker
```

Load and add the CI-equivalent aliases (`buildLayeredImage` carries one tag, so
`latest` / `major.minor` are plain `docker tag`s after load):

```bash
docker image load -i forgetful.tar.gz
docker tag forgetful:<version> forgetful:latest
# optional GHCR aliases:
# docker tag forgetful:<version> ghcr.io/<owner>/forgetful:<version>
# docker tag forgetful:<version> ghcr.io/<owner>/forgetful:latest
docker run --rm -p 8020:8020 forgetful:latest
curl -sf http://localhost:8020/health
```

## Versions

Hatch-vcs has no `.git` inside Nix builds, so the version defaults to
`0.0.0+dev` (same spirit as the Dockerfile's `VERSION` default). For a real
tag, inject it release-side:

```bash
FORGETFUL_VERSION=$(git describe --tags) nix build --impure .#forgetful-ai
```

## Hooks, format, checks

- Hooks (`nixfmt`, `deadnix`, `statix`, `ruff`, `typos`) run at commit time
  from the dev shell: `pre-commit run --all-files`
- `nix fmt` rewrites the tree with the same hook set
- `nix flake check` runs the sandboxed pre-commit check (fast, hermetic)

Spelling allowlist lives in `_typos.toml` (e.g. the intentional `"FoRgEtFuL"`
in tests, personal notes in `org_knowledge_proposal.md` which is excluded).

## Tests

The integration suite needs network (embedding/model downloads), so it runs in
the dev shell rather than the sandboxed flake check:

```bash
nix develop -c pytest tests/integration/ -q
```

## Troubleshooting

- `warning: Git tree … is dirty` — benign; Nix tells you the evaluation used
  your worktree state. Commit for byte-identical reproducibility.
- `pre-commit: command not found` in an old shell — re-enter `nix develop`
  (the shell installs hooks and PATH on entry).
- `aarch64` packages evaluate but won't *build* here — that needs an aarch64
  builder or CI (`nix build --dry-run` proves the closure resolves).
- First `nix develop`/`nix build` downloads a lot (toolchain + all locked
  wheels) — subsequent runs are cached.
