"""URL helpers shared by adapters and the CLI."""

import re

# Optional "scheme://" prefix, then everything up to the last "@" of the
# authority (userinfo may itself contain unescaped "@"). The authority ends at
# the first "/", "?" or "#", so an "@" later in the path or query is left alone.
_USERINFO_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*://)?[^/?#]*@")

REDACTED_USERINFO = "***:***"


def redact_url(url: str) -> str:
    """Hide credentials embedded in a URL so it is safe to log or print.

    Only the userinfo part (``user:password@``) is replaced, the scheme, host,
    port and path are kept so the result is still useful for diagnostics.
    Works on schemeless values such as ``user:token@host:11434`` and never
    raises, whatever the input looks like.

    Args:
        url: URL or host string that may carry ``user:password@`` credentials.

    Returns:
        The same URL with any userinfo replaced by ``***:***``.
    """
    return _USERINFO_PATTERN.sub(
        lambda match: f"{match.group(1) or ''}{REDACTED_USERINFO}@",
        url,
        count=1,
    )
