"""Compare common Git addresses without rewriting caller-owned identifiers."""

import re
from urllib.parse import urlsplit


def repository_identity(value: str) -> tuple[str, ...]:
    """Return a comparison key, or a literal key when interpretation is uncertain.

    Hosts are case-insensitive; repository paths and explicit ports are significant.
    Unsupported forms remain usable as opaque identifiers rather than being rejected.
    """
    value = value.strip()
    literal = ("literal", value)
    if any(c.isspace() or c in "\\?#%" for c in value):
        return literal

    address = value
    if "://" not in value:
        scp = re.fullmatch(r"([^/@:]+)@([^/:]+):(.+)", value)
        if scp:
            user, host, path = scp.groups()
            address = f"ssh://{user}@{host}/{path}"
        else:
            authority = value.split("/", 1)[0]
            if "." not in authority and authority.split(":", 1)[0] != "localhost":
                path = value.removesuffix("/").removesuffix(".git")
                if "/" in path and ":" not in path and all(
                    part not in ("", ".", "..") for part in path.split("/")
                ):
                    return ("path", path)
                return literal
            address = f"//{value}"

    try:
        parsed = urlsplit(address)
        if parsed.scheme not in ("", "http", "https", "ssh") or not parsed.hostname:
            return literal
        if parsed.password is not None or (parsed.username and parsed.scheme != "ssh"):
            return literal
        port = str(parsed.port) if parsed.port is not None else ""
    except ValueError:
        return literal

    path = parsed.path.removeprefix("/").removesuffix("/").removesuffix(".git")
    if any(part in ("", ".", "..") for part in path.split("/")):
        return literal
    return ("address", parsed.hostname.lower(), port, path)
