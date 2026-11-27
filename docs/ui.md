# Web UI hosting

Forgetful can serve the built [forgetful-ui](https://github.com/ScottRBK/forgetful-ui) bundle
itself. The bundle is static files: no Node, no separate service, and no second deployment to keep
in step with the server.

The UI is an optional component and `UI_ENABLED` is its master feature flag, in the same shape as
the files, skills and planning flags. It is **off by default**: an installation that has not opted in
has no `/ui` route at all.

It is also an **HTTP-only** component. The UI is served by Starlette, so it exists only in the HTTP
transport; a `--transport stdio` run never mounts it, and `/.well-known` reports
`"ui": false` unless the flag is set. STDIO behaviour is unchanged.

## Enabling it

| Setting | Default | Meaning |
| --- | --- | --- |
| `UI_ENABLED` | `false` | Master feature flag for the web UI; mounts the bundle at `/ui/` |
| `UI_DIST_DIR` | empty | Bundle location; only relevant when `UI_ENABLED=true`. Empty means the copy shipped as package data at `app/web/ui` |

```bash
UI_ENABLED=true forgetful-ai --transport http --port 8020
```

If `UI_ENABLED` is set and no bundle is found, the server logs a warning and does not mount
anything. It does not serve an empty directory, because an empty mount turns every request into a
misleading 404.

For development against a local build of the UI:

```bash
cd ../forgetful-ui && npm ci && npm run build
UI_ENABLED=true UI_DIST_DIR="$PWD/dist" forgetful-ai --transport http --port 8020
```

## Where the bundle comes from

Three build paths, one pinned source. The UI commit is recorded in `flake.lock` as the
`forgetful-ui` input, and every path builds that same commit:

| Path | How the bundle is produced |
| --- | --- |
| `pip install` / wheel | Release CI builds the bundle before building the wheel, then ships it as package data. |
| Container image | A Node build stage in `docker/Dockerfile` builds it and copies it into the image. |
| Nix | `packages.ui-bundle` builds it from the pinned input; the package installs it into `app/web/ui` inside the store. |

The wheel includes the bundle only when the files are present, so a source checkout still builds.
Release and container builds set `FORGETFUL_REQUIRE_UI_BUNDLE=1`, which makes a missing bundle fail
the build instead of producing a wheel that serves nothing.

The bundle is not committed. `app/web/ui/` is a build output.

## The `/ui/` prefix contract

The server mounts the bundle at `/ui/` with Starlette's `StaticFiles`, `html=True`. There are no
per-screen server rules, and none are needed.

**Routing lives in the URL fragment.** The UI uses hash routing, so a screen address looks like
`/ui/#/graph`. The fragment is never sent to the server: every navigation is a request for
`/ui/`, which returns the shell. That is why the server never needs to know the screen list, and why
a real path such as `/ui/graph` is a plain 404 rather than the shell.

**The trailing slash matters.** The shell references its assets relatively
(`./assets/index-<hash>.js`), so it must be served at a path ending in `/ui/`. `StaticFiles` mounted
at `/ui` redirects `/ui` to `/ui/`; do not suppress that redirect.

**Assets are content-hashed** and sit under `/ui/assets/`. Lazy screen chunks import each other with
relative specifiers, so each chunk resolves against its own URL. This is what makes a nested chain
work: the shell loads `/ui/assets/index-<hash>.js`, which loads
`/ui/assets/GraphScreen-<hash>.js`, which loads `/ui/assets/GraphCanvas-<hash>.js`.

**The API prefix is derived from the UI path.** The UI strips a trailing `/ui` (or `/ui/index.html`)
from the current pathname to find its deployment prefix, then calls `<prefix>/api/v1` and
`<prefix>/.well-known`. Served at `/ui/`, that is `/api/v1`. Served behind `https://host/foo/ui/`, it
is `/foo/api/v1`.

### About the two prefixes

The UI is at `/ui/`; the API is at `/api/`. They are siblings, not nested. Under a reverse-proxy
prefix `P`, they are `P/ui/` and `P/api/`, and the UI derives `P` for itself.

## What a reverse proxy must forward

| Path | Purpose |
| --- | --- |
| `/ui/` and everything under it | The bundle: shell, hashed assets, brand images |
| `/api/` | The REST API and MCP-over-HTTP |
| `/health` | Liveness and readiness |
| `/.well-known` | Capability discovery used by the UI |

Notes that matter in practice:

- **Forward the path unchanged.** Do not strip `/ui` when proxying: the UI derives its API prefix
  from the path it is served at, so stripping it makes the app call `/api/v1` at the origin root
  while the browser is at `/ui/`.
- **Forward the fragment?** No. Browsers never send it, and nothing server-side reads it.
- **No rewrite rules are needed for screens.** `#/graph`, `#/memories/123` and every other screen
  are the same document request. A catch-all-to-`index.html` rule for `/ui/*` is unnecessary and
  would turn genuine bundle misses into silently wrong pages.
- **Do not merge a second prefix into `/ui`.** Mounting the app at `P/ui` while telling it it lives
  at `/ui` splits its asset and API base, which produces a page that loads and then fails on the
  second chunk fetch.

## What breaks if the prefix is rewritten

| Rewrite | Result |
| --- | --- |
| `/ui/*` → `/` | The shell loads, but relative asset URLs resolve to `/assets/...` and 404 immediately, and the API prefix becomes empty |
| `/ui/` → `/ui` (drops the slash) | Relative asset URLs resolve one directory up; the first chunk 404s |
| Strip `/ui` but serve the bundle under it | Assets 200, then the app calls `/api/v1` at the proxy root and every request misses |
| Add `/index.html` to asset paths | Harmless for the shell, wrong for hashed assets; hashed filenames are exact |

The failure is not always immediate. A wrong base can let the shell and the entry chunk load and
then 404 on the second-level import, so a smoke test that only checks `/ui/` is not enough.

## Verifying a deployment

Fetch the shell, then walk the chunk chain it names:

```bash
curl -s https://host/ui/ | grep -o 'src="\./assets/[^"]*"'
curl -sI https://host/ui/assets/index-<hash>.js
curl -sI https://host/ui/assets/GraphScreen-<hash>.js     # nested screen chunk
curl -sI https://host/ui/assets/GraphCanvas-<hash>.js     # deeper chunk
```

All four must return `200`. The test suite performs exactly this walk; see
`tests/integration/test_ui_static.py`, including the variant that walks a real built bundle when
`FORGETFUL_UI_DIST` points at one.

## Nix

`nix build .#ui-bundle` produces the bundle on its own, and `nix build .#forgetful-ai` installs it
into the package at `lib/app/web/ui`. No `dist/` and no `UI_DIST_DIR` are needed:

```bash
UI_ENABLED=true nix run .#forgetful-ai -- --transport http --port 8020
```

See [nix.md](nix.md) for the derivation and why the UI is a flake input rather than a submodule.
