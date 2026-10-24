# Security Policy

## Supported versions

Security reports are accepted for the latest released version and the current `main` branch.
Security fixes are normally released for the latest stable version only.

Where practical, confirm that the issue still exists in the latest release before reporting it.

## Deployment notes

The default stdio transport is the safest option for local use. HTTP listens on all network
interfaces by default and runs without authentication unless `FASTMCP_SERVER_AUTH` is configured.
Before exposing HTTP beyond your machine, bind it to `127.0.0.1` with `--host`, or configure
authentication and a TLS-terminating reverse proxy. See the
[security configuration](docs/configuration.md#security-best-practices) for details.

## Reporting a vulnerability

Do not report security vulnerabilities through a public GitHub issue.

Use GitHub's
[private vulnerability reporting](https://github.com/ScottRBK/forgetful/security/advisories/new)
to submit the report.

Please include:

- the affected Forgetful version
- the deployment method and relevant configuration
- the vulnerability's impact
- steps or a proof of concept that reproduce it
- any known workaround

Do not include passwords, access tokens, personal data, or other secrets.

We aim to acknowledge reports within seven days. Please allow time for investigation and a
coordinated fix before publishing vulnerability details.

Forgetful does not currently offer a paid bug bounty.
