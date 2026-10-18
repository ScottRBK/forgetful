# UAT Walkthrough Harness

Pre-release user-acceptance testing for Forgetful's agent-facing contract. A real agent
(driven headlessly via [agent-shell](https://pypi.org/project/agent-shell-py/)) works
through each canonical skill in `skills/` against a throwaway local Forgetful — does the
doc make sense, do the commands behave as documented — and reports issues. The harness
captures the agent's report *and* the full event transcript; acceptance is decided by a
supervising review of both, never by the agent's self-report alone.

The agent runs **inside a sandbox container** (pattern ported from eval-harness's
DockerRunner): it can only see the mounted skill artifacts and staged credential
copies, so the host filesystem — and the real knowledge base — are out of reach by
construction, not by convention. The throwaway server stays on the host, where the
FastEmbed cache is warm.

## Prerequisites

- Docker (Docker Desktop on this machine) running
- `uv sync --group harness` (installs the `docker` SDK — agent-shell lives in the
  container image, not on the host)
- Opencode authenticated on the host (`opencode auth login`); the harness stages a
  *copy* of `~/.local/share/opencode/auth.json` into the container

## Running

```bash
uv run python -m test_harness                                  # full 9-skill walkthrough
uv run python -m test_harness --skills forgetful-recall        # subset (canonical order)
uv run python -m test_harness --timeout 600 --output /tmp/uat
uv run python -m test_harness --rebuild-image                  # force image rebuild
```

Flags > `TEST_HARNESS_*` env > defaults (`test_harness/config.py`). `--skills` and
`TEST_HARNESS_SKILLS` share one comma-separated spelling (`a,b`; spaces around commas are
ignored; an empty value is an error, never "all skills"). `--timeout` /
`TEST_HARNESS_SKILL_TIMEOUT` applies to every skill, including encode-repo, whose longer
1800s default only applies when no timeout was given; it must be at least 1 second.

The walkthrough order
is fixed by data dependencies — write-skills populate the store the read-skills then
query: `cli-setup → remember → entities → procedures → files → recall → explore →
context-gather → encode-repo`. `forgetful-mcp-setup` is seeded but not walked: the MCP
surface pass is a reserved axis (`--surface` accepts only `cli` in v1). `--agent` accepts
only `opencode` in v1 — other agents need provisioning ported in `container.py`.

Exit codes: `0` every session completed (issues found are findings, not failures),
`1` some session timed out or errored (partial UAT), `2` harness infrastructure failure.

## The image

`forgetful-test-harness:latest`, built from `test_harness/docker/Dockerfile`: opencode,
uv-managed Python 3.12, agent-shell, and Forgetful's **locked dependency tree** baked as
cached layers. The working tree itself is built as a wheel on the host and installed
`--no-deps` at container start, so every run walks the current checkout without an
image rebuild. `ensure_image()` hashes `uv export --frozen` into an image label and
rebuilds automatically when the lock drifts (stale images have burned runs before);
`--rebuild-image` forces it, e.g. after an opencode release.

## What a run does

1. Build/verify the sandbox image, boot `forgetful serve` as a host subprocess:
   file-backed SQLite in the run dir, all feature flags on, no auth, FastEmbed
   embeddings (warm default cache), `/health` polled to 200.
2. Seed every `skills/*/SKILL.md` into the instance via `import_skill` (the store under
   review holds the docs under review).
3. Start one container for the run — fenced env baked in (`FORGETFUL_SERVER` →
   `host.docker.internal:<port>`, decoy `SQLITE_PATH` for any `--local` detour), staged
   opencode credentials, `runs/<ts>/skills/` mounted rw, the wheel + runner mounted ro —
   then an in-container agent health check (broken agent = infra error, not findings).
4. Per skill, in order: fresh agent session (one `docker exec` each) in a prepared
   workspace (`SKILL.md` copy; `fixture-repo/` for encode-repo), wrapped in an
   OS-level `timeout --kill-after` — host-side cancellation cannot kill a process
   inside a container.
5. Teardown container and server, then a summary table and `run.json`.

## Artifacts

```
test_harness/runs/<timestamp>-<agent>/
├── run.json               # per-skill summary: status, verdict, issues, breaches, cost
├── server.log             # throwaway server output (host-side, not visible in-container)
├── forgetful.db           # the state the walkthrough produced (inspectable)
├── harness/               # the ro /harness mount: working-tree wheel + runner.py
└── skills/<skill>/        # the rw /skills mount, one dir per walked skill
    ├── prompt.txt         # exactly what the agent was asked
    ├── events.jsonl       # normalized StreamEvents, flushed as they arrived
    ├── debug.log          # agent-shell raw DEBUG stream (full command args)
    ├── session.log        # runner stdout/stderr from the docker exec
    ├── meta.json          # status, timings, cost, tokens, report status, breaches
    └── workspace/         # the agent's cwd: SKILL.md, report.json, scratch files
```

## Supervising analysis (the acceptance step)

The run is evidence collection; acceptance is a review. For each skill:

1. Read `workspace/report.json` (missing/malformed report is itself a finding — the
   contract wasn't followable).
2. Cross-check every claim against `events.jsonl` and `debug.log`: did the commands the
   report cites actually run, did the outputs match the quoted evidence? The transcript
   owns the truth.
3. Classify surviving issues: doc defect / product defect / model noise.
4. Check `meta.json` breach flags — any flagged tool name means the agent reached a
   configured forgetful MCP server instead of the fenced CLI route. Grep `debug.log`
   for `--local` while you're there (the decoy makes it harmless, but it signals the
   doc failed to keep the agent on the connected-server route).

Then deliver the acceptance verdict with the classified issue list.

## Isolation notes

Three independent fences, outermost first:

- **The container** is the hard barrier: the host filesystem simply isn't mounted
  (only `runs/<ts>/skills/`, the ro harness dir, and staged credential *copies*), so
  no tool the agent wields can touch the real repo, home directory, or knowledge base.
- **Env fencing** still rides inside it (mem 1701: fence both routes) — the container
  is born with `FORGETFUL_SERVER` pointing at the throwaway and `SQLITE_PATH` at a
  container-local decoy, and with no real credentials to leak at all.
- **Tool scoping + breach scan** remain defence-in-depth: agent-shell's tool lists do
  not enforce under auto-approve, so the post-run scan flags any forgetful MCP tool
  use in the transcript.
