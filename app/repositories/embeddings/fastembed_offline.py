"""Helpers for FastEmbed offline/cache-only startup."""
import os
from collections.abc import Callable

from app.config.settings import settings


def get_fastembed_kwargs() -> dict[str, bool]:
    """Return kwargs that constrain FastEmbed to local files when configured."""
    if not settings.FASTEMBED_LOCAL_FILES_ONLY:
        return {}

    # Hugging Face Hub reads this env var during model resolution. Set it before
    # importing/constructing FastEmbed models so startup never falls back to network.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    return {"local_files_only": True}


def load_fastembed_model[T](
    *,
    model_role: str,
    model_name: str,
    cache_dir: str,
    factory: Callable[[dict[str, bool]], T],
) -> T:
    """Load a FastEmbed model and add actionable offline guidance on failure."""
    kwargs = get_fastembed_kwargs()
    try:
        return factory(kwargs)
    except Exception as exc:
        if not settings.FASTEMBED_LOCAL_FILES_ONLY:
            raise

        raise RuntimeError(
            f"Could not load FastEmbed {model_role} model from local cache. "
            f"FASTEMBED_LOCAL_FILES_ONLY=true prevents downloading missing models. "
            f"model={model_name!r}, cache_dir={cache_dir!r}. "
            "Pre-populate FASTEMBED_CACHE_DIR with the required model files, "
            "disable FASTEMBED_LOCAL_FILES_ONLY, or choose a remote embedding/reranking provider.",
        ) from exc
