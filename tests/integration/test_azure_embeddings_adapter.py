"""Integration tests for AzureOpenAIAdapter with mocked Azure client.

Tests the adapter class in isolation - no real API key required.
"""
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import httpx
import pytest

from app.repositories.embeddings.embedding_adapter import AzureOpenAIAdapter


@pytest.fixture
def mock_settings():
    """Provide mock settings with valid Azure config."""
    with patch("app.repositories.embeddings.embedding_adapter.settings") as mock:
        mock.AZURE_ENDPOINT = "https://example.openai.azure.com/"
        mock.AZURE_DEPLOYMENT = "text-embedding-3-small"
        mock.AZURE_API_VERSION = "2024-02-01"
        mock.AZURE_API_KEY = "azure-test-key"
        mock.AZURE_TIMEOUT_SECONDS = 120.0
        mock.EMBEDDING_MODEL = "text-embedding-3-small"
        mock.EMBEDDING_DIMENSIONS = 256
        yield mock


@pytest.fixture
def mock_azure_client():
    """Provide a mock Azure OpenAI client."""
    with patch("app.repositories.embeddings.embedding_adapter.AsyncAzureOpenAI") as mock_cls, \
            patch("app.repositories.embeddings.embedding_adapter.DefaultAsyncHttpxClient"):
        mock_client = MagicMock()
        mock_client.embeddings.create = AsyncMock()
        mock_client.close = AsyncMock()
        mock_cls.return_value = mock_client
        yield mock_cls, mock_client


def test_init_passes_azure_settings_to_async_client(mock_settings, mock_azure_client):
    mock_cls, _ = mock_azure_client

    AzureOpenAIAdapter()

    mock_cls.assert_called_once_with(
        api_version="2024-02-01",
        azure_endpoint="https://example.openai.azure.com/",
        api_key="azure-test-key",
        http_client=ANY,
        timeout=httpx.Timeout(120.0, connect=5.0),
    )


def test_default_max_concurrency_is_one(mock_settings, mock_azure_client):
    with patch("app.repositories.embeddings.embedding_adapter.DefaultAsyncHttpxClient") as mock_http:
        AzureOpenAIAdapter()

    _, kwargs = mock_http.call_args
    assert kwargs["limits"].max_connections == 1
    assert kwargs["limits"].max_keepalive_connections == 1


@pytest.mark.asyncio
async def test_generate_embedding_awaits_create_with_deployment(mock_settings, mock_azure_client):
    _, mock_client = mock_azure_client

    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1, 0.2, 0.3]
    mock_response = MagicMock()
    mock_response.data = [mock_embedding]
    mock_client.embeddings.create.return_value = mock_response

    adapter = AzureOpenAIAdapter()
    result = await adapter.generate_embedding("hello")

    assert result == [0.1, 0.2, 0.3]
    mock_client.embeddings.create.assert_awaited_once_with(
        input=["hello"],
        model="text-embedding-3-small",
        dimensions=256,
    )


@pytest.mark.asyncio
async def test_generate_embedding_api_error_propagates(mock_settings, mock_azure_client):
    _, mock_client = mock_azure_client
    mock_client.embeddings.create.side_effect = Exception("API rate limit exceeded")

    adapter = AzureOpenAIAdapter()

    with pytest.raises(Exception, match="API rate limit exceeded"):
        await adapter.generate_embedding("test text")


@pytest.mark.asyncio
async def test_generate_embedding_none_response_raises(mock_settings, mock_azure_client):
    _, mock_client = mock_azure_client
    mock_client.embeddings.create.return_value = None

    adapter = AzureOpenAIAdapter()

    with pytest.raises(RuntimeError, match="Azure response did not contain embedding vector"):
        await adapter.generate_embedding("test text")


@pytest.mark.asyncio
async def test_aclose_closes_client(mock_settings, mock_azure_client):
    _, mock_client = mock_azure_client

    adapter = AzureOpenAIAdapter()
    await adapter.aclose()

    mock_client.close.assert_awaited_once()
