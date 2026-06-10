import os

import pytest

from permitflow.jira import JiraClient
from permitflow.models import ApplicationDraft, PermissionItem, UserProfile, Validity

pytestmark = pytest.mark.skipif(
    not os.getenv("JIRA_INTEGRATION_URL"),
    reason="JIRA_INTEGRATION_URL is required for Docker integration tests",
)


def integration_draft() -> ApplicationDraft:
    permission = PermissionItem(
        name="GitHub 仓库写权限",
        category="GitHub",
        jira_project_key="ACCESS",
        approver_group="github-owners",
        required_fields=["repository", "reason"],
        validity_options=[Validity.THREE_MONTHS],
        aliases=["github写权限"],
    )
    return ApplicationDraft(
        permission=permission,
        applicant=UserProfile(
            open_id="ou_integration",
            name="集成测试用户",
            department="研发",
            email="integration@example.com",
        ),
        values={"repository": "team/api", "reason": "集成测试"},
        validity=Validity.THREE_MONTHS,
    )


async def test_real_http_jira_submission_and_reminder():
    base_url = os.environ["JIRA_INTEGRATION_URL"]
    client = JiraClient(base_url, "test@example.com", "test-token", f"{base_url}/servicedesk")
    result = await client.submit(integration_draft())
    assert result.success is True
    assert result.ticket_key == "ACCESS-1001"
    assert result.ticket_url == f"{base_url}/browse/ACCESS-1001"
    assert await client.remind("ACCESS-1001", "请关注测试工单") is True
