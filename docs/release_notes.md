# Release notes

## Unreleased

### OpenAI embedding request concurrency and timeout (#91, #180)

OpenAI and compatible endpoints now use a native async client with a per-process HTTP
connection pool capped by `EMBEDDING_MAX_CONCURRENCY`. Its default of `1` reduces
concurrency compared with earlier versions. Set a higher positive value and restart
for overlapping requests. Memory and skill operations share the pool, and SDK retry
backoff releases connection capacity. This is not a logical-operation or rate limit.
Shutdown closes the client without draining in-flight OpenAI operations. The SDK timeout
is now configurable with `OPENAI_TIMEOUT_SECONDS`, which defaults to 120 seconds per attempt
while retaining a 5-second connection timeout. The SDK retries timeouts twice by default, so a
failing operation can take close to 6 minutes plus retry delays. See
[embedding request concurrency](configuration.md#embedding-request-concurrency).
No database migration or embedding rebuild is needed. Other embedding providers are unchanged.

### Token scope enforcement (#107)

Fix MCP permission widening when a valid token contains mixed or list-valued scopes, or uses the
`scp` claim. A read-only token such as `"scope": "openid read"` now keeps its read restriction.

**Upgrade action for some JWT/introspection users:** a nonempty scope claim containing no
recognised Forgetful permission now denies all MCP tools. For example, a token containing only
`api:read api:write` may still authenticate, but tool discovery is empty and tool calls are denied.

`FASTMCP_SERVER_AUTH_*_REQUIRED_SCOPES` sets IdP admission requirements. It does not grant tool
permissions or add claims to an issued token. Keep those admission labels and configure the issuer
or introspection response to include the intended Forgetful permissions too:

- Read-only access: `"scope": "api:read api:write read"`.
- Read/write access: `"scope": "api:read api:write read write"`.
- Narrower access can use category labels such as `write:memories`.

Obtain replacement tokens after changing issued claims. Token permissions are limited by the
server's `FORGETFUL_SCOPES` setting; `*` is appropriate only when the token should have all tools
allowed by that server. Environment scope settings use commas; token scope strings use spaces.
There is no new `forgetful_scopes` field.

Absent or empty scope claims keep the existing server-permission fallback, subject to the normal
authentication checks. Built-in GitHub/Google OAuth logins and local no-auth usage do not need the
JWT/introspection token change above. No database migration, embedding rebuild or dependency
upgrade is required by this fix. These changes apply to MCP tool permissions, not REST endpoint
scope enforcement.

See [configuration and upgrade steps][configuration] for the full rules and provider differences.
This fix does not address the separate empty-instance-permission-set fallback described there.

[configuration]: configuration.md#authentication-scopes-and-forgetful-tool-permissions
