import json

import httpx
import pytest

from server.autofill.providers import OpenAIResponsesProvider, ResearchProviderError


def test_openai_provider_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    provider = OpenAIResponsesProvider()

    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(401, request=request, text=json.dumps({"error": "unauthorized"}))

    def fake_post(*args, **kwargs):
        raise httpx.HTTPStatusError("Unauthorized", request=request, response=response)

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ResearchProviderError) as excinfo:
        provider.research("system", "user", use_web=False, max_attempts=1)

    assert "Unauthorized OpenAI request" in str(excinfo.value)
    assert "Check OPENAI_API_KEY and model access" in str(excinfo.value)
