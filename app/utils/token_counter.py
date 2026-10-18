"""Token counting utilities for context budget management
"""
import logging
import threading

import tiktoken

logger = logging.getLogger(__name__)

# Rough characters-per-token ratio used when tiktoken is unavailable
APPROX_CHARS_PER_TOKEN = 4


def _approximate_tokens(text: str) -> int:
    """Estimate token count from text length (used when tiktoken cannot be used)"""
    return max(1, len(text) // APPROX_CHARS_PER_TOKEN)


class TokenCounter:
    """Utility class for counting tokens

    Falls back to an approximate character based estimate when the tiktoken encoding
    cannot be loaded (e.g. offline with an empty tiktoken cache), so token budgeting
    never prevents a query from completing.
    """

    def __init__(self, model: str="gpt-4"):
        self.encoding: tiktoken.Encoding | None = None
        try:
            try:
                self.encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Unknown model name, use the default encoding instead
                self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.warning(
                "Could not initialise tiktoken, using approximate token counting",
                exc_info=True,
                extra={"model": model},
            )

    def count_tokens(self, text: str) -> int:
        """Uses tiktoken to count the number of tokens in a string

        Text is always treated as plain text, so special token literals such as
        ``<|endoftext|>`` in user content are counted rather than rejected.

        Args:
            text: Text to count tokens

        Returns:
            token count
        """
        if not text:
            return 0

        if self.encoding is not None:
            try:
                return len(self.encoding.encode(text, disallowed_special=()))
            except Exception:
                logger.warning("tiktoken failed to encode text, using approximation", exc_info=True)

        return _approximate_tokens(text)


_token_counter: TokenCounter | None = None
_token_counter_lock = threading.Lock()


def get_token_counter() -> TokenCounter:
    """Return the shared TokenCounter, creating it on first use

    Loading a tiktoken encoding may download it, which blocks. Async callers should
    run this in a worker thread (``asyncio.to_thread``) until the counter exists.
    """
    global _token_counter
    if _token_counter is None:
        with _token_counter_lock:
            if _token_counter is None:
                _token_counter = TokenCounter()
    return _token_counter
