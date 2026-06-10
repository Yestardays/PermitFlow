import pytest

from permitflow.models import ApplicationDraft, PermissionItem, UserProfile, Validity


def test_draft_reports_only_missing_required_values():
    item = PermissionItem(
        name="日志权限",
        category="监控",
        jira_project_key="ACCESS",
        approver_group="sre",
        required_fields=["service", "reason"],
        validity_options=[Validity.ONE_MONTH],
        aliases=["日志"],
    )
    draft = ApplicationDraft(
        permission=item,
        applicant=UserProfile(open_id="1", name="李四", email="l@example.com"),
        values={"service": "api"},
    )
    assert draft.missing_fields == ["reason", "validity"]


def test_sensitive_permission_cannot_be_permanent():
    item = PermissionItem(
        name="生产权限",
        category="云账号",
        jira_project_key="CLOUD",
        approver_group="cloud",
        required_fields=[],
        sensitive=True,
        validity_options=[Validity.PERMANENT],
        aliases=["prod"],
    )
    with pytest.raises(ValueError):
        ApplicationDraft(
            permission=item,
            applicant=UserProfile(open_id="1", name="李四", email="l@example.com"),
            validity=Validity.PERMANENT,
        )
