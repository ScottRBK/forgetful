"""Build deterministic keyword expressions for hybrid memory search."""

from __future__ import annotations

import re
from dataclasses import dataclass

_RUN = re.compile(r"[^\W_]+", re.UNICODE)
_MEMORY_REF = re.compile(r"(?<![A-Za-z0-9&])#\d{2,5}\b")
_TICKET_KEY = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d{1,6}\b")
_CODE_MARK = re.compile(r"[._:/\\-]|[a-z][A-Z]")


@dataclass(frozen=True)
class KeywordQuery:
    """Tokenized query for FTS5 MATCH and Postgres to_tsquery."""

    terms: tuple[str, ...]
    phrases: tuple[tuple[str, ...], ...]

    @property
    def is_empty(self) -> bool:
        return len(self.terms) == 0


def build_keyword_query(query: str, max_terms: int = 32) -> KeywordQuery:
    """Extract alphanumeric runs from whitespace tokens; dedupe terms and phrases."""
    terms: list[str] = []
    seen_terms: set[str] = set()
    phrases: list[tuple[str, ...]] = []
    seen_phrases: set[tuple[str, ...]] = set()

    for tok in query.split():
        runs = [r.lower() for r in _RUN.findall(tok)]
        phrase_runs = [r for r in runs if len(r) >= 2]
        if len(phrase_runs) >= 2:
            phrase_tuple = tuple(phrase_runs)
            if phrase_tuple not in seen_phrases:
                seen_phrases.add(phrase_tuple)
                phrases.append(phrase_tuple)
        for run in runs:
            if len(run) < 2:
                continue
            if run in seen_terms:
                continue
            seen_terms.add(run)
            terms.append(run)
            if len(terms) >= max_terms:
                break
        if len(terms) >= max_terms:
            break

    return KeywordQuery(terms=tuple(terms), phrases=tuple(phrases))


def to_fts5_match(kq: KeywordQuery) -> str:
    """Double-quote each term and phrase; join with OR."""
    parts: list[str] = []
    for term in kq.terms:
        parts.append(f'"{term}"')
    for phrase in kq.phrases:
        parts.append(f'"{" ".join(phrase)}"')
    return " OR ".join(parts)


def to_pg_tsquery(kq: KeywordQuery) -> str:
    """Terms as-is; phrases with <->; joined with |."""
    parts: list[str] = []
    for term in kq.terms:
        parts.append(term)
    for phrase in kq.phrases:
        parts.append(" <-> ".join(phrase))
    return " | ".join(parts)


def is_identifier_query(query: str) -> bool:
    """True for a memory ref (#123), a ticket key (ABC-12) or a single code-like token."""
    text = query.strip()
    if _MEMORY_REF.search(text) or _TICKET_KEY.search(text):
        return True
    tokens = text.split()
    return len(tokens) == 1 and _CODE_MARK.search(tokens[0]) is not None
