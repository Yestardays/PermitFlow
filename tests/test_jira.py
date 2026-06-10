import httpx

from permitflow.jira import JiraClient
from permitflow.models import ApplicationDraft, PermissionItem, UserProfile, Validity


def draft():
    item = PermissionItem(
        name="GitHub 写权限",
        category="GitHub",
        jira_project_key="ACCESS",
        approver_group="owners",
        required_fields=["reason"],
        validity_options=[Validity.THREE_MONTHS],
        aliases=["github"],
    )
    return ApplicationDraft(
        permission=item,
        applicant=UserProfile(open_id="1", name="张三", email="z@example.com"),
        values={"reason": "开发 <script>"},
        validity=Validity.THREE_MONTHS,
    )


async def test_jira_success_returns_ticket_link():
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(201, json={"key": "ACCESS-12"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        result = await JiraClient("https://jira.test", "a", "b", "https://desk", http).submit(
            draft()
        )
    assert result.ticket_url == "https://jira.test/browse/ACCESS-12"
    assert calls == 1


async def test_jira_retries_twice_then_returns_escaped_fallback():
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        result = await JiraClient("https://jira.test", "a", "b", "https://desk", http).submit(
            draft()
        )
    assert calls == 3
    assert result.success is False
    assert "&lt;script&gt;" in result.fallback_text
    assert result.fallback_url == "https://desk"
