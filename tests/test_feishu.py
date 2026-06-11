import httpx
import pytest

from permitflow.feishu import FeishuClient


async def test_token_reports_feishu_business_error():
    async def handler(_request):
        return httpx.Response(200, json={"code": 10014, "msg": "app secret invalid"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = FeishuClient("app-id", "bad-secret", http)
        with pytest.raises(RuntimeError, match="code=10014"):
            await client._token()


async def test_http_error_reports_feishu_business_error():
    async def handler(_request):
        return httpx.Response(400, json={"code": 99991672, "msg": "missing scope"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = FeishuClient("app-id", "secret", http)
        client._tenant_token = "token"
        with pytest.raises(RuntimeError, match="code=99991672"):
            await client.get_user_profile("ou_1")


async def test_token_is_cached_after_success():
    calls = 0

    async def handler(_request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"code": 0, "tenant_access_token": "token"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = FeishuClient("app-id", "secret", http)
        assert await client._token() == "token"
        assert await client._token() == "token"

    assert calls == 1
